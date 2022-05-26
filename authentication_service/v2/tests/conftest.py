from starlette.testclient import TestClient
from run import app
import pytest
from authentication_service import models
from graphene_utils import tests as test_utils
import json


@pytest.fixture
def client():
    # return client_app(app)
    return TestClient(app)


def create_test_agent():
    agent = models.Agent.signup_agent(
        company_name="Eleja Systems",
        first_name="John",
        email="john@example.com")
    agent.set_password('password101')
    agent.save()
    return agent


@pytest.fixture
def login_test(mocker, graphql_mutation):
    def _login_test(email, password):
        mock_jwt_func = mocker.patch(
            'authentication_service.models.base.jwt_encode_handler')
        token = "1001"
        mock_jwt_func.return_value = token
        create_test_agent()
        mutationName = "agentLogin"
        query = """
            query %s($email: String!, $password: String!){
                %s(email:$email, password:$password){
                   token
                   personal_info{
                      first_name
                      company_name
                      email
                      plan
                   }
                   errors
                }
            }
        """ % (mutationName, mutationName)
        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={
                'email': email,
                'password': password
            })
        assert models.Agent.objects.count() == 1
        return response['data'][mutationName]

    return _login_test


@pytest.fixture
def mock_token(mocker):
    def _mock_token(value="1001"):
        mock_jwt_func = mocker.patch(
            'authentication_service.models.base.jwt_encode_handler')
        token = value
        mock_jwt_func.return_value = token
        return mock_jwt_func

    return _mock_token


@pytest.fixture
def signup_test(mocker, graphql_mutation, mock_token):
    def _signup_test(details, step=1, additional_fields="", **kwargs):
        token = "1001"
        mock_token(token)
        mutationName = "agentSignupOrUpdate"
        query = """
            mutation %s($details: AgentSignupDetail!, $step: Int!){
                %s(details:$details, step: $step){
                   token
                   personal_info{
                      company_name
                      email
                      %s
                   }
                   errors
                }
            }
        """ % (mutationName, mutationName, additional_fields)
        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={
                'details': details,
                'step': step
            },
            **kwargs)
        if response.get('data'):
            return response['data'][mutationName]
        return response

    return _signup_test


@pytest.fixture
def profile_update_test(signup_test):
    def _profile_update_test(details, step=2, token="1001"):
        headers = None
        if token:
            headers = {'Authorization': f'Token {token}'}
        return signup_test(
            details,
            step=step,
            additional_fields="""
            pk
            first_name
            last_name
            country
            phone
            website
            company_size
            plan
            preferences""",
            headers=headers)

    return _profile_update_test


@pytest.fixture
def profile_fetch_test(graphql_mutation, valid_token):
    def _profile_fetch_test(token="1001"):
        agent = create_test_agent()
        if token != "1001":
            valid_token(agent)
        mutationName = "agentDetails"
        query = """
        query {%s{
            company_name
            email
        }}
        """ % mutationName
        headers = None
        if token:
            headers = {'Authorization': f'Token {token}'}
        response = graphql_mutation(query, headers=headers)
        if response.get('data'):
            return response['data'][mutationName]
        return response

    return _profile_fetch_test


@pytest.fixture
def plan_fetch_test(graphql_mutation):
    def _plan_fetch_test(kind='agent'):
        mutationName = "getPlans"
        query = """
        query %s($kind: String!){
            %s(kind: $kind){
                plans
                discount
                plan_code
                plan_id
                resume_allowed
            }
        }""" % (mutationName, mutationName)
        response = graphql_mutation(
            query, operationName=mutationName, variables={'kind': kind})
        if response.get('data'):
            return response['data'][mutationName]
        return response

    return _plan_fetch_test


@pytest.fixture
def update_quickbooks(graphql_mutation):
    def _update_quickbooks(data):
        agent = create_test_agent()
        mutationName = "agentQuickbooksUpdate"
        query = """
    query %s($details: JSONString!, $email: String!){
                    %s(details:$details, email: $email)
                }
    """ % (mutationName, mutationName)

        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={
                'details': json.dumps(data),
                'email': f"{agent.email}---subscription"
            })
        return response['data'][mutationName]

    return _update_quickbooks


@pytest.fixture
def update_plan_test(graphql_mutation, valid_token):
    def _update_plan_test(data, agent, token=None):
        valid_token(agent)
        mutationName = "agentUpdatePlan"
        query = """
        query %s($plan: String!, $currency: String!, $duration: String!,
            $date: String!, $paystack_details: JSONString, $email: String){
                %s(plan:$plan, currency:$currency, duration:$duration,
                date:$date, paystack_details: $paystack_details, email: $email){
                pk
                first_name
                last_name
                country
                phone
                email
                company_name
                plan

            }
        }
        """ % (mutationName, mutationName)
        headers = None
        if token:
            headers = {'Authorization': f'Token {token}'}
        response = graphql_mutation(
            query, operationName=mutationName, variables=data, headers=headers)
        if response.get('data'):
            return response['data'][mutationName]
        return response

    return _update_plan_test


@pytest.fixture
def reset_password_test(graphql_mutation):
    def _reset_password_test(email):
        mutationName = "agentResetPassword"
        query = """
            query %s($email: String, $callback_url: String){
                %s(email: $email, callback_url: $callback_url)
            }
        """ % (mutationName, mutationName)
        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={
                'email': email,
                "callback_url": "http://www.google.com"
            },
        )
        return response['data'][mutationName]

    return _reset_password_test


@pytest.fixture
def email_url_test(client):
    def _email_url_test(**details):
        agent = create_test_agent()
        new_token = agent.get_new_token()

        return client.get(
            "/v2/verify-email-callback",
            params={
                "email": agent.email,
                "token": new_token,
                **details
            })

    return _email_url_test


@pytest.fixture
def valid_token(mocker):
    def _valid_token(agent):
        mock_resolve_token = mocker.patch(
            'rest_framework_jwt.utils.jwt.decode')

        mock_resolve_token.return_value = {
            'user_id': agent.pk,
            'username': agent.email,
            'exp': 1549100031,
            'email': agent.email
        }
        return mock_resolve_token

    return _valid_token


@pytest.fixture
def validate_token_test(valid_token, graphql_mutation):
    def _validate_token_test(use_token=False):
        agent = create_test_agent()
        valid_token(agent)
        mutationName = "agentValidateToken"
        query = """
             query %s($email: String!){
                %s(email: $email)
            }
        """ % (mutationName, mutationName)
        headers = None
        if use_token:
            headers = {'Authorization': f'Token {agent.get_new_token()}'}
        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={'email': agent.email},
            headers=headers)
        return response['data'][mutationName]

    return _validate_token_test


@pytest.fixture
def reset_password(graphql_mutation):
    def _reset_password(token, password):
        mutationName = 'agentResetPassword'
        query = """
            query %s ($token: String, $password: String){
                %s(token:$token, password:$password)
            }
        """ % (mutationName, mutationName)
        response = graphql_mutation(
            query,
            operationName=mutationName,
            variables={
                'token': token,
                'password': password
            })
        return response['data'][mutationName]

    return _reset_password


@pytest.fixture
def delete_account_test(mocker, valid_token, graphql_mutation):
    def _delete_account_test(agent):
        mock_delete_payment_detail = mocker.patch(
            'authentication_service.utils.delete_agent_payment_references')
        mock_delete_cv_details = mocker.patch(
            'authentication_service.utils.delete_agent_cv_details')
        valid_token(agent)
        token = agent.get_new_token()
        mutationName = "agentDeleteAccount"
        query = """
            query %s{
                %s
            }""" % (mutationName, mutationName)
        headers = {'Authorization': f'Token {token}'}
        response = graphql_mutation(
            query, operationName=mutationName, headers=headers)
        mock_delete_cv_details.assert_called_once_with(agent.pk, token)
        mock_delete_payment_detail.assert_called_once_with(agent.pk, token)
        return response['data'][mutationName]

    return _delete_account_test


@pytest.fixture
def create_plans():
    def _create_plans(agent=False):
        if agent:
            models.Plan.objects.bulk_create([
                models.Plan(kind="agent", **x) for x in [
                    dict(
                        name="Starter",
                        plan_details={
                            "monthly": {
                                'name': "New monthly retainer",
                                'interval': 'monthly',
                                'plan': {
                                    'ngn': "PlanStarterNairaMonthly",
                                    'usd': "PlanStarterDollarMonthly"
                                },
                                'plan_id': {
                                    'usd': 28,
                                    'ngn': 29
                                }
                            },
                            "annually": {
                                'name': "New monthly retainer",
                                'interval': 'monthly',
                                'plan': {
                                    'ngn': "PlanStarterNairaAnnually",
                                    'usd': "PlanStarterDollarAnnually"
                                },
                                'plan_id': {
                                    'usd': 30,
                                    'ngn': 31
                                }
                            },
                        },
                        data={
                            "amount": {
                                "monthly": {
                                    "ngn": 9900,
                                    "usd": 39
                                }
                            },
                            "discount": 20
                        },
                        resume_allowed=20,
                    ),
                    dict(
                        name="Pro",
                        plan_details={
                            "monthly": {
                                'name': "New monthly retainer",
                                'interval': 'monthly',
                                'plan': {
                                    'ngn': "PlanProNairaMonthly",
                                    'usd': "PlanProDollarMonthly"
                                },
                                'plan_id': {
                                    'usd': 32,
                                    'ngn': 33
                                }
                            },
                            "annually": {
                                'name': "New monthly retainer",
                                'interval': 'monthly',
                                'plan': {
                                    'ngn': "PlanProNairaAnnually",
                                    'usd': "PlanProDollarAnnually"
                                },
                                'plan_id': {
                                    'usd': 34,
                                    'ngn': 35
                                }
                            },
                        },
                        data={
                            "amount": {
                                "monthly": {
                                    "ngn": 29900,
                                    "usd": 99
                                }
                            },
                            "discount": 20
                        },
                        resume_allowed=50,
                    )
                ]
            ])
        else:
            models.Plan.objects.create(name="Free", data={})
            models.Plan.objects.create(name="Pro", resume_allowed=None)

    return _create_plans


from cv_utils.tests import *
# pytest_plugins = ['cv_utils.tests']
