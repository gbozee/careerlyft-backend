import pytest
import json
from graphene_utils import tests as test_utils
from starlette.testclient import TestClient
from cv_utils.tests import MockResponse
from run import app
from django.conf import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def authorized(mocker, agent_data):
    def _authorized(token):
        status_code = 200
        if not token:
            status_code = 400
        auth = mocker.patch("cv_utils.client.authorize_agent")
        auth.return_value = [
            MockResponse(
                dict(data=dict(agentDetails=agent_data)), status_code=status_code
            ),
            "agentDetails",
        ]
        return auth

    return _authorized


@pytest.fixture
def agent_data():
    return {
        "pk": 101,
        "first_name": "Danny",
        "last_name": "Novca",
        "email": "danny@example.com",
        "phone": "+2347023322321",
        "country": "Nigeria",
        "company_name": "Eleja Systems",
    }


@pytest.fixture
def customers_call(graphql_call, authorized):
    def _custoem_call(token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        auth = authorized(token)

        result = graphql_call(
            mutationName="getCustomers",
            params=[],
            fields="data{\n%s\n}\npage\ncount"
            % "\n".join(["first_name", "last_name", "email", "id"]),
            headers=headers,
        )
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _custoem_call


@pytest.fixture
def generate_resume_call(graphql_call):
    def _generate_resume_call(job_position):
        headers = None
        result = graphql_call(
            mutationName="generateResume",
            params=[
                {"type": "String!", "value": job_position, "field": "job_position"}
            ],
            fields="",
            headers=headers,
        )
        return result

    return _generate_resume_call


@pytest.fixture
def customers_create(graphql_call, authorized):
    def _customers_create(data=None, id=None, token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        iauth = authorized(token)
        params = [{"type": "CustomerInputType!", "value": data, "field": "details"}]
        if id:
            params.append({"type": "Int", "value": id, "field": "customer_id"})
        result = graphql_call(
            mutationName="addOrEditCustomer",
            params=params,
            fields="\n".join(["id", "first_name", "last_name", "email"]),
            headers=headers,
        )
        if token:
            iauth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _customers_create


@pytest.fixture
def customer_delete(graphql_call, authorized):
    def _customers_create(id, token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        iauth = authorized(token)
        params = [{"type": "Int!", "value": id, "field": "customer_id"}]
        result = graphql_call(
            mutationName="deleteCustomer", params=params, fields=None, headers=headers
        )
        if token:
            iauth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _customers_create


@pytest.fixture
def resumes_call(graphql_call, authorized):
    def _custoem_call(token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        auth = authorized(token)

        result = graphql_call(
            mutationName="getResumes",
            params=[],
            fields="data\npage\ncount",
            headers=headers,
        )
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _custoem_call


@pytest.fixture
def user_cvscripts_call(graphql_call, authorized):
    def _call(kind, user_id=None, token=None, **kwargs):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        auth = authorized(token)
        params = [{"type": "String!", "value": kind, "field": "kind"}]
        if user_id:
            params.append({"type": "Int", "value": user_id, "field": "user_id"})
        if kwargs:
            for key, value in kwargs.items():
                params.append({"type": "String", "value": value, "field": key})
        result = graphql_call(
            mutationName="getCVScript", params=params, fields="result", headers=headers
        )
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _call


@pytest.fixture
def resume_fetch(client, authorized):
    def _fetch(pk, token="1000001"):
        auth = authorized(token)
        result = client.get(f"/v2/resumes/{pk}", params={"token": token})
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result.json()

    return _fetch


@pytest.fixture
def resume_add(graphql_call, authorized):
    def _custoem_call(data=None, resume_id=None, token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        auth = authorized(token)
        if data:
            params = [{"type": "ResumeInput!", "value": data, "field": "details"}]
        else:
            params = [{"type": "Int", "value": resume_id, "field": "cv_id"}]
        result = graphql_call(
            mutationName="createOrDuplicateResume",
            params=params,
            fields=None,
            headers=headers,
        )
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _custoem_call


@pytest.fixture
def resume_delete(graphql_call, authorized):
    def _customers_create(id, token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        iauth = authorized(token)
        params = [{"type": "Int!", "value": id, "field": "cv_id"}]
        result = graphql_call(
            mutationName="deleteResume", params=params, fields=None, headers=headers
        )
        if token:
            iauth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _customers_create


@pytest.fixture
def resume_save(graphql_call, authorized):
    def _custoem_call(data, resume_id, token="100001"):
        headers = None
        if token:
            headers = {"Authorization": f"Token {token}"}
        auth = authorized(token)
        params = [
            {"type": "JSONString!", "value": json.dumps(data), "field": "details"},
            {"type": "Int!", "value": resume_id, "field": "cv_id"},
        ]
        result = graphql_call(
            mutationName="saveResume", params=params, fields=None, headers=headers
        )
        if token:
            auth.assert_called_once_with(
                settings.AUTHENTICATION_HOST + "/v2/graphql", token
            )
        return result

    return _custoem_call


from cv_utils.tests import *

# pytest_plugins = ['cv_utils.tests']
