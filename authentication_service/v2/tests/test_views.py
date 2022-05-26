from datetime import datetime
from starlette.testclient import TestClient
from run import app
import pytest
from authentication_service import models
from rest_framework import status


@pytest.mark.django_db(transaction=True)
def test_get_all_plans(client, create_plans):
    create_plans()
    response = client.get("/v2/plans")
    assert response.status_code == 200
    assert response.json() == {
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
    }


@pytest.mark.django_db(transaction=True)
def test_get_all_agent_plans(client, create_plans):
    create_plans(agent=True)
    response = client.get('/v2/plans', params={'kind': 'agent'})
    assert response.status_code == 200
    assert response.json() == {
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


def create_user_data(**kwargs):
    plan = kwargs.pop("plan", None)
    duration = kwargs.pop("duration", None)
    last_renewed = kwargs.pop("last_renewed", None)
    data = {
        "username":
        "b@example.com",
        "email":
        "b@example.com",
        "password":
        "set_password",
        "first_name":
        "Sample 1",
        "last_name":
        "Sample 2",
        "country":
        "Nigeria",
        "photo_url":
        "https://res.cloudinary.com/techcre8/image/upload/v1524063447/be9k2agdleomrvcksnrd.jpg",
        "social": {
            "link": "http://www.kola.com",
            "network": "website"
        },
        "phone_number":
        "08137449421",
        "contact_address":
        "32 Araromi Street, Lagos, Nigeria",
        **kwargs,
    }
    user = models.User.objects.create_user(**data)
    if plan:
        user.create_plan(
            plan=plan, duration=duration, last_renewed=last_renewed)
    return user


def get_personal_info(user, extra=None):
    data = extra or {}
    return {
        "first_name":
        user.first_name,
        "last_name":
        user.last_name,
        "country":
        "Nigeria",
        "photo_url":
        "https://res.cloudinary.com/techcre8/image/upload/v1524063447/be9k2agdleomrvcksnrd.jpg",
        "social_link": {
            "url": "http://www.kola.com",
            "name": "website"
        },
        "phone":
        "08137449421",
        "address":
        "32 Araromi Street, Lagos, Nigeria",
        "location":
        "32 Araromi Street, Lagos, Nigeria",
        "email":
        user.email,
        "social_link_url":
        "http://www.kola.com",
        'verified_email':
        False,
        **data,
    }


@pytest.mark.django_db(transaction=True)
def test_get_profile_info_for_free_plan():
    user = create_user_data(last_stop_point="mission-statement")
    client = TestClient(app)
    response = client.get(
        "/personal-info",
        headers={"Authorization": f"Token {user.get_new_token()}"})
    assert response.status_code == 200
    assert response.json() == get_personal_info(
        user,
        {
            "email_subscribed": False,
            "dob": None,
            "feature_notification": True,
            "last_stop_point": "mission-statement",
            "plan": {
                "name": "Free",
                "currency": "ngn",
                "duration": None,
                "expiry_date": None,
                "last_renewed": None,
                "resume_allowed": 1,
            },
        },
    )


@pytest.fixture
def make_request():
    def _make_request(method, *args, **kwargs):
        client = TestClient(app)
        options = {'GET': client.get, 'POST': client.post}
        return options[method](*args, **kwargs)

    return _make_request


@pytest.mark.django_db(transaction=True)
def test_get_profile_info_for_free_plan_2(make_request):
    user = create_user_data(last_stop_point="mission-statement")
    response = make_request(
        'GET',
        "/personal-info",
        headers={"Authorization": f"Token {user.get_new_token()}"})
    assert response.status_code == 200
    assert response.json() == get_personal_info(
        user,
        {
            "email_subscribed": False,
            "dob": None,
            "feature_notification": True,
            "last_stop_point": "mission-statement",
            "plan": {
                "name": "Free",
                "currency": "ngn",
                "duration": None,
                "expiry_date": None,
                "last_renewed": None,
                "resume_allowed": 1,
            },
        },
    )


@pytest.mark.django_db(transaction=True)
def test_user_on_basic_semi_annual_plan(create_plans):
    expiry_date = datetime(2018, 6, 1)
    create_plans()
    user = create_user_data(
        country="Ghana",
        plan="Pro",
        duration="annual",
        last_renewed=expiry_date)
    client = TestClient(app)
    response = client.get(
        "/personal-info",
        headers={"Authorization": f"Token {user.get_new_token()}"})
    assert response.status_code == 200
    assert response.json() == get_personal_info(
        user,
        {
            "country": "Ghana",
            "email_subscribed": False,
            "dob": None,
            "feature_notification": True,
            "last_stop_point": None,
            "plan": {
                "name": "Pro",
                "currency": "ghs",
                "duration": "annual",
                "last_renewed": "2018-06-01",
                "expiry_date": "2019-06-01",
                "resume_allowed": "unlimited",
            },
        },
    )


@pytest.mark.django_db(transaction=True)
def test_renew_or_upgrade_plan(create_plans):
    create_plans()
    user = create_user_data(country="Ghana")
    client = TestClient(app)
    response = client.post(
        "/upgrade-plan",
        json={
            "plan": "Pro",
            "currency": "usd",
            "duration": "annual",
            "date": "2018-06-01",
        },
        headers={"Authorization": f"Token {user.get_new_token()}"},
    )
    assert response.status_code == 201
    assert response.json() == {
        "user_id": user.pk,
        "plan": {
            "name": "Pro",
            "currency": "usd",
            "duration": "annual",
            "last_renewed": "2018-06-01",
            "expiry_date": "2019-06-01",
            "resume_allowed": "unlimited",
        },
    }


@pytest.mark.django_db(transaction=True)
def test_authenticate_token_with_pricing_information(create_plans):
    create_plans()
    user = create_user_data(last_stop_point="story-statement")
    client = TestClient(app)

    token = user.get_new_token()
    client = TestClient(app)
    response = client.post(
        "/api-token-verify?user_details=facebook",
        {
            "token": token,
            "last_stop_point": "story-statement",
            "shared_network": "facebook",
            "user_details": "true",
            "pricing": "client",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["token"] == token
    assert data["shared_networks"] == {
        "first_name": "Sample 1",
        "last_name": "Sample 2",
        "country": 'Nigeria',
        "email": "b@example.com",
        "phone_number": "08137449421",
        "dob": None,
        "feature_notification": True,
        "contact_address": "32 Araromi Street, Lagos, Nigeria",
        "networks": ["facebook"],
        "email_subscribed": False,
        "quickbooks_customer_details": {},
    }

    assert data["pricing"] == {
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
    }
