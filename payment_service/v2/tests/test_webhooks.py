import pytest
import json
from payment_service import models
from paystack.utils import generate_digest
from cv_utils.tests import MockResponse
from django.conf import settings

url = "/paystack/webhook"
body = {
    "event": "charge.success",
    "data": {
        "id": 302961,
        "domain": "live",
        "status": "success",
        "reference": "ADESFG123453",
        "amount": 10000,
        "message": None,
        "paid_at": "2016-09-30T21:10:19.000Z",
        "created_at": "2016-09-30T21:09:56.000Z",
        "channel": "card",
        "currency": "NGN",
        "ip_address": "41.242.49.37",
        "metadata": 0,
        "fees": None,
        "customer": {
            "id": 68324,
            "first_name": "BoJack",
            "last_name": "Horseman",
            "email": "bojack@horseman.com",
            "customer_code": "CUS_qo38as2hpsgk2r0",
            "phone": None,
            "metadata": None,
            "risk_action": "default"
        },
        "authorization": {
            "authorization_code": "AUTH_f5rnfq9p",
            "bin": "539999",
            "last4": "8877",
            "exp_month": "08",
            "exp_year": "2020",
            "card_type": "mastercard DEBIT",
            "bank": "Guaranty Trust Bank",
            "country_code": "NG",
            "brand": "mastercard"
        },
        "plan_object": {
            "id": 6743,
            "name": "Starter+ Monthly",
            "plan_code": "PLN_tq8ur7pqz80fbpi",
            "description": "This is to test listing plans, etc etc",
            "amount": 200000,
            "interval": "hourly",
            "send_invoices": True,
            "send_sms": True,
            "currency": "NGN"
        }
    }
}


@pytest.fixture
def web_hook_setup(create_plan_instance, mock_assertions, json_call,
                   quickbooks_api, mock_post, mocker, monkeypatch,
                   paystack_api):
    def _webhook_setup(made_payment=False, create_agent=True, **kwargs):
        mock_client_api = mocker.patch(
            'cv_utils.client.update_agent_plan_details')
        mock_client_api.return_value = {
            "pk": 101,
            "first_name": "Danny",
            "last_name": "Novca",
            "email": "danny@example.com",
            "phone": "+2347023322321",
            "country": "Nigeria",
            "company_name": "Eleja Systems"
        }
        mock_agent_quickbooks = mocker.patch(
            'cv_utils.client.update_quickbooks_info_for_agent')
        mock_instance = paystack_api(None)
        mock_post.side_effect = []
        mock_instance.subscription_api.get_all_subscriptions.return_value = (
            True, "Subscriptions retrieved", [{
                "subscription_code":
                "SUB_6phdx225bavuwtb",
                "email_token":
                "ore84lyuwcv2esu",
                "easy_cron_id":
                "275226",
                "cron_expression":
                "0 0 * * 6",
                "next_payment_date":
                "2016-10-15T00:00:00.000Z",
                "open_invoice":
                "INV_qc875pkxpxuyodf",
                "id":
                4192,
            }])
        mock_quickbooks = quickbooks_api({
            'create_customer': {
                "id": "23",
                "name": "Danny Novaka"
            },
            'create_sales_receipt': "2322"
        })
        models.ReferralDiscount.objects.create()
        if create_agent:
            create_plan_instance(
                "ADESFG123453",
                10800,
                made_payment=made_payment,
                kind="agent",
                plan_code="PlanProDollarMonthly",
                company_name="Eleja Systems",
                **kwargs)
        signedhash = generate_digest(json.dumps(body).encode('utf-8'))

        response = json_call(
            'POST',
            "/paystack/webhook/",
            json=body,
            headers={
                'X_PAYSTACK_SIGNATURE': signedhash,
                "Content-Type": "application/json",
            })
        assert response.status_code == 200
        record = models.PlanPayment.objects.first()
        return response, mock_assertions, mock_quickbooks, mock_post, record, mock_agent_quickbooks

    return _webhook_setup


custoemr = body['data']['customer']
auth_data = body['data']['authorization']
assertion_response = {
    'authorization': auth_data['authorization_code'],
    'auth_data': auth_data,
    'customer': {
        'id': custoemr['id'],
        'email': custoemr['email'],
        'customer_code': custoemr['customer_code']
    },
    'plan': body['data']['plan_object']['plan_code'],
    'subscription_code': "SUB_6phdx225bavuwtb",
    'email_token': "ore84lyuwcv2esu",
    'plan_id': 6743
}


@pytest.mark.django_db(transaction=True)
def test_update_unpaid_payment_with_webhook(web_hook_setup, ):
    response, mock_assertions, mock_quickbooks, mock_post, record, mock_agent_quickbooks = web_hook_setup(
    )
    assert record.made_payment
    extra_data = record.extra_data
    assert extra_data["quickbooks_customer_details"] == {
        "id": "23",
        "name": "Danny Novaka",
    }
    assert extra_data['paystack_details'] == assertion_response

    assert extra_data["quickbooks_receipt_id"] == "2322"

    mock_assertions(
        record,
        mock_quickbooks,
        kind="agent",
    )
    assert mock_post.call_count == 0


@pytest.mark.django_db(transaction=True)
def test_updated_paid_payment_with_webhook(web_hook_setup, ):
    response, _, mock_quickbooks, mock_post, record, mock_agent_quickbooks = web_hook_setup(
        True, paystack_details=assertion_response)
    assert mock_post.call_count == 0
    assert record.made_payment
    extra_data = record.extra_data
    assert extra_data['paystack_details'] == assertion_response
    assert not mock_quickbooks.called


@pytest.mark.django_db(transaction=True)
def test_create_new_payment_from_webhook(web_hook_setup):
    response, mock_assertions, mock_quickbooks, mock_post, record, mock_agent_quickbooks = web_hook_setup(
        create_agent=False)
    assert record.made_payment
    extra_data = record.extra_data
    assert extra_data["quickbooks_customer_details"] == {
        "id": "23",
        "name": "Danny Novaka",
    }
    assert extra_data['paystack_details'] == assertion_response

    assert extra_data["quickbooks_receipt_id"] == "2322"
    assert record.order == body['data']['reference']
    assert record.duration == 'monthly'
    # assert record.currency == 'ngn'
    assert record.plan == 'Starter+'
    mock_assertions(
        record,
        mock_quickbooks,
        kind="agent",
    )
    assert mock_post.call_count == 0
    mock_agent_quickbooks.assert_called_once_with(
        settings.AUTH_ENDPOINT + "/v2/graphql", {
            "quickbooks_customer_details":
            extra_data['quickbooks_customer_details']
        }, "danny@example.com")
