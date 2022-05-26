from typing import Dict, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
import jwt
from django.contrib.auth.models import (
    AbstractBaseUser,
    UnicodeUsernameValidator,
    UserManager,
    send_mail,
    timezone,
)
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import _
from django.db import models
from django.contrib.postgres.fields import JSONField
from rest_framework_jwt import utils
from cv_utils import utils as c_utils
from .plans import Plan as PlanModel

PersonalInfoType = Union[str, Dict[str, str]]


def jwt_get_secret_key(payload=None, model=None):
    """
    For enhanced security you may want to use a secret key based on user.

    This way you have an option to logout only this user if:
        - token is compromised
        - password is changed
        - etc.
    """
    if utils.api_settings.JWT_GET_USER_SECRET_KEY:
        User = model  # noqa: N806
        # import pdb; pdb.set_trace()
        user = User.objects.get(pk=payload.get("user_id"))
        key = str(utils.api_settings.JWT_GET_USER_SECRET_KEY(user))
        return key
    return utils.api_settings.JWT_SECRET_KEY


def jwt_decode_handler(token, model=None):
    options = {"verify_exp": utils.api_settings.JWT_VERIFY_EXPIRATION}
    # get user from token, BEFORE verification, to get user secret key
    unverified_payload = utils.jwt.decode(token, None, False)
    secret_key = jwt_get_secret_key(unverified_payload, model)
    return utils.jwt.decode(
        token,
        utils.api_settings.JWT_PUBLIC_KEY or secret_key,
        utils.api_settings.JWT_VERIFY,
        options=options,
        leeway=utils.api_settings.JWT_LEEWAY,
        audience=utils.api_settings.JWT_AUDIENCE,
        issuer=utils.api_settings.JWT_ISSUER,
        algorithms=[utils.api_settings.JWT_ALGORITHM],
    )


def jwt_encode_handler(payload, model):
    key = utils.api_settings.JWT_PRIVATE_KEY or jwt_get_secret_key(payload, model)
    return utils.jwt.encode(payload, key, utils.api_settings.JWT_ALGORITHM).decode(
        "utf-8"
    )


def get_payload(token: str) -> Optional[str]:
    try:
        payload = utils.jwt_decode_handler(token)
    except jwt.ExpiredSignature:
        payload = None
    except jwt.DecodeError:
        payload = None
    # except ObjectDoesNotExist:
    #     payload = None
    if not payload:
        return None
    username = utils.jwt_get_username_from_payload_handler(payload)
    return username


class AbstractUser(AbstractBaseUser):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """

    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={"unique": _("A user with that username already exists.")},
    )
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text=_(
            "Designates that this user has all permissions without "
            "explicitly assigning them."
        ),
    )
    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class BaseUser(AbstractUser):
    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        error_messages={
            "unique": _("You have an account with us already, Login instead")
        },
    )
    country = models.CharField(max_length=200, null=True)
    last_login = models.DateTimeField(null=True)
    verified_email = models.BooleanField(default=False)
    email_subscribed = models.BooleanField(default=False)
    feature_notification = models.BooleanField(default=True)
    other_details = JSONField(default={})

    class Meta:
        abstract = True

    @property
    def password_hash(self) -> str:
        return self.password

    def get_new_token(self) -> str:
        payload = utils.jwt_payload_handler(self)
        return jwt_encode_handler(payload, self.__class__)

    @classmethod
    def verify_token(cls, token: str, email: str) -> bool:
        # may want to refactor)
        result = get_payload(token)
        if not result:
            return False
        return result == email

    def mark_as_verified(self):
        self.verified_email = True
        self.save()

    def create_plan(self, plan, **kwargs):
        f_plan = self.get_plan()
        duration = kwargs.pop("duration", None)
        f_plan.plan = PlanModel.objects.filter(name__iexact=plan).first()
        for key, value in kwargs.items():
            setattr(f_plan, key, value)
        f_plan.update_duration(duration)
        f_plan.save()
        return f_plan


class BasePlan(models.Model):
    plan = models.ForeignKey(
        "authentication_service.Plan",
        # related_name=related_name,
        on_delete=models.SET_NULL,
        null=True,
    )
    currency = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    last_renewed = models.DateTimeField(null=True, blank=True)
    countries = None

    class Meta:
        abstract = True

    def as_json(self):
        date = self.expiry_date
        renewed = self.last_renewed
        FORMAT = "%Y-%m-%d"
        if date:
            date = date.strftime(FORMAT)
        if renewed:
            renewed = renewed.strftime(FORMAT)
        plan_details = self.plan.plan_details
        expires = plan_details.get("expires")
        return {
            "name": self.plan.name,
            "currency": self.currency,
            "duration": self.duration,
            "last_renewed": renewed,
            "expiry_date": date,
            "resume_allowed": self.plan.get_resume_allowed(),
            "expires": expires,
        }

    def update_duration(self, duration=None):
        options = {
            "quarterly": 90,
            "semi_annual": 180,
            "semi_annually": 180,
            "annual": 365,
            "annually": 365,
            "monthly": 30,
        }
        if duration:
            last_renewed = self.last_renewed or datetime.now()
            value = options.get(duration.lower())
            if value:
                self.duration = duration
                self.expiry_date = last_renewed + timedelta(days=value)

    @classmethod
    def create_free_plan(cls, user):
        if not hasattr(user, "plan"):
            currency = c_utils.get_currency(
                user.country, working_countries=cls.countries
            )
            plan, _ = PlanModel.objects.get_or_create(name="Free", data={})
            return cls.objects.create(user=user, currency=currency, plan=plan)
        return user.plan
