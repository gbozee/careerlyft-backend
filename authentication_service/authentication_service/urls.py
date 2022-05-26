"""authentication_service URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import json
import logging

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import reverse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import RedirectView
from rest_framework import response, serializers, status, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt import views
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from . import forms, services, utils, models
from .utils import JsonResponse, send_mail

logger = logging.getLogger(__name__)


@api_view(["GET"])
@authentication_classes((SessionAuthentication, JSONWebTokenAuthentication))
@permission_classes((IsAuthenticated, ))
def send_verification_email(request):
    token = request.user.get_new_token()
    callback = request.GET.get("callback", "")
    instance = request.user
    link = request.build_absolute_uri(
        "{}?email={}&token={}&callback_url={}".format(
            reverse("verify_email_link"), instance.email, token, callback))
    services.send_mail(
        "verify_email",
        {
            "first_name": instance.first_name,
            "link": link
        },
        instance.email,
    )
    return JsonResponse({"sent": True})


def signup(request):
    dataFromBody = json.loads(request.body)
    about_details = dataFromBody.pop("about_details", {})
    token = None
    if hasattr(request, "auth"):
        token = request.auth

    req_status, result = services.signup_user(dataFromBody, request.user,
                                              token)
    if req_status:
        instance = result["instance"]
        token = instance.get_new_token()
        if result.get("callback"):
            services.update_about_info_and_send_verification_email(
                user_id=instance.pk,
                about=about_details,
                first_name=instance.first_name,
                link=request.build_absolute_uri(
                    "{}?email={}&token={}&callback_url={}".format(
                        reverse("verify_email_link"),
                        instance.email,
                        token,
                        result["callback"],
                    )),
                email=instance.email,
            )
        services.after_signup(
            dataFromBody,
            {
                "user_id": instance.pk,
                "token": token
            },
            about_details,
            result["data"],
        )
        return JsonResponse(
            {
                "user_id": instance.pk,
                "token": token
            },
            status=status.HTTP_201_CREATED)
    return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)


class JSONWebTokenSerializer(views.JSONWebTokenSerializer):
    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            "password": attrs.get("password"),
        }

        status, data = services.validate_token(credentials,
                                               attrs[self.username_field])
        if status:
            return data
        raise serializers.ValidationError(data)


class LoginView(views.ObtainJSONWebToken):
    serializer_class = JSONWebTokenSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response.data = services.validate_token_response(
            response.status_code, response.data)
        return response


class VerifyTokenView(views.VerifyJSONWebToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        last_stop_point = request.data.get("last_stop_point")
        response.data = services.after_token_verification(
            response.data,
            meta_flag=request.GET.get("meta"),
            shared_network=request.data.get("shared_network"),
            include_user_details=request.data.get("user_details"),
            cv_details=request.data.get("cv_details"),
            pricing=request.data.get("pricing"),
        )
        services.save_last_stop_point(last_stop_point,
                                      response.data["user_id"])
        return response


class VerifyEmail(RedirectView):
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        params = self.request.GET
        status, url = services.verify_email(
            params.get("email"), params.get("token"))
        if status:
            services.send_welcome_email_and_mailing_list(url["user"])
            return url["callback"]
        raise SuspiciousOperation("Invalid Email or Token passed")


def reset_password_redirect(request, token):
    email = forms.UserForm.get_email_from_token(token)
    callback = request.GET.get("callback_url", "{}{}".format(
        settings.CLIENT_URL, settings.CLIENT_PASSWORD_URL))
    if email:
        return HttpResponsePermanentRedirect("{}?token={}".format(
            callback, token))
        # return HttpResponsePermanentRedirect("{}?email={}".format(callback, email))
    raise SuspiciousOperation("Invalid Token passed")


def save_custom_data(request):
    data = json.loads(request.body)
    forms.UserForm.save_custom_data(data)
    return JsonResponse({"status": True})


def reset_password(request):
    body = json.loads(request.body)
    req_status, result, data = services.reset_password(body)
    if req_status:
        if data:
            services.send_forgot_password_link({
                **data,
                "link":
                "{}{}?callback_url={}".format(
                    settings.BASE_URL,
                    reverse("reset_password_redirect", args=[data["token"]]),
                    data.get("callback"),
                ),
            })

        return JsonResponse(result, status=status.HTTP_200_OK)
    return JsonResponse(result, status=status.HTTP_400_BAD_REQUEST)


class PersonalInfoView(views.APIView):
    authentication_classes = (SessionAuthentication,
                              JSONWebTokenAuthentication)
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        about = request.data.get("about_details")
        token = None
        if hasattr(request, "auth"):
            token = request.auth
        req_status, data = services.update_personal_info(
            request.data, request.user, token)
        if req_status:
            instance = data["instance"]
            services.update_about_info_and_send_verification_email(
                user_id=instance.pk, about=about)
            return Response(
                {
                    "user_id": instance.pk,
                    "token": token
                },
                status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, format=None):
        instance = request.user
        return Response(instance.as_json, status=status.HTTP_200_OK)

    def delete(self, request, format=None):
        instance = request.user
        services.delete_profile_data(request.user, request._auth.decode())

        return Response({"deleted": True}, status=status.HTTP_200_OK)


def generate_new_token(request, pk):
    is_admin = request.GET.get("is_admin")
    kind = request.GET.get('kind', 'user')
    if is_admin == "sama101":
        options = {'user': models.User, 'agent': models.Agent}
        new_token = options[kind].objects.filter(pk=pk).first()
        token = new_token.get_new_token()
        base_url = settings.CLIENT_URL
        if kind == 'agent':
            base_url = settings.AGENT_URL
        url = f"{base_url}/admin-login?isAdmin=true&token={token}"
        return JsonResponse({"url": url, "token": token})
    return JsonResponse({"error": True}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes((SessionAuthentication, JSONWebTokenAuthentication))
@permission_classes((IsAuthenticated, ))
def upgrade_plan(request, format=None):
    body = json.loads(request.body)
    result = services.upgrade_plan(request.user, body)
    return Response(result, status=status.HTTP_201_CREATED)


urlpatterns = [
    path("signup", signup, name="signup"),
    path("login", LoginView.as_view(), name="login"),
    path("api-token-refresh", views.refresh_jwt_token),
    path("api-token-verify", VerifyTokenView.as_view()),
    path(
        "generate-new-token/<pk>",
        generate_new_token,
        name="generate-new-token"),
    path("verify_email_link", VerifyEmail.as_view(), name="verify_email_link"),
    path(
        "login/reset/<token>",
        reset_password_redirect,
        name="reset_password_redirect"),
    path("reset-password", reset_password, name="reset_password"),
    path(
        "personal-info",
        PersonalInfoView.as_view(),
        name="update-personal-info"),
    path("upgrade-plan", upgrade_plan, name="upgrade_plan"),
    path(
        "save-custom-data",
        csrf_exempt(save_custom_data),
        name="save_custom_data"),
    path(
        "verify-email",
        send_verification_email,
        name="send_verification_email"),
]
