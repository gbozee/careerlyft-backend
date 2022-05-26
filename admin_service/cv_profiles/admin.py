from django.conf import settings
from django.utils.safestring import mark_safe
from django.db import models

from admin_service.admin import ServicesModelAdmin, admin
from cv_utils import utils, mail
from django.db import models
from django.utils.translation import gettext as _

# Register your models here.
from .models import Customer, RegistrationServiceCvprofile, Agent, AgentCustomer
from .shared import GeneralMixin
from payments.models import Plan, UserPlan
from payments.admin import PlanForm


class CustomerCompletedFilter(admin.SimpleListFilter):
    title = _("completed_cv")
    parameter_name = "completed"

    def lookups(self, request, model_admin):
        return (
            ("Completed", "Completed"),
            ("Multiple", "Multiple"),
            ("Made Payment", "Made Payment"),
        )

    def queryset(self, request, queryset):
        if self.value():
            if self.value() == "Completed":
                return queryset.filter(resume_completed__gt=0)
            if self.value() == "Multiple":
                return queryset.filter(resume_completed__gt=1)
            if self.value() == "Made Payment":
                return queryset.filter(total_paid__gt=0)
        return queryset


class PlanFilter(admin.SimpleListFilter):
    title = _("plan_filter")
    parameter_name = "plan"

    def lookups(self, request, model_admin):
        plans = Plan.s_objects.values_list("name", "name")
        return plans

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(plan__plan__name=self.value())
        return queryset


class UserAdmin(ServicesModelAdmin, GeneralMixin):
    list_display = [
        "email",
        "first_name",
        "last_name",
        "date_joined",
        "country",
        "email_subscribed",
        "plan_name",
        "subscription",
        "expiry_date",
        "hijack_account",
    ]
    search_fields = ["email"]
    list_filter = ["country"]

    def hijack_account(self, obj):
        return mark_safe(
            f'<a target="_blank" href="{settings.AUTH_SERVICE}/generate-new-token/{obj.pk}?is_admin=sama101&kind={self.kind}">Hijack Account</a>'
        )

    def expiry_date(self, obj):
        plan = obj.get_plan()
        return plan.expiry_date

    def subscription(self, obj):
        plan = obj.get_plan()
        return plan.duration


@admin.register(Agent)
class AgentAdmin(UserAdmin):
    kind = "agent"
    list_display = UserAdmin.list_display + ["company_name"]


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    kind = "user"
    list_display = UserAdmin.list_display + [
        "resume_count",
        "resume_completed",
        "total_paid",
    ]
    list_filter = [
        "verified_email",
        PlanFilter,
        CustomerCompletedFilter,
    ] + UserAdmin.list_filter
    actions = GeneralMixin.actions + [
        "add_to_mailing_list",
        "create_free_trial_for_users",
    ]
    action_form = PlanForm

    def resume_count(self, obj):
        return obj.resume_created

    def resume_completed(self, obj):
        return obj.resume_completed

    def total_paid(self, obj):
        return obj.total_paid

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            resume_created=models.Count("registrationservicecvprofile"),
            resume_completed=models.Count(
                "registrationservicecvprofile",
                filter=models.Q(registrationservicecvprofile__completed=True),
            ),
            total_paid=models.Sum(
                "userpayment__amount", filter=models.Q(userpayment__made_payment=True)
            ),
        )
        return queryset

    def add_to_mailing_list(self, request, queryset):
        queryset.update(email_subscribed=True)
        self.message_user(request, "Added to Mailing list")
        mail.add_to_email_list(
            queryset.annotate(
                completed_count=models.Count("registrationservicecvprofile")
            ).all(),
            True,
        )

    def create_free_trial_for_users(self, request, queryset):
        plan = request.POST.get("plan")
        duration = request.POST.get("duration")
        if plan or duration:
            for i in queryset.all():
                UserPlan.create_plan_for_user(i, plan, duration)
        self.message_user(request, "User Plans successfully updated")


@admin.register(AgentCustomer)
class AgentCustomerAdmin(ServicesModelAdmin):
    list_display = ["email", "first_name", "last_name", "agent", "country"]
    search_fields = ["email", "agent__email"]


@admin.register(RegistrationServiceCvprofile)
class CVProfile(ServicesModelAdmin):
    list_display = ["email", "pk", "completed", "customer"]
    search_fields = ["user__email", "customer__email"]
    list_filter = ["completed"]
    actions = ["update_cv_data", "update_mailing_list"]

    def email(self, obj):
        if obj.user:
            return obj.user.email
        if obj.customer:
            return obj.customer.email

    def update_mailing_list(self, request, queryset):
        mail.update_current_steps_of_profiles(queryset.select_related("user").all())

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            paid_count=models.Count(
                "user__userpayment",
                filter=models.Q(user__userpayment__made_payment=True),
            )
        )
        return queryset

    def download_template(self, obj):
        if obj.paid_count > 0:
            return mark_safe(
                f'<a href="{settings.PAYMENT_SERVICE}/download-receipt/{obj.order}">Download receipt</a>'
            )
        return ""
