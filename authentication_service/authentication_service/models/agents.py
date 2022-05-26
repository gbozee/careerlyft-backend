import random
from typing import Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from django.contrib.postgres.fields import JSONField
from django.db import models
from cv_utils import payment, utils as c_utils
from .base import BaseUser, BasePlan

PersonalInfoType = Union[str, Dict[str, str]]


def generate_code(referral_class, key="order", length=12):
    def _generate_code():
        t = "ABCDEFGHIJKLOMNOPQRSTUVWXYZ1234567890"
        return "".join([random.choice(t) for i in range(length)])

    code = _generate_code()
    kwargs = {key: code}
    while referral_class.objects.filter(**kwargs).exists():
        code = _generate_code()
    return code


class Agent(BaseUser):
    CHOICES = (
        ("self-employed", "Self employed"),
        ("2_TO_10", "2-10 employees"),
        ("11_TO_50", "11-50 employees"),
        ("51_TO_200", "51-200 employees"),
        ("200+", "200+ employees"),
    )
    max_count = 6
    business_id = models.CharField(
        max_length=max_count, unique=True, db_index=True)
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    company_size = models.CharField(
        max_length=100, blank=True, choices=CHOICES)
    website = models.TextField(blank=True)
    is_owner = models.BooleanField(default=False)
    preferences = JSONField(default={})
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []

    @classmethod
    def fetchUser(cls, email=None, password=None):
        user = cls.objects.filter(email__iexact=email).first()
        if user:
            if user.check_password(password):
                return {
                    "token": user.get_new_token(),
                    "personal_info": user.as_json
                }
        return None

    @classmethod
    def signup_agent(cls, **kwargs):
        if not cls.objects.filter(email__iexact=kwargs["email"]).exists():
            password = kwargs.pop("password", None)

            user = {**kwargs, 'username': kwargs['email']}
            business_id = generate_code(cls, "business_id", cls.max_count)
            user["business_id"] = business_id
            result = cls.objects.create(**user, is_active=True)
            if password:
                result.set_password(password)
                result.save()
            return result

    @property
    def as_json(self) -> Dict[str, PersonalInfoType]:
        def_fields = [
            "pk",
            "first_name",
            "last_name",
            "country",
            "phone",
            "email",
            "business_id",
            "verified_email",
            "feature_notification",
            "company_size",
            "company_name",
            "website",
            "email_subscribed",
            'preferences',
            'is_owner'
        ]
        result = {}
        for k in def_fields:
            result[k] = getattr(self, k)
        result["plan"] = self.get_plan().as_json()
        return result

    def get_plan(self):
        return AgentPlan.create_free_plan(self)


class AgentPlan(BasePlan):
    user = models.OneToOneField(
        Agent, related_name="plan", on_delete=models.CASCADE)
    duration = models.CharField(
        max_length=100,
        choices=payment.PricingMixin.DURATIONS,
        null=True,
        blank=True)
    plan_info = JSONField(default={})
    countries = [{
        "name": "Nigeria",
        "dial_code": "+234",
        "code": "NG",
        "currency": "ngn"
    }]
