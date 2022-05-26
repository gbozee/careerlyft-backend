from django.db import models
from django.contrib.postgres.fields import JSONField
from cv_profiles.models import Customer, CustomerManager, Agent
from cv_utils.payment import PricingMixin
from .plans import Plan, UserPlan, AgentPlan

# Create your models here.
def default_value():
    return {"facebook": 10, "linkedin": 10, "twitter": 10}


class ReferralDiscount(models.Model, PricingMixin):
    data = JSONField(default=default_value)
    price_factor = JSONField(default=PricingMixin.DEFAULT)

    @classmethod
    def get_single(cls):
        result = cls.objects.first()
        if not result:
            result = cls.objects.create()
        return result.data

    @property
    def rates(self):
        return self.price_factor.get("rates")

    @property
    def base_rate(self):
        return self.price_factor.get("currencies")

    @classmethod
    def discount(self, network):
        return self.get_single()[network]

    class Meta:
        managed = False
        db_table = "payment_service_referraldiscount"


class PriceFactor(ReferralDiscount):
    class Meta:
        proxy = True


class TemplateInfo(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.TextField()
    data = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "payment_service_templatinfo"

    def __str__(self):
        return self.name


class UserPayment(models.Model):
    PAYSTACK = 1
    RAVEPAY = 2
    CHOICES = ((PAYSTACK, "Paystack"), (RAVEPAY, "Ravepay"))

    created = models.DateTimeField()
    modified = models.DateTimeField()
    # user = models.IntegerField(blank=True, null=True)
    user_instance = models.ForeignKey(
        Customer, null=True, db_column="user", on_delete=models.SET_NULL
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.CharField(primary_key=True, max_length=12)
    payment_method = models.IntegerField(choices=CHOICES, default=PAYSTACK)
    template = models.ForeignKey(TemplateInfo, models.DO_NOTHING, blank=True, null=True)
    made_payment = models.BooleanField()
    # This field type is a guess.
    extra_data = JSONField(blank=True, default=dict)
    objects = CustomerManager()

    class Meta:
        managed = False
        db_table = "payment_service_userpayment"

    def create_payment_plan(self, plan, duration):
        UserPlan.create_plan_for_user(self.user_instance, plan, duration)
        # plan = Plan.s_objects.filter(name=plan).first()
        # instance = UserPlan.create_free_plan(self.user_instance)
        # instance.plan = plan
        # instance.update_duration(duration)
        # instance.save()

    # @property
    # def user_instance(self):
    #     return Customer.objects.filter(pk=self.user).first()

    # @property
    # def email(self):
    #     if self.user_instance:
    #         return self.user_instance.email


class PlanPayment(models.Model):
    created = models.DateTimeField()
    modified = models.DateTimeField()
    # user = models.IntegerField(blank=True, null=True)
    user_instance = models.ForeignKey(
        Agent, null=True, db_column="user", on_delete=models.SET_NULL
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.CharField(primary_key=True, max_length=12)
    payment_method = models.IntegerField()
    made_payment = models.BooleanField()
    extra_data = JSONField(
        blank=True, default=dict, null=True
    )  # This field type is a guess.
    plan = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=100, blank=True, null=True)
    coupon = models.ForeignKey("Coupon", models.DO_NOTHING, blank=True, null=True)
    kind = models.CharField(
        max_length=50,
        default="client",
        choices=[("client", "client"), ("agent", "agent")],
    )

    class Meta:
        managed = False
        db_table = "payment_service_planpayment"


class Coupon(models.Model):
    code = models.CharField(max_length=50)
    expiry_date = models.DateTimeField(blank=True, null=True)
    limit = models.IntegerField(blank=True, null=True)
    discount = models.IntegerField(default=5)

    class Meta:
        managed = False
        db_table = "payment_service_coupon"
