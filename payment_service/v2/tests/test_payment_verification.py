import pytest
from payment_service import models
from django.conf import settings

p_response = lambda amount: (True, 'verification succeess', {
    "amount": amount * 100,
    "currency": "NGN",
    "transaction_date": "2016-10-01T11:03:09.000Z",
    "status": "success",
    "reference": "DG4uishudoq90LD",
    "domain": "test",
    "metadata": 0,
    "gateway_response": "Successful",
    "message": None,
    "channel": "card",
    "ip_address": "41.1.25.1",
    "log": {
        "time_spent":
        9,
        "attempts":
        1,
        "authentication":
        None,
        "errors":
        0,
        "success":
        True,
        "mobile":
        False,
        "input": [],
        "channel":
        None,
        "history": [{
            "type":
            "input",
            "message":
            "Filled these fields: card number, card expiry, card cvv",
            "time":
            7
        }, {
            "type": "action",
            "message": "Attempted to pay",
            "time": 7
        }, {
            "type": "success",
            "message": "Successfully paid",
            "time": 8
        }, {
            "type": "close",
            "message": "Page closed",
            "time": 9
        }]
    },
    "fees": None,
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


@pytest.mark.django_db(transaction=True)
def test_paystack_verify_hook(mocker, monkeypatch, paystack_api,
                              quickbooks_api, mock_mail, mock_post, json_call):
    mock_instance = paystack_api(p_response(2000))
    mock_quickbooks = quickbooks_api({
        'create_customer': {
            "id": "23",
            "name": "Danny Novaka"
        },
        'create_sales_receipt': "2322"
    })

    template = models.TemplatInfo.objects.create(
        name="Blue Salmon", price=2000, thumbnail="http://google.com")
    models.ReferralDiscount.objects.create()

    models.UserPayment.objects.create(
        order="ADESFG123453",
        template=template,
        user=22,
        amount=0,
        extra_data={
            "networks": [],
            "first_name": "Danny",
            "last_name": "Novca",
            "email": "danny@example.com",
            "phone_number": "+2347023322321",
            "country": "NG",
            "contact_address": "lorem ipsum is hjere"
            "",
        },
    )
    assert models.UserPayment.objects.count() == 1
    response = json_call(
        "GET",
        "/v2/paystack/verify-payment/ADESFG123453/",
        params={
            "amount": 2000 * 100,
            "trxref": "freeze me",
        },
    )
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_instance.verify_payment.assert_called_once_with(
        "freeze me", amount=200000, amount_only=True)
    record = models.UserPayment.objects.first()
    assert record.made_payment == True
    extra_data = record.extra_data
    assert extra_data["quickbooks_customer_details"] == {
        "id": "23",
        "name": "Danny Novaka",
    }

    assert extra_data["quickbooks_receipt_id"] == "2322"
    mock_quickbooks.create_customer.assert_called_once_with(
        **{
            "email":
            record.extra_data["email"],
            "full_name":
            f"{record.extra_data['first_name']} {record.extra_data['last_name']}",
            "phone_number":
            record.extra_data["phone_number"],
            "location": {
                "country":
                "NG",  # ensure country comes in full version e.g Nigeria
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
    mock_post.assert_called_once_with(
        settings.AUTH_ENDPOINT + "/save-custom-data",
        json={
            "user_id": record.user,
            "data": {
                "quickbooks_customer_details": {
                    "id": "23",
                    "name": "Danny Novaka"
                }
            },
        },
    )
    mock_mail.assert_called_once_with("first_resume_download",
                                      {"first_name": "Danny"},
                                      [record.extra_data["email"]])


@pytest.mark.django_db
def test_ravepay_verify_hook(mocker, monkeypatch, ravepay_api, mock_mail,
                             mock_post, quickbooks_api, json_call):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "MY-SECRET-KEY")
    mock_instance = ravepay_api((True, "verification successful"))
    mock_quickbooks = quickbooks_api({
        'create_customer': {
            "id": "23",
            "name": "Danny Novaka"
        },
        'create_sales_receipt': "2322"
    })

    template = models.TemplatInfo.objects.create(
        name="Blue Salmon", price=2000, thumbnail="http://google.com")
    discount_ref = models.ReferralDiscount.objects.create()

    models.UserPayment.objects.create(
        order="ADESFG123453",
        template=template,
        user=22,
        amount=0,
        extra_data={
            "networks": [],
            "first_name": "Danny",
            "last_name": "Novca",
            "email": "danny@example.com",
            "phone_number": "+2347023322321",
            "country": "NG",
            "contact_address": "lorem ipsum is hjere"
            "",
        },
    )
    assert models.UserPayment.objects.count() == 1
    response = json_call(
        "GET",
        "/v2/ravepay/verify-payment/ADESFG123453/",
        params={
            "amount": 2000,
            "code": "freeze me"
        },
    )
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_instance.verify_payment.assert_called_once_with("freeze me", 2000)
    record = models.UserPayment.objects.first()
    assert record.made_payment


@pytest.mark.django_db
def test_successful_payment_of_plan(mocker, paystack_api, quickbooks_api,
                                    mock_post, mock_mail, json_call,
                                    create_plan_instance, mock_assertions):
    mock_instance = paystack_api(p_response(10800))

    mock_quickbooks = quickbooks_api({
        'create_customer': {
            "id": "23",
            "name": "Danny Novaka"
        },
        'create_sales_receipt': "2322"
    })
    create_plan_instance("ADESFG123453", 10800)
    models.ReferralDiscount.objects.create()

    assert models.PlanPayment.objects.count() == 1
    response = json_call(
        'GET',
        "/v2/paystack/verify-payment/ADESFG123453/",
        params={
            "amount": 10800 * 100,
            "plan": "Pro",
            "trxref": "freeze me"
        },
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_instance.verify_payment.assert_called_once_with(
        "freeze me", amount=1080000, amount_only=True)
    record = models.PlanPayment.objects.first()
    assert record.made_payment
    extra_data = record.extra_data
    assert extra_data["quickbooks_customer_details"] == {
        "id": "23",
        "name": "Danny Novaka",
    }

    assert extra_data["quickbooks_receipt_id"] == "2322"
    mock_assertions(record, mock_quickbooks, mock_post, mock_mail)


@pytest.mark.django_db
def test_successful_payment_of_agent_plan(
        mocker, paystack_api, quickbooks_api, mock_post, json_call,
        create_plan_instance, mock_assertions):
    paystack_result = p_response(10800)
    mock_client_api = mocker.patch('cv_utils.client.update_agent_plan_details')
    mock_client_api.return_value = {
        "pk": 101,
        "first_name": "Danny",
        "last_name": "Novca",
        "email": "danny@example.com",
        "phone": "+2347023322321",
        "country": "Nigeria",
        "company_name": "Eleja Systems"
    }

    mock_instance = paystack_api(paystack_result, mock_data=paystack_result[2])
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
    mock_instance.subscription_api.get_plan.return_value = (
        True,
        "Plan Received",
        {
            "currency": "NGN",
            "id": 28,
        },
    )
    mock_quickbooks = quickbooks_api({
        'create_customer': {
            "id": "23",
            "name": "Danny Novaka"
        },
        'create_sales_receipt': "2322"
    })
    create_plan_instance(
        "ADESFG123453",
        10800,
        kind="agent",
        plan_code="PlanProDollarMonthly",
        company_name="Eleja Systems")
    models.ReferralDiscount.objects.create()

    assert models.PlanPayment.objects.count() == 1
    response = json_call(
        'GET',
        "/v2/paystack/verify-payment/ADESFG123453/",
        params={
            "amount": 10800 * 100,
            "plan": "Pro",
            "kind": "agent",
            "trxref": "freeze me"
        },
    )

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_instance.verify_payment.assert_called_once_with(
        "freeze me", amount=1080000, amount_only=False)
    record = models.PlanPayment.objects.first()
    assert record.made_payment
    extra_data = record.extra_data
    assert extra_data["quickbooks_customer_details"] == {
        "id": "23",
        "name": "Danny Novaka",
    }
    assert extra_data['paystack_details'] == {
        'authorization': paystack_result[2]['authorization'],
        'customer': paystack_result[2]['customer'],
        'plan': paystack_result[2]['plan'],
        'subscription_code': "SUB_6phdx225bavuwtb",
        'email_token': "ore84lyuwcv2esu",
        'plan_id': 28
    }

    assert extra_data["quickbooks_receipt_id"] == "2322"
    mock_assertions(record, mock_quickbooks, kind="agent")
    assert mock_post.call_count == 1


def test_when_subscription_changes():
    pass
