from datetime import datetime
import pytest
from payment_service import models
from django.conf import settings


def generate_link(path, domain=settings.CURRENT_DOMAIN):
    return f"{domain}/v2{path}"


token = "jeojwiojwioejwijowjo"


@pytest.mark.django_db(transaction=True)
def test_create_plan_payment(mock_auth, plan_call, build_response):
    models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    response = plan_call({"plan": "Pro", "duration": "annual"}, token)
    assert response.status_code == 200
    n_amount = int(9600 * 100)
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == build_response(9600.0, link, token)


@pytest.mark.django_db(transaction=True)
def test_create_plan_payment_with_currency_passed(mock_auth, plan_call, build_response):
    models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    response = plan_call(
        {"plan": "Pro", "duration": "annual", "currency": "ghs"}, token
    )
    assert response.status_code == 200
    link = generate_link(
        f"/ravepay/verify-payment/ADESFG123453/?amount={288.0}&plan=Pro"
    )
    assert response.json() == build_response(288.0, link, token, "GH", kind="ravepay")


@pytest.mark.django_db(transaction=True)
def test_create_plan_payment_ravepay(mock_auth_ghana, plan_call, build_response):
    models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    response = plan_call({"plan": "Pro", "duration": "annual"}, token)
    assert response.status_code == 200
    amount = 288
    n_amount = float(amount)
    link = generate_link(
        f"/ravepay/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == build_response(
        amount, link, token, "GH", kind="ravepay", default_country=False
    )


@pytest.mark.django_db(transaction=True)
def test_create_payment_with_coupon_not_expired(mock_auth, plan_call, build_response):
    models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    models.Coupon.objects.create(
        code="EVENT101", limit=100, discount=5, expiry_date=datetime(2019, 10, 10)
    )
    response = plan_call(
        {"plan": "Pro", "duration": "annual", "coupon": "EVENT101"}, token
    )
    assert response.status_code == 200
    n_amount = int(9120 * 100)
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == build_response(9120, link, token, discount=480)

    # try making another call with the coupon should still return the discount
    response = plan_call(
        {"plan": "Pro", "duration": "annual", "coupon": "EVENT101"}, token
    )
    assert response.status_code == 200
    n_amount = int(9120 * 100)
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == build_response(9120, link, token, discount=480)


@pytest.mark.django_db(transaction=True)
def test_create_payment_with_coupon_exhausted(mock_auth, plan_call, build_response):
    plan_payment = models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    models.Coupon.objects.create(
        code="EVENT101", limit=0, discount=5, expiry_date=datetime(2019, 10, 10)
    )
    response = plan_call(
        {"plan": "Pro", "duration": "annual", "coupon": "EVENT101"}, token
        # {"plan": "Pro", "duration": "annual", "coupon": "","currency":"usd"}, token
    )
    assert response.status_code == 200
    plan_payment = models.PlanPayment.objects.get(order=plan_payment.order)
    tk = plan_payment.extra_data["token"]
    assert tk == token
    n_amount = int(9600 * 100)
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == {
        **build_response(9600, link, token, plan=True),
        "coupon_used": False,
    }


@pytest.mark.django_db(transaction=True)
def test_create_payment_with_coupon_expired(mock_auth, plan_call, build_response):
    models.PlanPayment.objects.create(order="ADESFG123453", user=101)
    models.Coupon.objects.create(
        code="EVENT101", limit=100, discount=5, expiry_date=datetime(2018, 10, 10)
    )
    response = plan_call(
        {"plan": "Pro", "duration": "annual", "coupon": "EVENT101"}, token
    )
    assert response.status_code == 200
    n_amount = int(9600 * 100)
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro"
    )
    assert response.json() == {
        **build_response(9600.0, link, token),
        "coupon_used": False,
    }


@pytest.mark.django_db(transaction=True)
def test_create_plan_payment_for_agent(mocker, plan_call, agent_auth, build_response):
    mock_random = mocker.patch("payment_service.models.base.get_random_string")
    mock_random.return_value = "ADESFG123453"
    agent_auth(token)
    response = plan_call(
        {"plan": "Pro", "duration": "monthly", "kind": "agent", "currency": "usd"},
        token,
    )
    n_amount = 9900
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro&kind=agent"
    )
    assert response.json() == build_response(
        99,
        link,
        token,
        override_currency="usd",
        duration="monthly",
        company_name="Eleja Systems",
        plan_code="PlanProDollarMonthly",
        user_kind="agent",
    )


@pytest.mark.django_db(transaction=True)
def test_create_plan_payment_with_different_callback_endpoint(
    mocker, plan_call, agent_auth, build_response
):
    mock_random = mocker.patch("payment_service.models.base.get_random_string")
    mock_random.return_value = "ADESFG123453"
    agent_auth(token)
    response = plan_call(
        {
            "plan": "Pro",
            "duration": "monthly",
            "kind": "agent",
            "currency": "usd",
            "redirect_url": "http://www.google.com",
        },
        token,
    )
    n_amount = 9900
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={n_amount}&plan=Pro&kind=agent",
        "http://www.google.com",
    )
    assert response.json() == build_response(
        99,
        link,
        token,
        override_currency="usd",
        duration="monthly",
        company_name="Eleja Systems",
        plan_code="PlanProDollarMonthly",
        user_kind="agent",
    )


@pytest.mark.django_db(transaction=True)
def test_creating_plan_payment_with_coupon_doesnot_use_plan(
    plan_call, mocker, agent_auth, build_response
):
    mock_random = mocker.patch("payment_service.models.base.get_random_string")
    mock_random.return_value = "ADESFG123453"
    agent_auth(token)
    models.Coupon.objects.create(
        code="EVENT101", limit=100, discount=5, expiry_date=datetime(2019, 10, 10)
    )
    response = plan_call(
        {
            "plan": "Pro",
            "duration": "monthly",
            "coupon": "EVENT101",
            "kind": "agent",
            "currency": "usd",
            "redirect_url": "http://www.google.com",
        },
        token,
    )

    assert response.status_code == 200
    n_amount = 94.05
    link = generate_link(
        f"/paystack/verify-payment/ADESFG123453/?amount={int(n_amount*100-1)}&plan=Pro&kind=agent",
        "http://www.google.com",
    )
    assert response.json() == build_response(
        n_amount,
        link,
        token,
        override_currency="usd",
        duration="monthly",
        company_name="Eleja Systems",
        user_kind="agent",
        discount=4.95
    )
