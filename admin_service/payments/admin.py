from django import forms
from django.contrib.admin.helpers import ActionForm
from admin_service.admin import admin, ServicesModelAdmin
from django.utils.safestring import mark_safe
from cv_profiles.shared import GeneralMixin
from cv_utils import client as client_api

# Register your models here.
from .models import (
    TemplateInfo,
    ReferralDiscount,
    UserPayment,
    PriceFactor,
    PlanPayment,
    Plan,
    AgentPlan,
    UserPlan,
    Coupon,
)
from django.conf import settings
from cv_utils import mail


@admin.register(TemplateInfo)
class TemplateInfoAdmin(ServicesModelAdmin, GeneralMixin):
    list_display = ["name", "price"]


@admin.register(ReferralDiscount)
class ReferralDiscountAdmin(ServicesModelAdmin):
    list_display = ["facebook", "linkedin", "twitter"]

    def facebook(self, obj):
        return obj.data["facebook"]

    def linkedin(self, obj):
        return obj.data["linkedin"]

    def twitter(self, obj):
        return obj.data["twitter"]


@admin.register(PriceFactor)
class PriceFactorAdmin(ServicesModelAdmin):
    list_display = ["rates", "base_rate"]


class PlanForm(ActionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].choices = [("", "Select Plan")] + list(
            Plan.s_objects.values_list("name", "name")
        )
        pro = Plan.s_objects.filter(name="Pro").first()
        if pro:
            self.fields["duration"].choices = [("", "Select duration")] + [
                (x, x)
                for x in [
                    "weekly",
                    "fortnight",
                    "monthly",
                    "quarterly",
                    "semi_annual",
                    "annual",
                ]
            ]

    plan = forms.ChoiceField(choices=(), required=False)
    duration = forms.ChoiceField(choices=(), required=False)


@admin.register(UserPayment)
class UserPaymentAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = [
        "order",
        "created",
        "email",
        "amount",
        "payment_method",
        "made_payment",
        "download_pdf",
    ]
    search_fields = ["user_instance__email", "order"]
    list_filter = ["payment_method"]
    actions = GeneralMixin.actions + ["update_mailing_list", "create_plan_for_user"]
    action_form = PlanForm

    # def get_search_results(self, request, queryset, search_term):
    #     queryset, use_distinct = super().get_search_results(request, queryset, search_term)
    #     queryset |= self.model.objects.filter(user_instance__email=search_term)
    #     return queryset, use_distinct

    def email(self, obj):
        if obj.user_instance:
            return obj.user_instance.email

    def download_pdf(self, obj):
        if obj.made_payment:
            return mark_safe(
                f'<a href="{settings.PAYMENT_SERVICE}/download-receipt/{obj.order}">Download receipt</a>'
            )
        return ""

    def update_mailing_list(self, request, queryset):
        mail.paid_template_to_list(queryset.select_related("user_instance").all())

    def create_plan_for_user(self, request, queryset):
        plan = request.POST.get("plan")
        duration = request.POST.get("duration")
        if plan or duration:
            for i in queryset.all():
                if i.made_payment:
                    i.create_payment_plan(plan, duration)
        self.message_user(request, "User Plans successfully updated")


@admin.register(PlanPayment)
class PlanPaymentAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = [
        "order",
        "plan",
        "created",
        "email",
        "currency",
        "amount",
        "payment_method",
        "made_payment",
        "download_pdf",
        "coupon_code",
    ]
    search_fields = ["user_instance__email", "order"]
    list_filter = ["payment_method"]
    actions = GeneralMixin.actions + ["update_mailing_list", "update_payment_as_paid"]

    def email(self, obj):
        if obj.user_instance:
            return obj.user_instance.email

    def currency(self, obj):
        if obj.extra_data:
            return obj.extra_data.get("currency")

    def coupon_code(self, obj):
        if obj.coupon:
            return obj.coupon.code

    def download_pdf(self, obj):
        if obj.made_payment:
            return mark_safe(
                f'<a href="{settings.PAYMENT_SERVICE}/download-receipt/plan/{obj.order}">Download receipt</a>'
            )
        return ""

    def update_mailing_list(self, request, queryset):
        mail.paid_template_to_list(
            queryset.select_related("user_instance").all(), agent=True
        )

    def update_payment_as_paid(self, request, queryset):
        for i in queryset.all():
            client_api.mark_payment_as_paid(
                settings.PAYMENT_SERVICE, i.order, plan=i.plan, amount=i.amount
            )


def is_valid(*arg, **kwargs):
    import pdb

    pdb.set_trace()
    pass


@admin.register(UserPlan)
class UserPlanAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = ["user", "plan"]

    def get_form(self, request, obj=None, **kwargs):
        parent = super().get_form(request, obj, **kwargs)
        # import pdb; pdb.set_trace()
        return parent


@admin.register(AgentPlan)
class AgentPlanAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = [
        "user",
        "plan",
        "currency",
        "duration",
        "expiry_date",
        "last_renewed",
    ]

    def get_form(self, request, obj=None, **kwargs):
        parent = super().get_form(request, obj, **kwargs)
        # import pdb; pdb.set_trace()
        return parent


@admin.register(Plan)
class PlanAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = [
        "name",
        "kind",
        "monthly",
        "quarterly",
        "semi_annual",
        "annual",
        "allowed_resume",
    ]
    actions = ["sync_plans_with_paystack"]
    list_filter = ["kind"]

    def sync_plans_with_paystack(self, request, queryset):
        Plan.create_plans_on_paystack(queryset.all())

    def get_amount(self, obj, key):
        if obj.data:
            amount = obj.data.get("amount")
            if amount:
                return amount.get(key)

    def quarterly(self, obj):
        return self.get_amount(obj, "quarterly")

    def monthly(self, obj):
        return self.get_amount(obj, "monthly")

    def semi_annual(self, obj):
        return self.get_amount(obj, "semi_annual")

    def annual(self, obj):
        semi_annual = self.get_amount(obj, "semi_annual")
        monthly = self.get_amount(obj, "monthly")
        if monthly:
            result = {}
            discount = obj.data.get("discount")
            for key, value in monthly.items():
                result[key] = round(value * 12 * (1 - (discount / 100)), 1)
            return result
        if semi_annual:
            result = {}
            discount = obj.data.get("discount")
            for key, value in semi_annual.items():
                result[key] = round(value * 2 * (1 - (discount / 100)), 1)
            return result

    def allowed_resume(self, obj):
        if obj.resume_allowed:
            return obj.resume_allowed
        return "unlimited"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset


@admin.register(Coupon)
class CouponAdmin(GeneralMixin, ServicesModelAdmin):
    list_display = ["code", "expiry_date", "limit", "discount"]
