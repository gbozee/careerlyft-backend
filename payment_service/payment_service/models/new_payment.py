import json
from django.db import models
from cv_utils import payment, client as client_api
from .base import PaymentMixin, ReferralDiscount, send_mail
from django.utils import timezone
from typing import Dict
import requests
from django.conf import settings


class Coupon(models.Model):
    code = models.CharField(max_length=50)
    expiry_date = models.DateTimeField(null=True, blank=True)
    limit = models.IntegerField(null=True, blank=True)
    discount = models.IntegerField(default=5)

    def limit_reached(self):
        if self.limit:
            return self.payments.filter(made_payment=True).count() >= self.limit
        return True

    def expired(self):
        current = timezone.now()
        if self.expiry_date:
            return current >= self.expiry_date
        return True

    @classmethod
    def get_discount(cls, coupon):
        instance = cls.objects.filter(code__iexact=coupon).first()
        # import pdb; pdb.set_trace()
        if instance:
            if not instance.limit_reached() and not instance.expired():
                return instance
        return None


class PlanPayment(PaymentMixin):
    plan = models.CharField(max_length=100, null=True, blank=True)
    duration = models.CharField(
        max_length=100, choices=payment.PricingMixin.DURATIONS, null=True, blank=True
    )
    kind = models.CharField(
        max_length=50,
        default="client",
        choices=[("client", "client"), ("agent", "agent")],
    )
    coupon = models.ForeignKey(
        Coupon,
        null=True,
        blank=True,
        related_name="payments",
        on_delete=models.SET_NULL,
    )

    def get_currency_for_country(self, country, currency=None) -> Dict[str, str]:
        selected_country = country or "United States"
        return self.get_price(country=selected_country, currency=currency)

    def get_price(self, country="Nigeria", currency=None) -> Dict[str, str]:
        result = ReferralDiscount.determine_rates(country=country, currency=currency)
        return {"currency": result.currency, "base_country": result.country}

    def get_currency(self) -> Dict[str, str]:
        user_details = self.extra_data or {}
        country = user_details.get("country")
        currency = user_details.get("currency")
        return self.get_currency_for_country(country, currency=currency)

    @property
    def details(self):
        user_details = self.extra_data or {}
        return {
            "amount": self.price,
            "order": self.order,
            **self.get_currency(),
            "description": f"{self.plan} {self.duration} subscription payment",
            "discount": round(self.discount, 2),
            "user_details": user_details,
            "paid": self.made_payment,
        }

    @property
    def q_discount(self):
        return self.discount

    def update_agent_plan(self, **kwargs):
        extra_data = self.extra_data
        variables = {
            "plan": self.plan,
            "currency": self.details["currency"],
            "duration": self.duration,
            "date": self.modified.strftime("%Y-%m-%d"),
            "paystack_details": json.dumps(extra_data.get("paystack_details")),
        }
        return client_api.update_agent_plan_details(
            variables,
            settings.AUTH_ENDPOINT + "/v2/graphql",
            token=extra_data.get("token"),
            **kwargs,
        )

    def miscellaneous_actions(self, **kwargs):
        extra_data = self.extra_data
        if extra_data.get("kind") == "agent":
            result = self.update_agent_plan(**kwargs)
            self.extra_data = {
                **extra_data,
                **result,
                "phone_number": result["phone"],
                "contact_address": "",
            }
            self.save()
            return self
        else:
            requests.post(
                settings.AUTH_ENDPOINT + "/upgrade-plan",
                json={
                    "plan": self.plan,
                    "currency": self.details["currency"],
                    "duration": self.duration,
                    "date": self.modified.strftime("%Y-%m-%d"),
                },
                headers={"Authorization": f"Token {extra_data['token']}"},
            )
        if PlanPayment.objects.filter(user=self.user).count() == 1:
            send_mail(
                "first_plan_payment",
                {"first_name": extra_data["first_name"], "plan": self.plan},
                extra_data["email"],
            )
        # if response.status_
