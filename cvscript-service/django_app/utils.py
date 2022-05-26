import typing
import random
from django.http import HttpResponse

try:
    import ujson
except ImportError:
    import json as ujson
import json
import requests
from functools import wraps
from django.conf import settings
from cv_utils.client import get_cvscript


class JsonResponse(HttpResponse):
    """
    An HTTP response class that consumes data to be serialized to JSON.

    :param data: Data to be dumped into json. By default only ``dict`` objects
      are allowed to be passed due to a security flaw before EcmaScript 5. See
      the ``safe`` parameter for more information.
    :param encoder: Should be a json encoder class. Defaults to
      ``django.core.serializers.json.DjangoJSONEncoder``.
    :param safe: Controls if only ``dict`` objects may be serialized. Defaults
      to ``True``.
    :param json_dumps_params: A dictionary of kwargs passed to json.dumps().
    """

    def __init__(self, data, **kwargs):
        kwargs.setdefault("content_type", "application/json")
        data = ujson.dumps(data)
        super().__init__(content=data, **kwargs)


def authenticate(token):
    """util function to validate token"""
    response = requests.post(settings.AUTHENTICATION_SERVICE, json={"token": token})
    if response.status_code < 400:
        return response.json()
    return None


def get_user_cvscripts(token, kind, agent=False, **kwargs):
    user_id = None
    headers = None
    if agent:
        headers = {"Authorization": f"Token {token}"}
    else:
        result = authenticate(token)
        if result:
            user_id = result["user_id"]
    additional_props = {}
    if agent:
        additional_props = kwargs
    if user_id or headers:
        response = get_cvscript(
            kind,
            f"{settings.CV_PROFILE_SERVICE}/v2/graphql",
            user_id=user_id,
            headers=headers,
            **additional_props,
        )
        if response:
            return response["result"]
    return []


def login_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header:
                return JsonResponse(
                    {
                        "errors": "Ensure to set the Authorization Header with your user token"
                    },
                    status=403,
                )
            token = auth_header.replace("Bearer", "").replace("Token", "").strip()
            result = authenticate(token)
            if not result:
                return JsonResponse(
                    {"errors": "This token is either invalid or expired"}, status=403
                )
            request.session["user_id"] = result["user_id"]
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator

def randomizer(scripts: typing.List[str], count: int) -> typing.List[str]:
    result = []
    while len(result) < count:
        value = random.choice(scripts)
        if value not in result:
            result.append(value)
    return result
