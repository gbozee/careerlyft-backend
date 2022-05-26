from django.db import models
from datetime import datetime, timedelta
from django.contrib.postgres.fields import JSONField
from cv_profiles.models import Customer, Agent
from cv_utils.payment import PricingMixin
from cv_utils import utils as c_utils
from admin_service.utils import SharedMixin
from paystack.utils import PaystackAPI


class Plan(models.Model, SharedMixin):
    name = models.CharField(max_length=255)
    data = JSONField(
        default=PricingMixin.PLAN_OPTIONS, blank=True
    )  # This field type is a guess.
    resume_allowed = models.IntegerField(blank=True, null=True)
    kind = models.CharField(
        max_length=50,
        choices=[("client", "client"), ("agent", "agent")],
        default="client",
    )
    plan_details = JSONField(blank=True, default={})

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = "authentication_service_plan"

    @property
    def paystack_api(self):
        return PaystackAPI()

    def set_or_update_data(self, duration, data):
        params = {
            "name": f"{self.name} {duration.title()}",
            "amount": {
                key: value for key, value in self.full_duration_data(duration).items()
            },
        }
        if data:
            result = self.paystack_api.subscription_api.update_plans(data, params)
        else:
            result = self.paystack_api.subscription_api.create_plans(
                {"interval": duration, **params}
            )
        return result[1]

    def full_duration_data(self, duration="monthly"):
        data = self.data["amount"]
        discount = self.data["discount"]
        if duration != "annually":
            return data[duration]
        monthly = data.get("monthly")
        return {
            key: round(value * 12 * (1 - (discount / 100)), 1)
            for key, value in monthly.items()
        }

    def sync_with_paystack(self):
        monthly_result = self.set_or_update_data(
            "monthly", self.plan_details.get("monthly")
        )
        yearly_result = self.set_or_update_data(
            "annually", self.plan_details.get("annually")
        )
        self.plan_details = {"monthly": monthly_result, "annually": yearly_result}
        self.save()

    @classmethod
    def create_plans_on_paystack(cls, plans):
        for plan in plans:
            plan.sync_with_paystack()


class BasePlan(models.Model):
    currency = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    last_renewed = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def create_free_plan(cls, user):
        plan = user.plan.first()
        kls = user.__class__.__name__
        kind = "client"
        if kls == "Agent":
            kind = "agent"
        if not plan:
            currency = c_utils.get_currency(user.country)
            plan, _ = Plan.s_objects.get_or_create(name="Free", data={}, kind=kind)
            return cls.s_objects.create(user=user, currency=currency, plan=plan)
        return plan

    @classmethod
    def create_plan_for_user(cls, user, plan, duration):
        fetched_plan = Plan.s_objects.filter(name=plan).first()
        instance = cls.create_free_plan(user)
        instance.plan = fetched_plan
        instance.update_duration(duration)
        instance.save()

    def update_duration(self, duration=None):
        options = {
            "quarterly": 90,
            "semi_annual": 180,
            "annual": 365,
            "weekly": 7,
            "fortnight": 14,
            "monthly": 30,
        }
        if duration:
            last_renewed = self.last_renewed or datetime.now()
            value = options.get(duration.lower())
            if value:
                self.duration = duration
                self.expiry_date = last_renewed + timedelta(days=value)


class UserPlan(BasePlan, SharedMixin):
    plan = models.ForeignKey(
        Plan, related_name="users", on_delete=models.SET_NULL, blank=True, null=True
    )
    user = models.ForeignKey(Customer, related_name="plan", on_delete=models.CASCADE)

    class Meta:
        managed = False
        db_table = "authentication_service_userplan"


class AgentPlan(BasePlan, SharedMixin):
    plan = models.ForeignKey(
        Plan, related_name="agents", on_delete=models.SET_NULL, blank=True, null=True
    )
    user = models.ForeignKey(Agent, related_name="plan", on_delete=models.CASCADE)
    plan_info = JSONField(default={})

    class Meta:
        managed = False
        db_table = "authentication_service_agentplan"
