import json
import logging
import django
from datetime import datetime

django.setup()
import requests
from django.conf import settings
from rest_framework import status
from rest_framework_jwt.serializers import (
    _,
    authenticate,
    jwt_encode_handler,
    jwt_payload_handler,
    serializers,
)

from . import forms, utils
from .models import User, Plan, Agent
from .utils import send_mail
from cv_utils.starlette import database_sync_to_async

logger = logging.getLogger(__name__)


def signup_user(dataFromBody, user, token):
    data = forms.UserForm.transform_to_snake_case(dataFromBody)
    form = forms.UserForm(data)
    if form.is_valid():
        result, callback = form.save(user, token)
        return True, {"instance": result, "callback": callback, "data": data}
    logger.info(form.errors)
    if "email" in form.errors:
        if len(form.errors["email"]) == 0:
            logger.info(form.errors)
            return (
                False,
                {
                    "errors": {
                        "email": ["You have an account with us already, Login instead"]
                    }
                },
            )
    return False, {"errors": form.errors}


def after_signup(dataFromBody, result, about_details, data):
    last_stop_point = dataFromBody.get("last_stop_point")
    if last_stop_point:
        forms.UserForm.save_last_stop_point(result["user_id"], last_stop_point)
    if about_details:
        logger.info({"key": "about_details", "data": about_details})
        cv_details = User.get_cv_profile(result["user_id"])
        utils.save_about_details(cv_details, about_details, result["user_id"])
    utils.add_to_email_list(result["user_id"])


def validate_token_response(status_code, data):
    if status_code == status.HTTP_400_BAD_REQUEST:
        if "non_field_errors" in data:
            data["errors"] = data["non_field_errors"]
            del data["non_field_errors"]
        else:
            pass
    else:
        data["last_stop_point"] = forms.UserForm.get_last_stop_point(data["user_id"])
        data["working_cv"] = utils.fetch_last_uncompleted_cv(data["token"])["data"]
        data["personal_info"] = User.get_cv_profile(data["user_id"])
    return data


def validate_token(credentials, email_):
    if all(credentials.values()):
        user = authenticate(**credentials)
        if user:
            if not user.is_active:
                msg = _("User account is disabled.")
                return False, msg
            payload = jwt_payload_handler(user)

            return True, {"token": jwt_encode_handler(payload), "user": user}
        else:
            users = User.objects.filter(email__icontains=email_).first()
            if not users:
                msg = _(
                    "Looks like you don't have an account with us, sign up by creating your first Resume"
                )
            else:
                if not users.check_password(credentials["password"]):
                    msg = _("Your password is incorrect, try again")
                else:
                    msg = _(
                        "Your email and password combination is incorrect, try again"
                    )
            return False, msg
    else:
        msg = _("Your email and password combination is incorrect, try again")
        return False, msg


def after_token_verification(
    data,
    meta_flag=False,
    shared_network=False,
    include_user_details=False,
    cv_details=False,
    pricing=None,
):
    if shared_network or include_user_details or pricing:
        data["shared_networks"] = forms.UserForm.update_shared_social_media(
            data["user_id"], shared_network
        )
    if meta_flag == "1":
        data["metadata"] = list(User.get_details(id=int(data["user_id"])))
    if cv_details:
        data["personal-info"] = User.get_cv_profile(data["user_id"])
    if pricing:
        data["pricing"] = get_plans(kind=pricing)
    return data


def save_last_stop_point(last_stop_point, user_id):
    if last_stop_point:
        forms.UserForm.save_last_stop_point(user_id, last_stop_point)


def send_welcome_email_and_mailing_list(user):
    utils.add_to_email_list(user.pk, True)

    send_mail(
        "welcome_email",
        {"link": "https://app.careerlyft.com", "first_name": user.first_name},
        user.email,
    )


def verify_email(email, token):
    # callback_url = self.request.GET.get("callback_url", settings.CLIENT_URL)
    callback_url = settings.CLIENT_URL
    is_valid, user = forms.UserForm.verify_token(token, email, callback_url)
    if is_valid:
        result = callback_url
        if not result.startswith("http"):
            result = settings.CLIENT_URL

        return (
            True,
            {
                "callback": "{}?last_stop_point={}".format(
                    result, user.last_stop_point or ""
                ),
                "user": user,
            },
        )
    return False, None


def reset_password(data):
    form = forms.PasswordChangeForm(data)
    if form.is_valid():
        data, result = form.save()
        return True, result, data
    return False, {"errors": form.errors}, None


def send_forgot_password_link(data):
    send_mail(
        "forgot_password",
        {
            "link": data["link"],
            "first_name": data["first_name"],
            "email": data["email"],
        },
        data["email"],
    )


def update_personal_info(params, user, token):
    data = forms.UserForm.transform_to_snake_case(params)
    del data["email"]
    form = forms.UserForm(data, instance=user, existing=True)
    if form.is_valid():
        instance, callback = form.save(user)
        return True, {"instance": instance, "token": token, "callback_url": callback}
    return False, {"errors": form.errors}


def update_about_information(user_id, about):
    if about:
        cv_details = User.get_cv_profile(user_id)
        utils.save_about_details(cv_details, about, user_id)


def update_about_info_and_send_verification_email(**kwargs):
    update_about_information(kwargs["user_id"], kwargs["about"])
    if kwargs.get("link"):
        send_mail(
            "verify_email",
            {"first_name": kwargs["first_name"], "link": kwargs["link"]},
            kwargs["email"],
        )


def delete_profile_data(user, token):
    instance = user
    res = requests.delete(
        settings.CV_SERVICE_DELETE_URL, headers={"Authorization": f"Bearer {token}"}
    )
    instance.delete()
    # if res.status_code < 400:


# @database_sync_to_async
def get_plans(kind="client"):
    return Plan.get_plans(kind or "client")


def upgrade_plan(user, data):
    date = data.pop("date", None)
    if date:
        date = datetime.strptime(date, "%Y-%m-%d")
    plan = user.create_plan(last_renewed=date, **data)
    return {"user_id": user.pk, "plan": plan.as_json()}


def get_user_plan(user_id, agent=False, _all_fields=False):
    if agent:
        user = Agent.objects.filter(pk=user_id).first()
    else:
        user = User.objects.filter(pk=user_id).first()
    if user:
        result = user.get_plan().as_json()
        if _all_fields:
            return result
        return result["name"]

