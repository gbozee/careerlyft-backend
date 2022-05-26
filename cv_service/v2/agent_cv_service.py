from cv_utils.backends import ValidationError
from cv_utils import client as client_api
import django

django.setup()
from django.conf import settings
from django.core.paginator import Paginator
from registration_service.models import AgentCustomer, CVProfile


def validateToken(token, kind="agent"):
    url = settings.AUTHENTICATION_HOST + "/v2/graphql"
    response, mutationName = client_api.authorize_agent(url, token)
    if response.status_code < 400:
        result = response.json()["data"]
        personal_info = result[mutationName]
        phone_number = personal_info.pop("phone", "")
        return {
            "personal_info": {**personal_info, "phone_number": phone_number},
            "user_id": personal_info["pk"],
        }
    else:
        result = response.json()
        raise ValidationError(result["detail"])


def paginate_result(result, **kwargs):
    paginator = Paginator(result, kwargs["per_page"])
    page = paginator.page(kwargs["current_page"])
    return {"items": page.object_list, "count": paginator.count}


def getCustomers(agent_id, **kwargs):
    result = AgentCustomer.get_agent_customers(agent_id)
    return paginate_result(result, **kwargs)


def getResumes(agent_id, **kwargs):
    customer_id = kwargs.pop("customer_id", None)
    result = CVProfile.all_user_cvs(agent_id=agent_id)
    if customer_id:
        result = result.filter(customer_id=customer_id)
    return paginate_result(result, **kwargs)


def createCustomer(agent_id, kwargs, customer_id=None):
    if customer_id:
        data = AgentCustomer.objects.filter(agent_id=agent_id, pk=customer_id).first()
        for key, value in kwargs.items():
            setattr(data, key, value)
        data.save()
        return data
    return AgentCustomer.objects.create(**kwargs, agent_id=agent_id)


def deleteCustomer(agent_id, customer_id):
    result = AgentCustomer.objects.filter(agent_id=agent_id, pk=customer_id).delete()
    return result[0]


def createOrDuplicateResume(agent_id, details=None, cv_id=None):
    if details:
        customer = details.pop("customer_email")
        customer = AgentCustomer.objects.filter(
            agent_id=agent_id, email__iexact=customer
        ).first()
        if customer:
            result = CVProfile.objects.create(**details, customer=customer)
            return result.rebuild_and_json()
    if cv_id:
        result = CVProfile.duplicate_cv(
            cv_id, agent_id=agent_id, job_position=None, job_category=None
        )
        return result


def getResumeDetail(cv_id, token):
    try:
        agent = validateToken(token)
        result = CVProfile.objects.filter(pk=cv_id).first()
        if result:
            return result.rebuild_and_json()
    except ValidationError:
        return None


def deleteResume(agent_id, cv_id):
    result = CVProfile.objects.filter(customer__agent_id=agent_id, pk=cv_id).delete()
    return result[0]


def saveResume(agent_id, details, cv_id):
    return CVProfile.save_cv_instance(cv_id, data=details, agent_id=agent_id)


def get_cv_scripts(agent_id, **kwargs):
    instances = CVProfile.objects.filter(customer__agent_id=agent_id)
    return instances.get_cv_scripts(**kwargs)


def get_cv_by_id(cv_id):
    pass
