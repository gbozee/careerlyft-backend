import pytest
from starlette.testclient import TestClient
from run import app
from django.conf import settings
from payment_service import models
from cv_utils.tests import MockResponse
from unittest.mock import call


@pytest.fixture
def paystack_api(mocker, monkeypatch):
    def _paystack_api(return_value,
                      key="verify_payment",
                      secret_key="MY-SECRET-KEY",
                      mock_data=None):
        monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret_key)

        mock_pastack = mocker.patch("payment_service.services.PaystackAPI")
        mock_instance = mock_pastack.return_value
        if return_value:
            new_mock = getattr(mock_instance, key)
            new_mock.return_value = return_value
        if mock_data:
            mock_instance.transaction_api.get_customer_and_auth_details.return_value = {
                'authorization': mock_data['authorization'],
                'customer': mock_data['customer'],
                'plan': mock_data['plan']
            }
        return mock_instance

    return _paystack_api


@pytest.fixture
def ravepay_api(mocker, monkeypatch):
    def _paystack_api(return_value,
                      key="verify_payment",
                      secret_key="MY-SECRET-KEY"):
        monkeypatch.setenv("PAYSTACK_SECRET_KEY", secret_key)

        mock_pastack = mocker.patch("payment_service.services.RavepayAPI")
        mock_instance = mock_pastack.return_value
        new_mock = getattr(mock_instance, key)
        new_mock.return_value = return_value
        return mock_instance

    return _paystack_api


@pytest.fixture
def quickbooks_api(mocker):
    def _quickbooks_api(return_value):
        mock_q_books = mocker.patch(
            "payment_service.models.base.QuickbooksAPI")

        mock_quickbooks = mock_q_books.return_value
        for k, value in return_value.items():
            mm = getattr(mock_quickbooks, k)
            mm.return_value = value
        return mock_quickbooks

    return _quickbooks_api


@pytest.fixture
def mock_mail(mocker):
    ock_mail = mocker.patch("payment_service.models.base.mail.send_mail")
    return ock_mail


@pytest.fixture
def mock_post(mocker):
    m_post = mocker.patch("requests.post")
    return m_post


@pytest.fixture
def json_call():
    def _json_call(method, url, **kwargs):
        client = TestClient(app)
        options = {"GET": client.get, "POST": client.post}
        return options[method](url, **kwargs)

    return _json_call


@pytest.fixture
def plan_call(json_call):
    def _plan_call(data, token):
        return json_call(
            'POST',
            '/v2/create-plan-payment',
            json=data,
            headers={'Authorization': "Bearer {}".format(token)})

    return _plan_call


@pytest.fixture
def build_response():
    def _build_response(amount,
                        link,
                        token,
                        country='NG',
                        discount=0,
                        kind='paystack',
                        default_country=True,
                        plan=False,
                        override_currency=None,
                        user_kind="client",
                        duration="annual",
                        **kwargs):
        old_kwargs = {
            "networks": [],
            "contact_address": "lorem ipsum is hjere",
        }
        working_kwargs = old_kwargs if len(kwargs.keys()) == 0 else kwargs

        key = settings.PAYSTACK_PUBLIC_KEY
        js_script = "https://js.paystack.co/v1/inline.js"
        c_props = {'NG': ['ngn', 'Nigeria'], 'GH': ['ghs', 'Ghana']}
        currency = c_props[country][0]
        if kind == 'ravepay':
            key = settings.RAVEPAY_PUBLIC_KEY
            js_script = "https://api.ravepay.co/flwv3-pug/getpaidx/api/flwpbf-inline.js"
        result = {
            "amount": float(amount) if plan else amount,
            "order": "ADESFG123453",
            "description": f"Pro {duration} subscription payment",
            "discount": discount,
            "paid": False,
            "base_country": country,
            "currency": override_currency or currency,
            "user_details": {
                "first_name":
                "Danny",
                "last_name":
                "Novca",
                "email":
                "danny@example.com",
                "phone_number":
                "+2347023322321",
                "country":
                "Nigeria" if default_country else c_props[country][1],
                "default_rate":
                float(amount + discount) if plan else amount + discount,
                "js_script":
                js_script,
                "kind":
                kind,
                "key":
                key,
                "redirect_url":
                link,
                "user_kind":
                user_kind,
                "token":
                token,
                **working_kwargs
            },
        }
        k = override_currency or currency
        if k not in ['ngn'] and default_country:
            result['user_details']['currency'] = k
        return dict(data=result)

    return _build_response


auth_value = {
    "pricing": {
        "plans": {
            "Pro": {
                "quarterly": {
                    "usd": 24.95,
                    "ngn": 3500,
                    "kes": 1500,
                    "gbp": 24.95,
                    "eur": 24.95,
                    "zar": 300,
                    "ghs": 100,
                },
                "semi_annual": {
                    "usd": 40,
                    "ngn": 6000,
                    "kes": 2500,
                    "gbp": 40,
                    "eur": 40,
                    "zar": 500,
                    "ghs": 180,
                },
            }
        },
        "discount": 20,
        "resume_allowed": {
            "Free": 1,
            "Pro": "unlimited"
        },
    },
    "shared_networks": {
        "networks": [],
        "first_name": "Danny",
        "last_name": "Novca",
        "email": "danny@example.com",
        "phone_number": "+2347023322321",
        "country": "Nigeria",
        "contact_address": "lorem ipsum is hjere"
        "",
    },
}


@pytest.fixture
def mock_auth(mock_auth_s):
    models.ReferralDiscount.objects.create()

    return mock_auth_s(extra=auth_value)


@pytest.fixture
def mock_auth_ghana(mock_auth_s):
    models.ReferralDiscount.objects.create()

    return mock_auth_s(
        extra={
            **auth_value,
            "shared_networks": {
                **auth_value["shared_networks"], "country": "Ghana"
            },
        })


@pytest.fixture
def mock_auth_s(mocker):
    def _mock_auth(extra={}, status_code=200):
        return create_mock(mocker, status_code, get_token(extra=extra))

    return _mock_auth


def create_mock(mocker, status_code=200, extra={}):
    token = "jeojwiojwioejwijowjo"
    ma = mocker.patch("payment_service.utils.requests.post")
    ma.return_value = MockResponse(
        {
            "user_id": 101,
            "token": token,
            **extra
        }, status_code=status_code)
    return ma


def get_token(extra={}):
    return {"user_id": 101, "token": "jeojwiojwioejwijowjo", **extra}


@pytest.fixture
def create_plan_instance():
    def _create_plan_instance(order,
                              amount,
                              kind="client",
                              made_payment=False,
                              **kwargs):
        models.PlanPayment.objects.create(
            order=order,
            plan="Pro",
            kind=kind,
            user=22,
            duration="annual",
            made_payment=made_payment,
            amount=amount,
            extra_data={
                "token": "234012",
                "networks": [],
                "first_name": "Danny",
                "default_rate": amount,
                "last_name": "Novca",
                "email": "danny@example.com",
                "phone_number": "+2347023322321",
                "country": "Nigeria",
                "email_subscribed": False,
                "contact_address": "lorem ipsum is hjere",
                **kwargs,
            },
        )

    return _create_plan_instance


@pytest.fixture
def mock_assertions():
    def _mock_assertions(
            record,
            mock_quickbooks,
            mock_post=None,
            mock_mail=None,
            paystack_details='{"plan": "PLN_0as2m9n02cl0kp6", "customer": {"id": 84312, "email": "bojack@horseman.com", "last_name": "Horseman", "first_name": "BoJack", "customer_code": "CUS_hdhye17yj8qd2tx"}, "authorization": {"bin": "412345", "bank": "TEST BANK", "last4": "1381", "channel": "card", "exp_year": "2018", "reusable": true, "card_type": "visa", "exp_month": "08", "signature": "SIG_idyuhgd87dUYSHO92D", "country_code": "NG", "authorization_code": "AUTH_8dfhjjdt"}}',
            kind="client"):
        mock_quickbooks.create_customer.assert_called_once_with(
            **{
                "email":
                record.extra_data["email"],
                "full_name":
                "{} {}".format(record.extra_data['first_name'],
                               record.extra_data['last_name']),
                "phone_number":
                record.extra_data["phone_number"],
                "location": {
                    "country": "Nigeria",
                    "address": record.extra_data["contact_address"],
                },
            })

        mock_quickbooks.create_sales_receipt.assert_called_once_with(
            {
                "id": "23",
                "name": "Danny Novaka"
            },
            {
                "currency": record.currency,
                "description": record.description,
                "price": record.price,
                "amount": record.price,
                "discount": 0,
            },
        )
        calls = [
            call(
                settings.AUTH_ENDPOINT + "/save-custom-data",
                json={
                    "user_id": record.user,
                    "data": {
                        "quickbooks_customer_details": {
                            "id": "23",
                            "name": "Danny Novaka",
                        }
                    },
                },
            ),
        ]
        if kind == 'client':
            calls.append(
                call(
                    settings.AUTH_ENDPOINT + "/upgrade-plan",
                    json={
                        "plan": "Pro",
                        "currency": "ngn",
                        "duration": "annual",
                        "date": record.modified.strftime("%Y-%m-%d"),
                    },
                    headers={"Authorization": f"Token 234012"},
                ))
        else:
            calls.append(
                call(
                    settings.AUTH_ENDPOINT + "/v2/graphql",
                    json={
                        'query':
                        '\n            query agentUpdatePlan($plan: String!, $currency: String!, $duration: String!,\n            $date: String!, $paystack_details: JSONString){\n                agentUpdatePlan(plan:$plan, currency:$currency, duration:$duration,\n                date:$date, paystack_details: $paystack_details)\n            }\n            ',
                        'variables': {
                            'plan': 'Pro',
                            'currency': 'ngn',
                            'duration': 'annual',
                            'date': '2019-02-06',
                            'paystack_details': paystack_details
                        },
                        'operationName':
                        'agentUpdatePlan'
                    },
                    headers={'Authorization': f"Token 234012"}))
        if mock_post:
            mock_post.assert_has_calls(calls, any_order=True)
        if mock_mail:
            mock_mail.assert_called_once_with(
                "first_plan_payment",
                {
                    "first_name": "Danny",
                    "plan": "Pro"
                },
                [record.extra_data["email"]],
            )

    return _mock_assertions


@pytest.fixture
def agent_auth(mocker):
    def _agent_auth(token, module_path='payment_service.utils.requests.post'):
        models.ReferralDiscount.objects.create()
        m_auth = mocker.patch(module_path)
        m_auth.return_value = MockResponse({
            "data": {
                'getPlans': {
                    "plans": {
                        "Starter": {
                            "monthly": {
                                "ngn": 9900,
                                "usd": 39
                            }
                        },
                        "Pro": {
                            "monthly": {
                                "ngn": 29900,
                                "usd": 99
                            }
                        }
                    },
                    "discount": 20,
                    "plan_code": {
                        'Starter': {
                            "monthly": {
                                'usd': "PlanStarterDollarMonthly",
                                'ngn': "PlanStarterNairaMonthly"
                            },
                            "annually": {
                                'usd': "PlanStarterDollarAnnually",
                                "ngn": "PlanStarterNairaAnnually"
                            },
                            'annual': {
                                'usd': "PlanStarterDollarAnnually",
                                "ngn": "PlanStarterNairaAnnually"
                            },
                        },
                        "Pro": {
                            "monthly": {
                                "usd": "PlanProDollarMonthly",
                                "ngn": "PlanProDollarMonthly"
                            },
                            "annually": {
                                'usd': "PlanProDollarAnnually",
                                "ngn": "PlanProNairaAnnually"
                            },
                            'annual': {
                                'usd': "PlanProDollarAnnually",
                                "ngn": "PlanProNairaAnnually"
                            },
                        }
                    }
                },
                "agentDetails": {
                    "pk": 101,
                    "first_name": "Danny",
                    "last_name": "Novca",
                    "email": "danny@example.com",
                    "phone": "+2347023322321",
                    "country": "Nigeria",
                    "company_name": "Eleja Systems"
                }
            }
        })

    return _agent_auth
