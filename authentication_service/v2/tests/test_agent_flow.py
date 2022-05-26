import pytest
import json
from authentication_service import models
from django.conf import settings


def create_test_agent(country="Nigeria"):
    agent = models.Agent.signup_agent(
        company_name="Eleja Systems",
        first_name="John",
        email="john@example.com",
        country=country)
    agent.set_password('password101')
    agent.save()
    return agent


@pytest.mark.django_db(transaction=True)
def test_agent_login_successful(login_test):
    data = login_test('john@example.com', 'password101')
    assert data == {
        "token": "1001",
        "personal_info": {
            "first_name": "John",
            "company_name": "Eleja Systems",
            "email": "john@example.com",
            'plan': {
                'name': "Free",
                'currency': "usd",
                "duration": None,
                "last_renewed": None,
                "expiry_date": None,
                "resume_allowed": 1
            }
        },
        "errors": None
    }


@pytest.mark.django_db(transaction=True)
def test_agent_login_failure(login_test):
    data = login_test('john@example.com1', "password101")
    assert data == {
        "token": None,
        "personal_info": None,
        "errors": ["Invalid credentials"]
    }


@pytest.mark.django_db(transaction=True)
def test_agent_signup_success(mocker, signup_test):
    mock_verify_email_action = mocker.patch(
        'authentication_service.utils.send_mail')
    params = {
        'details': {
            'email': "john@example.com",
            'password': "password101",
            'company_name': 'Eleja Systems'
        },
        'step': 1
    }
    data = signup_test(params['details'], params['step'])
    assert models.Agent.objects.count() == 1
    assert data == {
        'token': "1001",
        'personal_info': {
            'company_name': "Eleja Systems",
            'email': 'john@example.com'
        },
        'errors': None
    }
    mock_verify_email_action.assert_called_once_with(
        "verify_email", {
            'link':
            "{}?email={}&token={}".format(
                "http://testserver/v2/verify-email-callback",
                "john@example.com",
                "1001",
            ),
            'first_name':
            ""
        }, "john@example.com")


@pytest.mark.django_db(transaction=True)
def test_agent_signup_fail(signup_test):
    create_test_agent()
    params = {
        'details': {
            'email': "john@example.com",
            'password': "password101",
            'company_name': 'Eleja Systems'
        },
        'step': 1
    }
    data = signup_test(params['details'], params['step'])
    assert data == {
        'token': None,
        'personal_info': None,
        'errors': ["The email provided already exists"]
    }


working_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6Imdib3plZUBnbWFpbC5jb20iLCJleHAiOjE1NDkxMDAwMzEsImVtYWlsIjoiZ2JvemVlQGdtYWlsLmNvbSJ9.YGrRxmnShSpceGr03zW2VzUkOrJdpOc4TZGIM-JL3Mc"

profile_data = {
    'first_name': "Danny",
    'last_name': "Jones",
    "country": "Nigeria",
    "phone": "07032233222",
    "website": "http://www.hotmail.com",
    "company_size": "self-employed"
}


@pytest.mark.django_db(transaction=True)
def test_agent_profile_update(mocker, profile_update_test):
    mock_resolve_token = mocker.patch('rest_framework_jwt.utils.jwt.decode')

    agent = create_test_agent()
    mock_resolve_token.return_value = {
        'user_id': agent.pk,
        'username': agent.email,
        'exp': 1549100031,
        'email': agent.email
    }
    data = profile_update_test(
        {
            **profile_data, 'preferences': {
                'beta_testing': True
            }
        },
        token=working_token,
    )
    assert data == {
        'token': working_token,
        'personal_info': {
            "pk": agent.pk,
            "company_name": "Eleja Systems",
            "email": "john@example.com",
            'first_name': "Danny",
            'last_name': "Jones",
            "country": "Nigeria",
            "phone": "07032233222",
            "website": "http://www.hotmail.com",
            "company_size": "self-employed",
            'plan': {
                'name': "Free",
                'currency': "ngn",
                "duration": None,
                "last_renewed": None,
                "expiry_date": None,
                "resume_allowed": 1
            },
            'preferences': {
                'beta_testing': True
            }
        },
        'errors': None
    }


@pytest.mark.django_db(transaction=True)
def test_agent_profile_update_without_token(profile_update_test):
    data = profile_update_test(profile_data)
    assert data == {'detail': 'Invalid token credentials'}


@pytest.mark.django_db(transaction=True)
def test_agent_profile_update_with_invalid_token(profile_update_test):
    data = profile_update_test(profile_data, token="1001")
    assert data == {'detail': 'Invalid token credentials'}


@pytest.mark.django_db(transaction=True)
def test_reset_password(email_url_test):
    response = email_url_test()
    assert response.status_code == 404
    assert response.request.url == settings.AGENT_URL + "/"
    assert models.Agent.objects.first().verified_email


@pytest.mark.django_db(transaction=True)
def test_reset_password_with_callback_url(email_url_test):
    response = email_url_test(callback_url="http://www.facebooke.com")
    assert response.status_code == 404
    assert response.request.url == 'http://www.facebooke.com/'


@pytest.mark.django_db(transaction=True)
def test_agent_reset_password_request(mocker, reset_password_test, mock_token):
    mock_token("1001")
    agent = create_test_agent()
    mock_verify_email_action = mocker.patch(
        'authentication_service.utils.send_mail')
    response = reset_password_test(agent.email)
    assert response is True
    mock_verify_email_action.assert_called_once_with(
        "forgot_password", {
            'link':
            "{}?email={}&token={}&callback_url={}".format(
                "http://testserver/v2/verify-email-callback", agent.email,
                "1001", "http://www.google.com"),
            'first_name':
            agent.first_name,
            'email':
            agent.email
        }, agent.email)


@pytest.mark.django_db(transaction=True)
def test_agent_validate_token_success(mocker, validate_token_test):
    assert validate_token_test(True)


@pytest.mark.django_db(transaction=True)
def test_agent_validate_token_failed(mocker, validate_token_test):
    assert not validate_token_test(False)


@pytest.mark.django_db(transaction=True)
def test_get_agent_profile_success(profile_fetch_test):
    result = profile_fetch_test(working_token)
    assert result == {
        'company_name': "Eleja Systems",
        'email': 'john@example.com'
    }


@pytest.mark.django_db(transaction=True)
def test_get_agent_profile_fail(profile_fetch_test):
    result = profile_fetch_test()
    assert result == {'detail': "Invalid token credentials"}


@pytest.mark.django_db(transaction=True)
def test_agent_reset_new_password(reset_password, valid_token):
    agent = create_test_agent()

    assert agent.check_password('password101')
    valid_token(agent)
    result = reset_password(working_token, 'newpassword')
    assert result
    new_agent = models.Agent.objects.get(pk=agent.pk)
    assert new_agent.check_password('newpassword')


@pytest.mark.django_db(transaction=True)
def test_check_agent_plan_has_expired():
    pass


@pytest.mark.django_db(transaction=True)
def test_get_agent_plan(plan_fetch_test, create_plans):
    create_plans(agent=True)
    result = plan_fetch_test()
    assert result == {
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
        "resume_allowed": {
            "Starter": 20,
            "Pro": 50
        },
        "plan_id": {
            'Starter': {
                "monthly": {
                    'usd': 28,
                    'ngn': 29
                },
                "annually": {
                    'usd': 30,
                    "ngn": 31
                },
                'annual': {
                    'usd': 30,
                    "ngn": 31
                },
            },
            "Pro": {
                "monthly": {
                    "usd": 32,
                    "ngn": 33
                },
                "annually": {
                    'usd': 34,
                    "ngn": 35
                },
                'annual': {
                    'usd': 34,
                    "ngn": 35
                },
            }
        },
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
                    "ngn": "PlanProNairaMonthly"
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
    }


@pytest.mark.django_db(transaction=True)
def test_update_agent_plan(create_plans, update_plan_test):
    create_plans(agent=True)
    agent = create_test_agent()
    response = update_plan_test({
        "plan":
        "Pro",
        "currency":
        "usd",
        "duration":
        "annually",
        "date":
        "2019-10-01",
        "paystack_details":
        json.dumps({
            "authorization": {
                "authorization_code": "AUTH_8dfhjjdt",
                "card_type": "visa",
                "last4": "1381",
                "exp_month": "08",
                "exp_year": "2018",
                "bin": "412345",
                "bank": "TEST BANK",
                "channel": "card",
                "signature": "SIG_idyuhgd87dUYSHO92D",
                "reusable": True,
                "country_code": "NG"
            },
            "customer": {
                "id": 84312,
                "customer_code": "CUS_hdhye17yj8qd2tx",
                "first_name": "BoJack",
                "last_name": "Horseman",
                "email": "bojack@horseman.com"
            },
            "plan": "PLN_0as2m9n02cl0kp6"
        })
    }, agent, agent.get_new_token())
    assert agent.plan.plan_info == {
        "authorization": {
            "authorization_code": "AUTH_8dfhjjdt",
            "card_type": "visa",
            "last4": "1381",
            "exp_month": "08",
            "exp_year": "2018",
            "bin": "412345",
            "bank": "TEST BANK",
            "channel": "card",
            "signature": "SIG_idyuhgd87dUYSHO92D",
            "reusable": True,
            "country_code": "NG"
        },
        "customer": {
            "id": 84312,
            "customer_code": "CUS_hdhye17yj8qd2tx",
            "first_name": "BoJack",
            "last_name": "Horseman",
            "email": "bojack@horseman.com"
        },
        "plan": "PLN_0as2m9n02cl0kp6"
    }


@pytest.mark.django_db(transaction=True)
def test_delete_agent_account(delete_account_test):
    agent = create_test_agent()
    result = delete_account_test(agent)
    assert result


@pytest.mark.django_db(transaction=True)
def test_plans_to_expire_in_x_days():
    pass


def test_cancel_subscription():
    pass


@pytest.mark.django_db(transaction=True)
def test_update_quickbooks_for_agent(update_quickbooks):
    dd = {'quickbooks_customer_details': {'id': "23", 'name': "Danny Novaka"}}
    result = update_quickbooks(dd)
    assert result
    agent = models.Agent.objects.first()
    assert agent.other_details == dd
    # response =


@pytest.mark.django_db(transaction=True)
def test_update_plan_without_token(create_plans, update_plan_test):
    create_plans(agent=True)
    agent = create_test_agent()
    response = update_plan_test({
        'email':
        f"{agent.email}---subscription",
        "plan":
        "Pro",
        "currency":
        "usd",
        "duration":
        "annually",
        "date":
        "2019-10-01",
        "paystack_details":
        json.dumps({
            "authorization": {
                "authorization_code": "AUTH_8dfhjjdt",
                "card_type": "visa",
                "last4": "1381",
                "exp_month": "08",
                "exp_year": "2018",
                "bin": "412345",
                "bank": "TEST BANK",
                "channel": "card",
                "signature": "SIG_idyuhgd87dUYSHO92D",
                "reusable": True,
                "country_code": "NG"
            },
            "customer": {
                "id": 84312,
                "customer_code": "CUS_hdhye17yj8qd2tx",
                "first_name": "BoJack",
                "last_name": "Horseman",
                "email": "bojack@horseman.com"
            },
            "plan": "PLN_0as2m9n02cl0kp6"
        })
    }, agent)
    assert response == {
        "pk": agent.pk,
        "company_name": "Eleja Systems",
        "email": "john@example.com",
        'first_name': "John",
        'last_name': "",
        "country": "Nigeria",
        "phone": None,
        "plan": {
            'name': "Pro",
            'currency': "usd",
            "duration": "annually",
            "last_renewed": "2019-10-01",
            "expiry_date": '2020-09-30',
            "resume_allowed": 50
        }
    }
    assert agent.plan.plan_info == {
        "authorization": {
            "authorization_code": "AUTH_8dfhjjdt",
            "card_type": "visa",
            "last4": "1381",
            "exp_month": "08",
            "exp_year": "2018",
            "bin": "412345",
            "bank": "TEST BANK",
            "channel": "card",
            "signature": "SIG_idyuhgd87dUYSHO92D",
            "reusable": True,
            "country_code": "NG"
        },
        "customer": {
            "id": 84312,
            "customer_code": "CUS_hdhye17yj8qd2tx",
            "first_name": "BoJack",
            "last_name": "Horseman",
            "email": "bojack@horseman.com"
        },
        "plan": "PLN_0as2m9n02cl0kp6"
    }


@pytest.mark.django_db(transaction=True)
def test_plan_update_after_notification_to_expire():
    pass
