from typing import NamedTuple, Optional
import django
from datetime import datetime
django.setup()

from authentication_service.models import Agent, Plan
from authentication_service.models.base import jwt_decode_handler
from rest_framework_jwt.serializers import (jwt, _,
                                            jwt_get_username_from_payload)

from authentication_service import utils
from django.conf import settings
from cv_utils.backends import ValidationError


class VerificationSerializer(object):
    def __init__(self, model):
        self.model = model

    def _check_payload(self, token):
        # Check payload valid (based off of JSONWebTokenAuthentication,
        # may want to refactor)
        try:
            payload = jwt_decode_handler(token, Agent)
        except jwt.ExpiredSignature:
            msg = _('Signature has expired.')
            raise ValidationError(msg)
        except jwt.DecodeError:
            msg = _('Error decoding signature.')
            raise ValidationError(msg)
        except Agent.DoesNotExist:
            msg = _('User does not exist.')
            raise ValidationError(msg)
        return payload

    def _check_user(self, payload):
        username = jwt_get_username_from_payload(payload)

        if not username:
            msg = _('Invalid payload.')
            raise ValidationError(msg)

        # Make sure user exists
        try:
            user = self.model.objects.get_by_natural_key(username)
        except self.model.DoesNotExist:
            msg = _("Agent doesn't exist.")
            raise ValidationError(msg)

        if not user.is_active:
            msg = _('Agent account is disabled.')
            raise ValidationError(msg)

        return user


class ResponseType(NamedTuple):
    token: str
    personal_info: dict


def agentLogin(**kwargs) -> Optional[ResponseType]:
    return Agent.fetchUser(**kwargs)


def agentSignup(**kwargs) -> Optional[ResponseType]:
    user = Agent.signup_agent(**kwargs)
    if user:
        return {'token': user.get_new_token(), 'personal_info': user.as_json}


def validateToken(token):
    validator = VerificationSerializer(Agent)
    payload = validator._check_payload(token=token)
    user = validator._check_user(payload=payload)
    return {'token': token, 'user': user}


def updatePersonalInfo(data, details) -> ResponseType:
    agent = data['user']
    for key, value in details.items():
        setattr(agent, key, value)
    agent.save()
    return {'token': data['token'], 'personal_info': agent.as_json}


def send_verify_email(domain, data):
    email = data['personal_info']['email']
    token = data['token']
    utils.send_mail(
        'verify_email', {
            "link":
            "{}/v2/verify-email-callback?email={}&token={}".format(
                domain, email, token),
            "first_name":
            "",
        }, email)


def afterUserEmailVerification(verified, email: str) -> Optional[str]:
    user = verified['user']
    if user.email == email:
        user.verified_email = True
        user.save()
        return settings.AGENT_URL


def initiateResetPassword(domain, **kwargs):
    agent = Agent.objects.filter(email__icontains=kwargs['email']).first()
    if agent:
        token = agent.get_new_token()
        return {
            "link":
            "{}/v2/verify-email-callback?email={}&token={}&callback_url={}".
            format(domain, agent.email, token, kwargs['callback_url']),
            "first_name":
            agent.first_name,
            "email":
            kwargs['email']
        }


def resetPassword(token, password):
    result = validateToken(token)
    if result:
        user = result['user']
        user.set_password(password)
        user.save()
        return True
    return False


def deleteAccount(data):
    agent = data['user']
    token = data['token']
    utils.delete_agent_payment_references(agent.pk, token)
    utils.delete_agent_cv_details(agent.pk, token)
    agent.delete()


def get_plans(kind):
    return Plan.get_plans(kind)


def update_plan(data, agent=None, email=None):
    date = data.pop("date", None)
    paystack_details = data.pop('paystack_details', None)
    if date:
        date = datetime.strptime(date, "%Y-%m-%d")
    new_agent = agent
    if email:
        new_agent = Agent.objects.filter(email=email).first()
    if new_agent:
        plan = new_agent.create_plan(last_renewed=date, **data)
        if paystack_details:
            plan.plan_info = paystack_details
            plan.save()
        return new_agent.as_json


def update_user_details(email, others):
    agent = Agent.objects.filter(email=email).first()
    if agent:
        data = agent.other_details
        data.update(**others)
        agent.other_details = data
        agent.save()
        return True
