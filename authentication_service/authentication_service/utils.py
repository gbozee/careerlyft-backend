from django.http import HttpResponse
import requests
from django.conf import settings
import json as ujson
import json

# from . import mail
from cv_utils import mail, utils
import csv
import os
from django.db import models
from .models import User

BASE = os.path.dirname(os.path.abspath(__file__))


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


def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.

    Example:

    def jwt_response_payload_handler(token, user=None, request=None):
        return {
            'token': token,
            'user': UserSerializer(user, context={'request': request}).data
        }

    """
    return {"token": token, "user_id": user.pk}


def add_to_email_list(pk, verified=False):
    user = (User.objects.filter(pk=pk).annotate(
        completed_count=models.Value(0, output_field=models.IntegerField()))
            .first())
    mail.add_to_email_list([user], verified=False)


def send_mail(kind, params, to):
    recipient = to
    if type(recipient) == str:
        recipient = [recipient]
    mail.send_mail(kind, params, recipient)


def fetch_last_uncompleted_cv(token):
    result = requests.get(
        settings.CV_SERVICE_DELETE_URL,
        headers={"Authorization": f"Bearer {token}"})
    if result.status_code < 400:
        return result.json()
    return {"data": {}}


def save_about_details(personal_info, data, user_id):
    result = requests.post(
        f"{settings.CV_SERVICE_URL}/cv-profile-server",
        json={
            "data": data,
            "user_id": user_id,
            "personal-info": personal_info
        },
    )
    result.raise_for_status()


def delete_agent_payment_references(agent_id, token):
    pass


def delete_agent_cv_details(agent_id, token):
    pass


def get_emails():
    return utils.users_to_claim_template()
