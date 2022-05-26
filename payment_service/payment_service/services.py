import json
import os

import django

django.setup()
from decimal import Decimal
# from paystack import signals as p_signals
# from ravepay import signals as r_signals
from asgiref.sync import sync_to_async
from paystack.utils import PaystackAPI
from django.shortcuts import reverse
from ravepay.utils import RavepayAPI
from .models import UserPayment, TemplatInfo, ReferralDiscount, PlanPayment, Coupon
import django
from django.conf import settings
from django import forms
from cv_utils import utils
from paystack.utils import get_js_script as p_get_js_scripts
from ravepay.utils import get_js_script as r_get_js_scripts


class PaymentForm(forms.Form):
    template = forms.CharField()
    level = forms.CharField()
    create = forms.BooleanField(required=False)
    plan = forms.CharField()
    duration = forms.CharField()
    coupon = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        data = args[0]
        self.user_kind = kwargs.pop("kind", "client")
        if data.get("template"):
            self.kind = "template"
        else:
            self.kind = "plan"
            self.pricing = kwargs.pop("pricing_details")
        super().__init__(*args, **kwargs)
        if self.kind == "template":
            del self.fields["plan"]
            del self.fields["duration"]
        else:
            del self.fields["template"]
            del self.fields["level"]

    def clean_plan(self):
        plans = self.pricing["plans"].keys()
        plan = self.cleaned_data.get("plan")
        if plan not in plans:
            raise forms.ValidationError("Plan passed not supported")
        return plan

    def get_payment_plans(self, plan):
        plans = self.pricing["plans"][plan]
        discount = self.pricing["discount"]
        annual_plans = {}
        if "semi_annual" in plans.keys():
            for key, value in plans["semi_annual"].items():
                annual_plans[key] = value * 2 * (1 - (discount / 100))
            plans["annual"] = annual_plans
            plans["annually"] = annual_plans
        if "monthly" in plans.keys():
            for key, value in plans["monthly"].items():
                annual_plans[key] = value * 12 * (1 - (discount / 100))
            plans["annual"] = annual_plans
            plans["annually"] = annual_plans
        return plans

    def get_plan_codes(self, plan):
        plan_codes = self.pricing["plan_code"][plan]
        duration = self.cleaned_data.get("duration")
        return plan_codes[duration]

    def clean_duration(self):
        payment_plans = self.get_payment_plans(self.cleaned_data.get("plan"))
        duration = self.cleaned_data.get("duration")
        durations = payment_plans.keys()
        if duration not in durations:
            raise forms.ValidationError("Duration passed not supported")
        return duration

    def clean_template(self):
        self.template = TemplatInfo.objects.filter(
            name__iexact=self.cleaned_data.get("template")
        ).first()
        if not self.template:
            if self.data.get("create"):
                self.template = TemplatInfo.create_new_template_from_existing(
                    self.cleaned_data["template"]
                )
                return self.cleaned_data["template"]
            raise forms.ValidationError("Template does not exist")
        return self.cleaned_data["template"]

    def clean_level(self):
        self.level_value = self.cleaned_data.get("level")
        if self.level_value not in ReferralDiscount.OPTIONS:
            raise forms.ValidationError("Level not sent")
        return self.level_value

    def purchase_template(self, user, user_details=None):
        result = self.template.create_user_payment(user)
        result.amount = self.determine_new_price(country=user_details.get("country"))
        result.extra_data = {**user_details, "level": self.level_value}
        result.made_payment = True
        result.save()
        return result

    def paystack_details(self):
        pass

    def determine_new_price(self, country):
        return self.template.determine_new_price(self.level_value, country)

    def determine_plan_amount(self, instance, country, currency=None):
        plans = self.get_payment_plans(instance.plan)
        considered_plans = plans[instance.duration]
        c_currency = currency or instance.get_currency_for_country(country)["currency"]
        return considered_plans[c_currency.lower()]

    def save_template_form(self, user, user_details=None, redirect_url=None):
        # check if any payment currently exists
        data = user_details or {}
        result = UserPayment.pending_payment(user, template=self.template)
        if not result:
            result = self.template.create_user_payment(user)
        if not result.made_payment:
            result.template = self.template
            result.amount = self.determine_new_price(data.get("country"))
            result.extra_data = {**data, "level": self.level_value}
            result.save()
            payment_detail = result.details
            base_url = redirect_url or settings.CURRENT_DOMAIN
            if data.get("country").lower() == "nigeria":
                link = (
                    f"{base_url}/v2{reverse('paystack:verify_payment',args=[payment_detail['order']])}"
                    + f"?amount={int(Decimal(payment_detail['amount'])*100)}"
                )
                payment_detail["user_details"].update(
                    key=settings.PAYSTACK_PUBLIC_KEY,
                    redirect_url=link,
                    kind="paystack",
                    js_script=p_get_js_scripts(),
                )
            else:
                link = (
                    f"{base_url}/v2{reverse('ravepay:verify_payment',args=[payment_detail['order']])}"
                    + f"?amount={float(Decimal(payment_detail['amount']))}"
                )
                payment_detail["user_details"].update(
                    key=settings.RAVEPAY_PUBLIC_KEY,
                    redirect_url=link,
                    kind="ravepay",
                    js_script=r_get_js_scripts(),
                )
        return result.details

    def save_plan_form(self, user, user_details=None, currency=None, redirect_url=None):
        # check if any payment currently exists
        data = user_details or {}
        if currency:
            data["currency"] = currency
        result = PlanPayment.pending_payment(user)
        if not result:
            result = PlanPayment.objects.create(user=user)
        if not result.made_payment:
            result.kind = self.user_kind
            result.plan = self.cleaned_data.get("plan")
            result.duration = self.cleaned_data.get("duration")
            coupon = self.cleaned_data.get("coupon")
            result.amount = self.determine_plan_amount(
                result, data.get("country"), currency=currency
            )
            result.coupon = Coupon.get_discount(coupon)
            extra_data = {
                **data,
                "default_rate": result.amount,
                "user_kind": self.user_kind,
            }
            country = data.get("country", "United States")
            country_currency = utils.get_currency(country)
            if self.user_kind == "agent":
                if not result.coupon:
                    extra_data["plan_code"] = self.get_plan_codes(result.plan)[
                        currency or country_currency
                    ]
            result.extra_data = extra_data
            result.save()
            payment_detail = result.details
            condition = country_currency in ["ngn", "usd"]
            if currency:
                condition = currency in ["ngn", "usd"]
            base_url = redirect_url or settings.CURRENT_DOMAIN

            if condition:
                path = reverse(
                    "paystack:verify_payment", args=[payment_detail["order"]]
                )
                amount = int(payment_detail["amount"] * 100)
                link = f"{base_url}/v2{path}" + f"?amount={amount}&plan={result.plan}"
                # import ipdb; ipdb.set_trace()
                if self.user_kind == "agent":
                    link += "&kind=agent"
                payment_detail["user_details"].update(
                    key=settings.PAYSTACK_PUBLIC_KEY,
                    redirect_url=link,
                    kind="paystack",
                    js_script=p_get_js_scripts(),
                )
            else:
                path = reverse("ravepay:verify_payment", args=[payment_detail["order"]])
                amount = float(Decimal(payment_detail["amount"]))
                link = f"{base_url}/v2{path}" + f"?amount={amount}&plan={result.plan}"
                payment_detail["user_details"].update(
                    key=settings.RAVEPAY_PUBLIC_KEY,
                    redirect_url=link,
                    kind="ravepay",
                    js_script=r_get_js_scripts(),
                )
        status = True
        if coupon:
            if payment_detail["discount"] == 0:
                status = False
        return result.details, status

    def save(self, user, user_details=None, currency=None, redirect_url=None):
        if self.kind == "template":
            return self.save_template_form(
                user, user_details=user_details, redirect_url=redirect_url
            )
        return self.save_plan_form(
            user,
            user_details=user_details,
            currency=currency,
            redirect_url=redirect_url,
        )


def paystack_verification(request, amount_only=True, **kwargs):
    amount = request.get("amount")
    txrf = request.get("trxref")
    paystack_instance = PaystackAPI()
    result = paystack_instance.verify_payment(
        txrf, amount=int(amount), amount_only=amount_only
    )
    if not amount_only:
        result = (
            result[0],
            result[1],
            paystack_instance.transaction_api.get_customer_and_auth_details(result[2]),
        )
    return result


def ravepay_verification(request, **kwargs):
    amount = request.get("amount")
    code = request.get("code")
    ravepay_instance = RavepayAPI()
    return ravepay_instance.verify_payment(code, float(amount))


@sync_to_async
def verify_payment(request, order, kind="paystack", **kwargs):
    options = {"paystack": paystack_verification, "ravepay": ravepay_verification}
    result = options[kind](request, **kwargs)
    return result


def process_paystack_payment(request, order, kind="paystack", data=None):
    amount = request.get("amount")
    plan = request.get("plan")
    if kind == "paystack":
        txrf = request.get("trxref")
        # on_payment_verified(PaystackAPI, txrf, amount, order)
        p_signals.payment_verified.send(
            sender=PaystackAPI,
            ref=txrf,
            amount=int(amount),
            order=order,
            plan=plan,
            kind=request.get("kind"),
            data=data,
        )
    else:
        r_signals.payment_verified.send(
            sender=RavepayAPI, ref=order, amount=float(amount), plan=plan
        )
    return plan


def create_payment_record(user_id, body, networks):
    instance = PaymentForm(body)
    redirect_url = body.pop("redirect_url", None)
    if instance.is_valid():
        value = instance.save(user_id, user_details=networks, redirect_url=redirect_url)
        return True, value
    return False, {"errors": instance.errors}


def create_single_template_payment(user_id, body, user_details):
    instance = PaymentForm(body)
    redirect_url = body.pop("redirect_url", None)
    if instance.is_valid():
        value = instance.save(
            user_id, user_details=user_details, redirect_url=redirect_url
        )
        return True, {"data": value}
    return False, {"errors": instance.errors}


def create_payment_plan(user_id, body, pricing_details, user_details):
    currency = body.pop("currency", None)
    kind = body.pop("kind", "client")
    redirect_url = body.pop("redirect_url", None)
    instance = PaymentForm(body, pricing_details=pricing_details, kind=kind)
    if instance.is_valid():
        value, coupon_used = instance.save(
            user_id,
            user_details=user_details,
            currency=currency,
            redirect_url=redirect_url,
        )
        result = {"data": value}
        if not coupon_used:
            result["coupon_used"] = False
        # import pdb; pdb.set_trace()
        return True, result
    return False, {"errors": instance.errors}


def fetch_subscription_from_paystack(record):
    paystack_info = record.extra_data.get("paystack_details")
    if paystack_info.get("plan") and paystack_info.get("customer"):
        paystack_instance = PaystackAPI()
        extra_data = record.extra_data
        plan_details = extra_data.get("paystack_details", {}).pop("plan_details", None)
        if not plan_details:
            _, _, plan_details = paystack_instance.subscription_api.get_plan(
                paystack_info["plan"]
            )
        result = paystack_instance.subscription_api.get_all_subscriptions(
            {"plan": plan_details["id"], "customer": paystack_info["customer"]["id"]}
        )
        result = result[2]
        extra_data["paystack_details"] = {
            **extra_data["paystack_details"],
            "plan_id": plan_details["id"],
            "subscription_code": result[0]["subscription_code"],
            "email_token": result[0]["email_token"],
        }
        record.extra_data = extra_data
        record.save()
        return record


def update_payment_details(order, plan, **kwargs):
    if plan:
        record = PlanPayment.objects.filter(order=order).first()
    else:
        record = UserPayment.objects.filter(order=order).first()
    if record.payment_method != UserPayment.RAVEPAY:
        print("Send notification to auth service")
        print("Create sales reciept")
        print("Add to mailing list")
        if record.extra_data.get("kind") != "agent":
            record.add_to_mailing_list()
        else:
            data = fetch_subscription_from_paystack(record)
            if data:
                record = data
        data = record.miscellaneous_actions(**kwargs)
        if data:
            record = data
        print(" Fetched subscription from paystack")
        record.create_sales_receipt()
    return record
