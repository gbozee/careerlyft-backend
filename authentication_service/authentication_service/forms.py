import re

from django import forms
from django.conf import settings
from django.shortcuts import reverse

from . import utils
from .models import User, get_payload
from .utils import send_mail


class PasswordChangeForm(forms.Form):
    password = forms.CharField(required=False)
    email = forms.EmailField()
    token = forms.CharField(required=False)
    callback = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data["email"]
        self.user = User.objects.filter(email=email).first()
        if not self.user:
            self.add_error("email", "This email does not exist")

        return cleaned_data

    def save(self):
        password = self.cleaned_data.get("password")
        if password:
            self.user.set_password(password)
            self.user.save()
            return (
                None,
                {
                    "message": "password has been updated",
                    "email": self.user.email
                },
            )
        return (
            {
                "token": self.user.get_new_token(),
                "callback": self.cleaned_data.get("callback"),
                "first_name": self.user.first_name,
                "email": self.user.email,
            },
            {
                "message": "An email has been sent to reset password",
                "email": self.user.email,
            },
        )


class UserForm(forms.ModelForm):
    password = forms.CharField()
    social_link = forms.CharField(required=False)
    social_network = forms.CharField(required=False)
    callback = forms.CharField(required=False)
    gdpr = forms.BooleanField(required=False)
    feature_notification = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_subscribed'].required = False

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "country",
            "dob",
            "photo_url",
            "email_subscribed",
            "contact_address",
            "phone_number",
        ]

    def clean(self):
        cleaned_data = super().clean()
        social_link = cleaned_data.get("social_link")
        social_network = cleaned_data.get("social_network")
        # if (social_link and not social_network)or (social_network and not social_link):
        #     self.add_error(
        #         "social_link", "Ensure both social_netowrk and social_link is sent.")
        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data["email"]
        cust_email = User.objects.filter(email=email).exists()
        if cust_email:
            raise forms.ValidationError(
                "You have an account with us already, Login instead")
        return email

    @classmethod
    def save_custom_data(cls, data):
        user_id = data.get("user_id")
        others = data.get("data")
        instance = User.objects.filter(pk=user_id).first()
        if instance:
            data = instance.other_details
            data.update(**others)
            instance.other_details = data
            instance.save()

    @classmethod
    def verify_token(cls, token, email, callback=None):
        result = User.verify_token(token, email)
        user = None
        if result:
            user = User.objects.get(email=email)
            user.mark_as_verified()

        return result, user

    @classmethod
    def get_email_from_token(cls, token):
        email = get_payload(token)
        if User.objects.filter(email=email).exists():
            return email
        return None

    @classmethod
    def get_last_stop_point(cls, user_id):
        user = User.objects.get(pk=user_id)
        return user.last_stop_point

    @classmethod
    def update_shared_social_media(cls, user_id, network):
        user = User.objects.get(pk=user_id)
        return user.add_network(network)

    @classmethod
    def save_last_stop_point(cls, user_id, last_stop_point):
        User.objects.filter(pk=user_id).update(last_stop_point=last_stop_point)

    def ex_user(self, user):
        instance = user
        for i in [
                "first_name",
                "last_name",
                "country",
                "dob",
                "feature_notification",
                "email_subscribed",
                "photo_url",
                "contact_address",
                "phone_number",
        ]:
            setattr(instance, i, self.cleaned_data[i])
        if self.cleaned_data["social_link"] and self.cleaned_data["social_network"]:
            instance.social = {
                "link": self.cleaned_data["social_link"],
                "network": self.cleaned_data["social_network"],
            }
        if self.cleaned_data.get("gdpr"):
            instance.email_subscribed = self.cleaned_data.get("gdpr")
        instance.save()
        return instance, None

    def save(self, user, commit=False):
        instance = super().save(commit=False)
        if self.existing_user:
            return self.ex_user(user)
        instance.username = self.cleaned_data["email"]
        if self.cleaned_data["social_link"] and self.cleaned_data["social_network"]:
            instance.social = {
                "link": self.cleaned_data["social_link"],
                "network": self.cleaned_data["social_network"],
            }
        instance.set_password(self.cleaned_data["password"])
        instance.email_subscribed = self.cleaned_data.get("gdpr")
        instance.save()
        return instance, self.cleaned_data.get("callback")
        # token = instance.get_new_token()
        # send_mail(
        #     "verify_email",
        #     {
        #         "first_name": instance.first_name,
        #         "link": request.build_absolute_uri(
        #             "{}?email={}&token={}&callback_url={}".format(
        #                 reverse("verify_email_link"),
        #                 instance.email,
        #                 token,
        #                 self.cleaned_data.get("callback"),
        #             )
        #         ),
        #     },
        #     instance.email,
        # )
        # return {"user_id": instance.pk, "token": token}

    def __init__(self, *args, **kwargs):
        self.existing_user = kwargs.pop("existing", None)
        super(UserForm, self).__init__(*args, *kwargs)
        for field in ["first_name", "country", "last_name"]:
            self.fields[field].required = False
        if self.existing_user:
            self.fields["email"].required = False
            self.fields["email"].validators = []
            self.fields["password"].required = False

    @classmethod
    def transform_to_snake_case(cls, data):
        result = {}
        for key, value in data.items():
            result[convert(key)] = value
        return result


first_cap_re = re.compile("(.)([A-Z][a-z]+)")
all_cap_re = re.compile("([a-z0-9])([A-Z])")


def convert(name):
    s1 = first_cap_re.sub(r"\1_\2", name)
    return all_cap_re.sub(r"\1_\2", s1).lower()
