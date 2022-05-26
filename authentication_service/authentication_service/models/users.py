from typing import Dict, List, Optional, Set, Tuple, Union
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import UserManager as AUserManager
from django.contrib.auth.models import _
from django.contrib.postgres.fields import JSONField
from django.db import models
from cv_utils import payment, utils as c_utils
from .base import BaseUser, get_payload, BasePlan, PlanModel

PersonalInfoType = Union[str, Dict[str, str]]


class UserManager(AUserManager):
    def create_superuser(self, email, password, **extra_fields):
        return super().create_superuser(email, email, password, **extra_fields)


class User(BaseUser, PermissionsMixin):
    photo_url = models.URLField(blank=True, null=True)
    contact_address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    social = JSONField(null=True)
    last_stop_point = models.CharField(max_length=100, blank=True, null=True)
    shared_networks = JSONField(default=[])
    dob = models.CharField(max_length=50, blank=True, null=True)
    claimed_template = models.BooleanField(default=False)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: List[str] = []
    objects = UserManager()

    @classmethod
    def get_details(cls, id):
        return cls.objects.filter(pk=id).values("email", "photo_url", "social",
                                                "last_stop_point")

    @classmethod
    def get_cv_profile(cls, id):
        instance = User.objects.get(pk=id)
        return instance.as_json

    def add_network(self, network: Optional[str] = None
                    ) -> Dict[str, Union[str, Dict[str, str]]]:
        if network:
            self.shared_networks.append(network)
            self.shared_networks = list(set(self.shared_networks))
            self.save()
        quickbooks_customer_details = self.other_details.get(
            "quickbooks_customer_details", {})
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "country": self.country,
            "email": self.email,
            "dob": self.dob,
            "email_subscribed": self.email_subscribed,
            "feature_notification": self.feature_notification,
            "phone_number": self.phone_number,
            "contact_address": self.contact_address,
            "networks": self.shared_networks,
            "quickbooks_customer_details": quickbooks_customer_details,
        }

    @property
    def as_json(self) -> Dict[str, PersonalInfoType]:
        def_fields = [
            "pk",
            "first_name",
            "last_name",
            "country",
            "photo_url",
            "email",
            "dob",
            "verified_email",
            "feature_notification",
        ]
        result = {}
        for k in def_fields:
            result[k] = getattr(self, k)
        result["phone"] = self.phone_number
        result["address"] = self.contact_address
        result["location"] = self.contact_address
        result["social_link"] = ({
            "url": self.social["link"],
            "name": self.social["network"]
        } if self.social else {})
        result["email_subscribed"] = self.email_subscribed
        result["last_stop_point"] = self.last_stop_point
        result["social_link_url"] = (result["social_link"]["url"]
                                     if result.get("social_link") else "")
        plan = self.get_plan()
        # import pdb ; pdb.set_trace()
        result["plan"] = plan.as_json()
        return result

    def get_plan(self):
        return UserPlan.create_free_plan(self)


class UserPlan(BasePlan):
    user = models.OneToOneField(
        User, related_name="plan", on_delete=models.CASCADE)
    duration = models.CharField(
        max_length=100,
        choices=payment.PricingMixin.DURATIONS,
        null=True,
        blank=True)
