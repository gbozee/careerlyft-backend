from decimal import Decimal
from typing import Dict
from django.db import models

# from paystack.signals import event_signal, payment_verified

from .base import PaymentMixin, ReferralDiscount, send_mail


class TemplatInfo(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    thumbnail = models.TextField()
    data = models.TextField(null=True)

    def __repr__(self):
        return f"<TemplateInfo {self.name}"

    @classmethod
    def create_sample_template(cls, user_id):
        instance = cls.objects.get(name="Template 1")
        UserPayment.objects.create(
            user=user_id,
            order="1234567890AB",
            amount=instance.price,
            template=instance)

    def get_price(self, country="Nigeria") -> Dict[str, str]:
        result = ReferralDiscount.determine_rates(country)
        return {
            "price": result.base_rate,
            "currency": result.currency,
            "base_country": result.country,
        }

    @classmethod
    def create_new_template_from_existing(cls, template_name):
        template = cls.objects.values("price", "thumbnail", "data").first()
        new_template = cls(name=template_name)
        for key, value in template.items():
            setattr(new_template, key, value)
        new_template.save()
        return new_template

    def determine_new_price(self, level, country) -> Decimal:
        selected_country = country or "United States"
        price = self.get_price(selected_country)["price"]
        rate = ReferralDiscount.get_price_factor().get(level)
        if rate is not None:
            return Decimal(price) * Decimal(rate)
        return Decimal(price)

    @property
    def as_json(self):
        return {
            "name": self.name,
            "image": self.image,
            "id": self.id,
            # "data": self.data,
        }

    @classmethod
    def get_templates(cls, user=None, country=None):
        working_user = user or {}
        user_id = working_user.get("user_id")
        selected_country = country or "United States"
        bought_templates = []
        if user_id:
            # selected_country = working_user.get("shared_networks").get("country")
            bought_templates = UserPayment.objects.filter(
                made_payment=True, user=user_id)
        raw_results = cls.objects.annotate(image=models.F("thumbnail"))
        result = [{
            **x.as_json,
            **x.get_price(selected_country)
        } for x in raw_results]
        if user_id:
            return (
                [{
                    **x,
                    "paid":
                    x["id"] in bought_templates.values_list(
                        "template_id", flat=True),
                } for x in result],
                bought_templates.values_list("template__name", flat=True),
            )
        return result, bought_templates

    def create_user_payment(self, user_id):
        instance = UserPayment(
            user=user_id, amount=self.price, template=self, extra_data={})
        instance.save()
        return instance


class UserPayment(PaymentMixin):
    PAYSTACK = 1
    RAVEPAY = 2
    CHOICES = ((PAYSTACK, "Paystack"), (RAVEPAY, "Ravepay"))
    template = models.ForeignKey(
        TemplatInfo, null=True, on_delete=models.SET_NULL)

    @property
    def description(self):
        return f"Purchase of CV Template {self.template.name}"

    @property
    def discount(self):
        networks = self.extra_data.get("networks", [])
        total_discount = sum(ReferralDiscount.discount(x) for x in networks)
        return total_discount

    @property
    def q_discount(self):
        return 0

    @property
    def price(self):
        user_details = self.extra_data or {}
        level = user_details.get("level")
        country = user_details.get("country")
        old_price = self.template.determine_new_price(level, country)
        max_discount = ReferralDiscount.max_discount()
        if self.discount <= max_discount:
            return old_price - (old_price * self.discount / 100)
        return old_price

    def get_currency(self):
        user_details = self.extra_data or {}
        country = user_details.get("country")
        result = self.template.get_price(country)
        return {
            "currency": result["currency"],
            "base_country": result["base_country"]
        }

    @property
    def details(self):
        user_details = self.extra_data or {}
        return {
            "amount": self.price,
            "order": self.order,
            **self.get_currency(),
            "description": self.template.name,
            "discount": self.discount,
            "thumbnail": self.template.thumbnail,
            "user_details": user_details,
            "paid": self.made_payment,
        }

    @classmethod
    def add_discount(cls, user_id, network, credentials):

        credentials.pop("networks", [])
        instance = cls.objects.filter(user=user_id, made_payment=False).first()
        existing_data = instance.extra_data or {}
        instance.extra_data = {**existing_data, **credentials}
        instance.save()
        return instance

    @property
    def made_first_payment(self):
        return (UserPayment.objects.filter(user=self.user,
                                           made_payment=True).count() == 1)

    def create_sales_receipt(self):
        super().create_sales_receipt()
        if self.made_first_payment:
            send_mail(
                "first_resume_download",
                {"first_name": self.extra_data["first_name"]},
                self.extra_data["email"],
            )
