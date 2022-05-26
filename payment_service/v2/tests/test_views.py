import pytest
from payment_service.models import PlanPayment


@pytest.mark.django_db(transaction=True)
def test_agent_payment_details(json_call, mocker, agent_auth):
    token = "12345232"
    payment = PlanPayment.objects.create(
        order="ADESFG123453",
        user=101,
        amount=2000,
        plan="Pro",
        kind="agent",
        duration="annually",
        made_payment=True,
        extra_data={'country': "Nigeria"})
    agent_auth("requests.post")
    result = json_call(
        "POST",
        "/payment-details",
        json={"kind": 'agent'},
        headers={'Authorization': "Bearer {}".format(token)})
    assert result.json() == {
        "payment_details": [{
            "date":
            payment.modified.strftime("%B %d, %Y"),
            "amount":
            2000.0,
            "base_country":
            "NG",
            "currency":
            "ngn",
            "payment_method":
            "Paystack",
            "receipt":
            f"https://testserver/download-receipt/plan/{payment.order}",
            "made_payment":
            True
        }]
    }
