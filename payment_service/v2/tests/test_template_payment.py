from starlette.testclient import TestClient
from run import app
from unittest.mock import patch, call
import pytest
from payment_service import models
import time
from django.conf import settings
from cv_utils.tests import MockResponse


def json_call(method, url, **kwargs):
    client = TestClient(app)
    options = {"GET": client.get, "POST": client.post}
    return options[method](url, **kwargs)


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
def mock_auth(mock_auth_s):
    template = models.TemplatInfo.objects.create(
        name="Blue Salmon", thumbnail="http://google.com")
    discount_ref = models.ReferralDiscount.objects.create()

    return mock_auth_s(
        extra={
            "shared_networks": {
                "networks": [],
                "first_name": "Danny",
                "last_name": "Novca",
                "email": "danny@example.com",
                "phone_number": "+2347023322321",
                "country": "Nigeria",
                "contact_address": "lorem ipsum is hjere"
                "",
            }
        })


@pytest.fixture
def mock_auth_s(mocker):
    def _mock_auth(extra={}, status_code=200):
        return create_mock(mocker, status_code, get_token(extra=extra))

    return _mock_auth


def generate_link(path):
    return f"{settings.CURRENT_DOMAIN}/v2{path}"


token = "jeojwiojwioejwijowjo"


@pytest.mark.django_db(transaction=True)
def test_generate_payment_record_from_post_params(mock_auth):
    response = json_call(
        "POST",
        "/v2/create-payment",
        json={
            "template": "blue salmon",
            "level": "Intern"
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record = models.UserPayment.objects.first()

    assert response.status_code == 200
    link = generate_link(
        f"/paystack/verify-payment/{record.order}/?amount={int(3000*100)}")

    assert response.json() == {
        "data": {
            "amount": "3000.0",
            "order": record.order,
            "description": "Blue Salmon",
            "paid": False,
            "discount": 0,
            "base_country": "NG",
            "currency": "ngn",
            "thumbnail": "http://google.com",
            "user_details": {
                "key":
                settings.PAYSTACK_PUBLIC_KEY,
                **record.extra_data,
                "js_script":
                "https://js.paystack.co/v1/inline.js",
                "kind":
                "paystack",
                "redirect_url":
                link,
            },
        }
    }


@pytest.mark.django_db(transaction=True)
def test_generate_payment_record_from_post_params_when_template_doesnt_exist(
        mock_auth):
    response = json_call(
        "POST",
        "/v2/create-payment",
        json={
            "template": "green panther",
            "level": "Intern",
            "create": True
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    record = models.UserPayment.objects.first()

    assert response.status_code == 200
    link = generate_link(
        f"/paystack/verify-payment/{record.order}/?amount={int(3000*100)}")

    assert response.json() == {
        "data": {
            "amount": "3000.0",
            "order": record.order,
            "description": "green panther",
            "paid": False,
            "discount": 0,
            "base_country": "NG",
            "currency": "ngn",
            "thumbnail": "http://google.com",
            "user_details": {
                "key":
                settings.PAYSTACK_PUBLIC_KEY,
                **record.extra_data,
                "js_script":
                "https://js.paystack.co/v1/inline.js",
                "kind":
                "paystack",
                "redirect_url":
                link,
            },
        }
    }


@pytest.mark.django_db(transaction=True)
def test_when_invalid_details_is_passed(mock_auth):
    response = json_call(
        "POST",
        "v2/create-payment",
        json={
            "template": "Template 2",
            "level": "Intern"
        },
        headers={"Authorization": f"Bearer {mock_auth['token']}"},
    )
    assert response.status_code == 400
    assert response.json() == {
        "errors": {
            "template": ["Template does not exist"]
        }
    }
