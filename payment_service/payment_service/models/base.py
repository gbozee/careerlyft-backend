import os
from .fields import TimeStampedModel
from wsgiref.util import FileWrapper
from django.db import models
from cv_utils import payment, utils, mail, client as client_api
from django.utils.crypto import get_random_string
from django.contrib.postgres.fields import JSONField
from typing import NamedTuple
from django.utils.functional import cached_property
from django.shortcuts import reverse
from io import BytesIO
from quickbooks import QuickbooksAPI
import requests
from django.conf import settings
from payment_service.utils import update_list_after_payment_made
from decimal import Decimal


def default_value():
    return {"facebook": 10, "linkedin": 10, "twitter": 10}


def generate_random():
    return get_random_string(12).upper()


def send_mail(kind, params, to):
    recipient = to
    if type(recipient) == str:
        recipient = [recipient]
    mail.send_mail(kind, params, recipient)


class Price(NamedTuple):
    base_rate: str
    currency: str
    country: str


class ReferralDiscount(models.Model, payment.PricingMixin):
    data = JSONField(default=default_value, blank=True, null=True)

    price_factor = JSONField(default=payment.PricingMixin.DEFAULT)

    @classmethod
    def get_single(cls):
        result = cls.objects.first()
        if not result:
            result = cls.objects.create()
        return result.data

    @classmethod
    def discount(self, network):
        if network:
            return self.get_single()[network]
        return 0

    @classmethod
    def max_discount(cls):
        return sum(cls.get_single().values())

    @classmethod
    def get_price_factor(cls):
        result = cls.objects.first()
        return result.price_factor.get("rates")

    @classmethod
    def currencies(cls):
        result = cls.objects.first()
        return result.price_factor.get("currencies")

    @classmethod
    def base_country(cls):
        result = cls.objects.first()
        return result.price_factor.get("base_countries")

    @classmethod
    def determine_rates(cls, country=None, currency=None) -> Price:
        if currency:
            curr = currency
        else:
            curr = utils.get_currency(country)
        base_rate = cls.currencies().get(curr.upper())
        base_country = cls.base_country().get(curr.upper())
        return Price(currency=curr, base_rate=base_rate, country=base_country)
        # return {"currency": currency, "base_rate": base_rate, "country": base_country}


class PaymentMixin(TimeStampedModel):
    PAYSTACK = 1
    RAVEPAY = 2
    CHOICES = ((PAYSTACK, "Paystack"), (RAVEPAY, "Ravepay"))
    user = models.IntegerField(null=True)
    amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    order = models.CharField(
        max_length=20, default=generate_random, primary_key=True)
    payment_method = models.IntegerField(choices=CHOICES, default=PAYSTACK)
    made_payment = models.BooleanField(default=False)
    extra_data = JSONField(null=True)

    class Meta:
        abstract = True

    @property
    def currency(self):
        # return "NGN"
        return os.getenv("CURRENCY", "USD")

    @classmethod
    def pending_payment(cls, user_id, template=None, made_payment=False):
        if not template:
            return cls.objects.filter(
                user=user_id, made_payment=made_payment).first()
        return cls.objects.filter(user=user_id, template=template).first()

    @classmethod
    def generate_payment_details(cls, user_id):
        instance = cls.pending_payment(user_id)
        if not instance:
            return None
        return instance.details

    @cached_property
    def quick_book_instance(self):
        result = os.getenv("CUSTOM_DEBUG",
                           "payment_service.settings.production")
        if result == "payment_service.settings.local":

            QUICKBOOKS_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"
        else:
            QUICKBOOKS_BASE_URL = "https://quickbooks.api.intuit.com"
        print(result)
        return QuickbooksAPI(url=QUICKBOOKS_BASE_URL)

    def quickbook_customer_call(self):
        user_details = self.extra_data
        details = {
            "email":
            user_details["email"],
            "full_name":
            f"{user_details.get('first_name')} {user_details.get('last_name')}",
            "phone_number":
            user_details["phone_number"],
            "location": {
                "country": user_details["country"],
                "address": user_details["contact_address"],
            },
        }
        return self.quick_book_instance.create_customer(**details)

    def create_quickbook_customer(self):
        user_details = self.extra_data
        # process to quickbooks
        quickbook_customer_details = user_details.get(
            "quickbooks_customer_details")
        if quickbook_customer_details == {}:
            # get the customer details from existing payment records
            quickbook_customer_details = None
            klass = self.__class__
            exists = (
                klass.objects.filter(
                    extra_data__quickbooks_customer_details__name=user_details[
                        "email"])
                .exclude(extra_data__quickbooks_customer_details__id=None)
                .first())
            if exists:
                quickbook_customer_details = exists.extra_data[
                    "quickbooks_customer_details"]
        if not quickbook_customer_details:
            quickbook_customer_details = self.quickbook_customer_call()
            params = {
                "user_id": self.user,
                "data": {
                    "quickbooks_customer_details": quickbook_customer_details
                },
            }
            if user_details.get('kind') != 'agent':
                res = requests.post(
                    settings.AUTH_ENDPOINT + "/save-custom-data",
                    json=params,
                )
            else:
                client_api.update_quickbooks_info_for_agent(
                    settings.AUTH_ENDPOINT + "/v2/graphql", params['data'],
                    user_details.get('email'))
        self.update_user_details(
            quickbooks_customer_details=quickbook_customer_details)
        return quickbook_customer_details

    @property
    def q_discount(self):
        return self.discount

    @property
    def description(self):
        return f"{self.plan} {self.duration} subscription payment"

    @property
    def discount(self):
        # user_details = self.extra_data or {}
        # old_price = user_details.get("default_rate")
        if self.coupon:
            return self.coupon.discount * self.amount / 100
        return 0

    @property
    def price(self):
        user_details = self.extra_data or {}
        old_price = user_details.get("default_rate")
        if self.discount:
            return old_price - self.discount
        return old_price

    def create_sales_receipt(self):
        params = {
            "currency": self.currency,
            "description": self.description,
            "price": float(self.price),
            "amount": float(self.price),
            "discount": float(self.q_discount),
        }
        receipt_id = self.quick_book_instance.create_sales_receipt(
            self.create_quickbook_customer(), params)
        self.update_user_details(quickbooks_receipt_id=receipt_id)

    def update_user_details(self, **kwargs):
        user_details = self.extra_data
        user_details.update(**kwargs)
        self.extra_data = user_details
        self.save()

    def download_receipt(self):
        if self.made_payment:
            receipt_id = self.extra_data.get("quickbooks_receipt_id")
            if receipt_id:
                response = self.quick_book_instance.get_sales_receipt(
                    receipt_id)
                if response.status_code == 200:
                    bty = BytesIO(response.content)
                    return FileWrapper(bty)
        return

    def miscellaneous_actions(self):
        pass

    def add_to_mailing_list(self):
        if self.extra_data.get("email_subscribed"):
            update_list_after_payment_made(self.extra_data.get("email"))

    @classmethod
    def paid_records(cls, user_id, request, kind=None):
        queryset = cls.objects.filter(user=user_id, made_payment=True).all()
        skind = {"UserPayment": "template", "PlanPayment": "plan"}
        if kind == 'agent':
            queryset = queryset.filter(kind="agent")
        result = [{
            "date":
            x.modified.strftime("%B %d, %Y"),
            "amount":
            float(x.amount),
            **x.get_currency(),
            "payment_method":
            x.get_payment_method_display(),
            "made_payment":
            x.made_payment,
            "receipt":
            request.build_absolute_uri(
                reverse(
                    "generic_download_receipt",
                    args=[skind[cls.__name__], x.order])).replace(
                        "http", "https"),
        } for x in queryset]
        return result

    def on_payment_verification(self, amount, paystack_data, **kwargs):
        self.made_payment = True
        self.amount = Decimal(amount)
        extra_data = self.extra_data
        extra_data['paystack_details'] = paystack_data
        if kwargs.get('kind'):
            extra_data['kind'] = kwargs['kind']
        self.extra_data = extra_data
        self.save()
        return self
        # process to quickbooks
        # self.create_sales_receipt()
        # self.add_to_mailing_list()
        # self.miscellaneous_actions()
