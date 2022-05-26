import django
from django.conf import settings

django.setup()
from functools import wraps
from django.http import JsonResponse
import requests
import logging

# import aiohttp
from django.conf import settings
import json
from cv_utils import mail
from .models import CVProfile
from starlette.responses import JSONResponse
from .services import sync_to_async

logger = logging.getLogger(__name__)


def update_mailing_list(email, user_id, completed=False, data=None):
    if completed:
        count = CVProfile.objects.filter(pk=user_id, completed=True).count()
        mail.completed_cv([{"email": email, "cv_completed": count}])
    else:
        mail.complete_profile_steps(
            [
                {
                    "email": email,
                    "job_category": data["job_category"],
                    "job_position": data["job_position"],
                    "last_stop_point": data["last_stop_point"],
                }
            ]
        )


def get_user_plan(user_id, agent=None):
    params = {}
    if agent:
        params = {"agent": True}
    response = requests.get(
        settings.AUTHENTICATION_HOST + f"/v2/user-plan/{user_id}", params=params,verify=False
    )
    if response.status_code < 400:
        return response.json()
    return None


def authenticate(token, **kwargs):
    """util function to validate token"""
    post_data = {"token": token}
    if kwargs:
        post_data.update(kwargs)
    response = requests.post(settings.AUTHENTICATION_SERVICE, json=post_data,verify=False)
    if response.status_code < 400:
        return response.json()
    return None


@sync_to_async
def async_authenticate(*args, **kwargs):
    return authenticate(*args, **kwargs)


async def authenticate_async(token, **kwargs):
    post_data = {"token": token}
    if kwargs:
        post_data.update(kwargs)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            settings.AUTHENTICATION_SERVICE, json=post_data
        ) as response:
            if response.status < 400:
                return await response.json()
            return None


def async_login_required(profile=False):
    def decorator(view_func):
        @wraps(view_func)
        async def _warpped_view(request, *args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                logger.error(
                    "Failed authorization",
                    exc_info=True,
                    extra={
                        # Optionally pass a request and we'll grab any information we can
                        "request": request
                    },
                )
                return JSONResponse(
                    {
                        "errors": "Ensure to set the Authorization Header with your user token"
                    },
                    status_code=403,
                )
            token = auth_header.replace("Bearer", "").replace("Token", "").strip()
            kwar = [token]
            kw = {}
            if profile:
                kw.update({"cv_details": True})
            if request.method == "POST":
                data = await request.json()
                last_stop_point = data.pop("last_stop_point", None)
                if last_stop_point:
                    kw.update({"last_stop_point": last_stop_point})
                request.cleaned_body = data
            result = await async_authenticate(*kwar, **kw)
            print("Fetched")
            # result = await authenticate_async(*kwar, **kw)
            if not result:
                return JSONResponse(
                    {"errors": "This token is either invalid or expired"},
                    status_code=403,
                )
            request.user_id = result["user_id"]
            if profile:
                request.user_data = result.get("personal-info")
            return await view_func(request, *args, **kwargs)

        return _warpped_view

    return decorator


def login_required(profile=False):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            auth_header = request.META.get("HTTP_AUTHORIZATION")

            if not auth_header:
                logger.error(
                    "Failed authorization",
                    exc_info=True,
                    extra={
                        # Optionally pass a request and we'll grab any information we can
                        "request": request
                    },
                )
                return JsonResponse(
                    {
                        "errors": "Ensure to set the Authorization Header with your user token"
                    },
                    status=403,
                )
            token = auth_header.replace("Bearer", "").replace("Token", "").strip()
            kwar = [token]
            kw = {}
            if profile:
                kw.update({"cv_details": True})
            if request.method == "POST":
                data = json.loads(request.body)
                last_stop_point = data.pop("last_stop_point", None)
                if last_stop_point:
                    kw.update({"last_stop_point": last_stop_point})
                request.cleaned_body = data
            result = authenticate(*kwar, **kw)
            if not result:
                return JsonResponse(
                    {"errors": "This token is either invalid or expired"}, status=403
                )
            request.session["user_id"] = result["user_id"]
            request.user_id = result["user_id"]
            if profile:
                request.user = result.get("personal-info")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
