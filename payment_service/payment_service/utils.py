from functools import wraps
import json
from django.http import JsonResponse
import requests
from django.conf import settings
from cv_utils import mail, starlette, client as client_api
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


def authenticate(token, shared_network=None, plan=None):
    """util function to validate token"""
    post_data = {"token": token, "user_details": True}
    if shared_network:
        post_data["shared_network"] = shared_network
    if plan:
        post_data["pricing"] = plan
    response = requests.post(settings.AUTHENTICATION_SERVICE, json=post_data)
    if response.status_code < 400:
        return response.json()
    return None


def authenticate_agent(token, shared_network=None, plan=None):
    url = settings.AUTH_ENDPOINT + '/v2/graphql'
    response, mutationName = client_api.authorize_agent(
        url, token, with_plan=True)
    if response.status_code < 400:
        result = response.json()['data']
        plan_details = result['getPlans']
        personal_info = result[mutationName]
        user_id = personal_info.pop('pk')
        phone_nummber = personal_info.pop('phone', "")
        return {
            'shared_networks': {
                **personal_info, 'phone_number': phone_nummber
            },
            'pricing': plan_details,
            "token": token,
            'user_id': user_id
        }
    return None


@starlette.sync_to_async
def async_authenticate(*args, **kwargs):
    if 'agent' in args:
        return authenticate_agent(*args)
    return authenticate(*args, **kwargs)


def update_list_after_payment_made(email):
    data = {"email": email}
    mail.made_payment([data])


def paid_for_plan(**kwargs):
    mail.plan_payment_notice([kwargs])


def async_login_required():
    def decorator(view_func):
        @wraps(view_func)
        async def _wrapped_view(request, *args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                logger.error(
                    "Failed authorization",
                    exc_info=True,
                    extra={"request": request},
                )
                return JSONResponse(
                    {
                        "errors":
                        "Ensure to set the Authorization Header with your user token"
                    },
                    status_code=403,
                )
            token = auth_header.replace("Bearer", "").replace("Token",
                                                              "").strip()
            if request.method == "POST":
                data = await request.json()
                kwar = [token]
                kind = data.get('kind', 'client')
                if data.get("plan"):
                    kwar.append(True)
                    kwar.append(kind)
                request.cleaned_body = data

            result = await async_authenticate(*kwar)
            # print(result)
            if not result:
                return JSONResponse(
                    {
                        "errors": "This token is either invalid or expired"
                    },
                    status_code=403)
            request.user_id = result["user_id"]
            request.shared_networks = {}
            if "pricing" in result.keys():
                request.pricing = result["pricing"]
            if "shared_networks" in result.keys():
                request.shared_networks = {
                    **result["shared_networks"], "token": token
                }
            return await view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def login_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header:
                return JsonResponse(
                    {
                        "errors":
                        "Ensure to set the Authorization Header with your user token"
                    },
                    status=403,
                )
            token = auth_header.replace("Bearer", "").replace("Token",
                                                              "").strip()
            kwar = [token]
            if request.method == "POST":
                data = json.loads(request.body)
                if data.get("network"):
                    kwar.append(data["network"])
                request.cleaned_body = data
            if request.method == 'POST':
                kind = data.get('kind')
                if kind:
                    result = authenticate_agent(*kwar)
                else:
                    result = authenticate(*kwar)

            else:
                result = authenticate(*kwar)

            if not result:
                return JsonResponse(
                    {
                        "errors": "This token is either invalid or expired"
                    },
                    status=403)
            request.user_id = result["user_id"]
            request.shared_networks = {}
            if "shared_networks" in result.keys():
                request.shared_networks = result["shared_networks"]
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def when_logged_in():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            country = request.GET.get("country")
            request.country = country
            request.user = None
            if auth_header:
                token = auth_header.replace("Bearer", "").replace("Token",
                                                                  "").strip()
                kwar = [token]
                result = authenticate(*kwar)
                if result:
                    request.session["user_id"] = result["user_id"]
                    request.user = result
                    networks = result.get("shared_networks")
                    if networks:
                        request.country = networks.get("country")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
