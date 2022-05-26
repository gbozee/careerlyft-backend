import json
from decimal import Decimal

from django import forms
from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, reverse
from django.urls import include, path, re_path
from django.views.generic import RedirectView

# from paystack import signals as p_signals
from paystack.utils import PaystackAPI
from paystack.utils import get_js_script as p_get_js_scripts
from ravepay.utils import get_js_script as r_get_js_scripts
# from ravepay import signals as r_signals
from ravepay.utils import RavepayAPI
from asgiref.sync import async_to_sync
from . import utils, services
from .models import ReferralDiscount, TemplatInfo, UserPayment, PlanPayment


def get_user(request):
    return request.user_id


def create_free_template(request):
    data = json.loads(request.body)
    instance = services.PaymentForm({
        "template": "Blue Salmon",
        "level": "Free"
    })
    if instance.is_valid():
        value = instance.purchase_template(data["user_id"],
                                           data["personal-info"])
        return JsonResponse({"order": value.order}, status=200)
    return JsonResponse({"errors": instance.errors}, status=400)


@utils.login_required()
def get_payment_details(request):
    user_id = get_user(request)
    network = None
    if hasattr(request, "cleaned_body"):
        network = request.cleaned_body["network"]
    credentials = request.shared_networks
    UserPayment.add_discount(user_id, network, credentials)
    payment_detail = UserPayment.generate_payment_details(user_id)
    if not payment_detail:
        raise Http404("No payment record found")
    if hasattr(request, "cleaned_body") or "user_details" in request.GET:
        if payment_detail["user_details"].get("country").lower() == "nigeria":
            link = (
                f"{settings.CURRENT_DOMAIN}/v2{reverse('paystack:verify_payment',args=[payment_detail['order']])}"
                + f"?amount={int(Decimal(payment_detail['amount'])*100)}")
            payment_detail["user_details"].update(
                key=settings.PAYSTACK_PUBLIC_KEY,
                kind="paystack",
                js_script=p_get_js_scripts(),
                # redirect_url=request.build_absolute_uri(
                #     reverse("paystack:verify_payment", args=[payment_detail["order"]])
                # )
                # + f"?amount={int(Decimal(payment_detail['amount'])*100)}",
                redirect_url=link,
            )
        else:
            link = (
                f"{settings.CURRENT_DOMAIN}/v2{reverse('ravepay:verify_payment',args=[payment_detail['order']])}"
                + f"?amount={float(Decimal(payment_detail['amount']))}")
            payment_detail["user_details"].update(
                key=settings.RAVEPAY_PUBLIC_KEY,
                redirect_url=link,
                kind="ravepay",
                js_script=r_get_js_scripts(),
            )
    else:
        del payment_detail["user_details"]
    return JsonResponse(payment_detail)


@utils.login_required()
def update_sample_record(request):
    user_id = request.session.pop("user_id", None)
    TemplatInfo.create_sample_template(user_id)
    return JsonResponse({"created": True})


@utils.login_required()
def share_link(request):
    user_id = request.session.pop("user_id", None)


class RRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return settings.SUCCESS_URL


def demo_redirect(request):
    return redirect(reverse("redirect_func"))


redirect_function = RRedirectView.as_view()
# def redirect_function(request):
#     return redirect(settings.SUCCESS_URL)


@utils.when_logged_in()
def get_supported_templates(request):
    templates, bought = TemplatInfo.get_templates(
        user=request.user, country=request.country)
    # templates = TemplatInfo.get_templates(user_id=request.session.get("user_id"))
    rates = ReferralDiscount.get_price_factor()
    return JsonResponse({
        "data": templates,
        "rates": rates,
        "bought": list(bought)
    })


def sample_request(request):
    return JsonResponse({"message": "hello world from payment service"})


def download_receipt_func(request, kind, order):
    options = {"plan": PlanPayment, "template": UserPayment}
    modelInstance = options.get(kind) or UserPayment
    instance = modelInstance.objects.get(order=order)
    wrapper = instance.download_receipt()
    if wrapper:
        response = HttpResponse(wrapper, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={order}.pdf"
        return response
    return HttpResponse("Error downloading receipt", status=400)


def download_receipt(request, order):
    instance = UserPayment.objects.get(order=order)
    wrapper = instance.download_receipt()
    if wrapper:
        response = HttpResponse(wrapper, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={order}.pdf"
        return response
    return HttpResponse("Error downloading receipt", status=400)


@utils.login_required()
def all_payment_details(request):
    if request.method == 'POST':
        plan_details = PlanPayment.paid_records(
            request.user_id, request, kind=request.cleaned_body.get('kind'))
        template_details = []
    else:
        plan_details = PlanPayment.paid_records(request.user_id, request)
        template_details = UserPayment.paid_records(request.user_id, request)
    return JsonResponse({"payment_details": plan_details + template_details})


def verify_payment(request, order):
    return JsonResponse({"success": True})


def verify_ravepay_payment(request, order):
    return JsonResponse({"success": True})


urlpatterns = [
    path("", sample_request),
    re_path(
        "^paystack/verify-payment/(?P<order>[\w.@+-]+)/$",
        verify_payment,
        name="verify_payment",
    ),
    re_path(
        "^ravepay/verify-payment/(?P<order>[\w.@+-]+)/$",
        verify_ravepay_payment,
        name="verify_ravepay_payment",
    ),
    # re_path("^paystack/",
    #         include(("paystack.urls", "paystack"), namespace="paystack")),
    # re_path("^ravepay/",
    #         include(("ravepay.urls", "ravepay"), namespace="ravepay")),
    path(
        "quickbooks/",
        include(("quickbooks.urls", "quickbooks"), namespace="quickbooks"),
    ),
    path(
        "create-free-template",
        create_free_template,
        name="create-free-template"),
    path("payment-info", get_payment_details, name="get_new_payment_info"),
    path(
        "share-link", get_payment_details,
        name="reward-for-share-social-link"),
    path(
        "create-sample-record",
        update_sample_record,
        name="create_sample_record"),
    path("redirecting", redirect_function, name="redirect_func"),
    # path("create-payment", create_payment, name="create_payment"),
    path("templates", get_supported_templates, name="get_templates"),
    path(
        "download-receipt/<order>", download_receipt, name="download_receipt"),
    path(
        "download-receipt/<kind>/<order>",
        download_receipt_func,
        name="generic_download_receipt",
    ),
    path("payment-details", all_payment_details, name="all_payment_details"),
]
