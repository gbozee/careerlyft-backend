from django.db import models
from django.contrib.postgres.fields import JSONField
from admin_service.utils import SharedMixin

# Create your models here.


class CustomerManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.using('services')


class User(models.Model):
    password = models.CharField(max_length=128, blank=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(unique=True, max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    country = models.CharField(max_length=200, blank=True, null=True)
    email_subscribed = models.BooleanField(default=False)
    feature_notification = models.BooleanField(default=True)
    verified_email = models.BooleanField()
    other_details = JSONField(default={}, blank=True)
    objects = CustomerManager()

    class Meta:
        abstract = True

    @property
    def plan_name(self):
        plan = self.get_plan()
        return plan.plan.name

    def __str__(self):
        return self.email


class Customer(User, SharedMixin):
    contact_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    photo_url = models.CharField(max_length=200, blank=True, null=True)
    # This field type is a guess.
    social = JSONField(null=True, blank=True)
    last_stop_point = models.CharField(max_length=100, blank=True, null=True)
    shared_networks = JSONField(default=[], blank=True)
    claimed_template = models.BooleanField(default=False)
    dob = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'authentication_service_user'

    def get_plan(self):
        from payments.models import UserPlan
        return UserPlan.create_free_plan(self)


class Agent(User, SharedMixin):
    CHOICES = (
        ("self-employed", "Self employed"),
        ("2_TO_10", "2-10 employees"),
        ("11_TO_50", "11-50 employees"),
        ("51_TO_200", "51-200 employees"),
        ("200+", "200+ employees"),
    )
    business_id = models.CharField(unique=True, max_length=6)
    company_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True, null=True)
    company_size = models.CharField(
        max_length=100, blank=True, choices=CHOICES)
    website = models.TextField(blank=True)
    is_owner = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'authentication_service_agent'

    def get_plan(self):
        from payments.models import AgentPlan
        return AgentPlan.create_free_plan(self)
