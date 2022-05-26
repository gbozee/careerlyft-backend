# from paystack import signals as p_signals
# from ravepay import signals as r_signals
from django.dispatch import receiver
from decimal import Decimal
from .legacy_payment import TemplatInfo, UserPayment
from .new_payment import PlanPayment, Coupon
from .base import ReferralDiscount
from dispatch import receiver as d_receiver


# @receiver(r_signals.payment_verified)
def on_ravepay_payment_verified(sender, ref, amount, **kwargs):
    plan = kwargs.get("plan")
    if plan:
        record = PlanPayment.objects.filter(order=ref).first()
    else:
        record = UserPayment.objects.filter(order=ref).first()
    record.payment_method = UserPayment.RAVEPAY
    record.amount = amount
    record.made_payment = True
    record.save()
    # process to quickbooks
    # record.create_sales_receipt()
    record.add_to_mailing_list()
    record.miscellaneous_actions()


# @receiver(p_signals.payment_verified)
def on_payment_verified(sender, ref, amount, order, **kwargs):
    plan = kwargs.get("plan")
    paystack_data = kwargs.get("data", {})
    if plan:
        record = PlanPayment.objects.filter(order=order).first()
    else:
        record = UserPayment.objects.filter(order=order).first()
    record.on_payment_verification(amount / 100, paystack_data, **kwargs)
    # process to quickbooks
    # record.create_sales_receipt()
    # record.add_to_mailing_list()
    # record.miscellaneous_actions()
    return plan


# @receiver(p_signals.event_signal)
def on_event_received(sender, event, data, **kwargs):
    # this is where we listen for events.
    pass


# @d_receiver(p_signals.successful_payment_signal)
def on_successful_transfer(sender, **kwargs):
    from payment_service import services

    data = kwargs["data"]
    amount = data["amount"]
    plan_details = data.get("plan_object") or data.get("plan") or {}
    authorization = data["authorization"]
    paystack_details = {
        "customer": data["customer"],
        "plan_details": plan_details,
        "plan": plan_details.get('plan_code'),
        "auth_data": authorization,
        "authorization": authorization["authorization_code"],
    }
    record = PlanPayment.objects.filter(order=data["reference"]).first()
    if data["status"] == "success":
        email = data["customer"]["email"]
        if not record:
            plan_name, duration = plan_details["name"].split(" ")
            record = PlanPayment.objects.create(
                order=data["reference"],
                # currency=data['currency'],
                plan=plan_name,
                duration=duration.lower(),
                kind="agent",
                extra_data={"default_rate": amount, "email": email},
            )
        if not record.made_payment:
            record = record.on_payment_verification(
                amount, paystack_details, kind="agent"
            )
            services.update_payment_details(record.order, True, email=email)
        else:
            record.extra_data = {
                **record.extra_data,
                "paystack_details": paystack_details,
            }
            record = services.fetch_subscription_from_paystack(record)
            record.update_agent_plan(email=data["customer"]["email"])


# @receiver(r_signals.event_signal)
def on_ravepay_signals(sender, event, data, **kwargs):
    pass
