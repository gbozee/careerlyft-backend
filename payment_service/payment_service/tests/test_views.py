import hashlib
import hmac
import json
from unittest import mock

from django.conf import settings
from django.shortcuts import reverse
from django.test import TestCase

from paystack.utils import generate_digest

from .. import models


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data


class BaseTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.template = models.TemplatInfo.objects.create(
            name="Blue Salmon", thumbnail="http://google.com")
        self.discount_ref = models.ReferralDiscount.objects.create()
        self.patcher = mock.patch("payment_service.utils.requests.post")
        self.mock_auth = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def create_payment_record(self, order):
        return models.UserPayment.objects.create(
            order=order,
            template=self.template,
            user=22,
            extra_data={"level": "Intern"},
            amount=0,
            made_payment=True,
        )

    def json_get(self, url, data=None, **kwargs):
        return self.client.get(
            url, data, content_type="application/json", **kwargs)

    def get_token(self, extra={}):
        self.mock_auth.return_value = MockResponse({
            "user_id":
            22,
            "token":
            "jeojwiojwioejwijowjo",
            **extra
        })
        return "jeojwiojwioejwijowjo"


class PaymentViewTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        # models.ReferralDiscount.objects.create()
        self.payment = models.UserPayment.objects.create(
            order="ADESFG123453", template=self.template, user=22, amount=0)

    def assert_result(self, response, amount, currency, paid=False, bc="NG"):
        only_template = models.TemplatInfo.objects.first()
        self.assertEqual(response.status_code, 200)
        result = {
            "currency": currency.lower(),
            # "data": {},
            "id": only_template.pk,
            "name": "Blue Salmon",
            "price": amount,
            "image": "http://google.com",
            "base_country": bc,
        }
        if paid:
            result = {**result, "paid": False}
        self.assertCountEqual(response.json()["data"], [result])

    def test_templates_rates_based_on_countries_without_autorization(self):
        response = self.json_get("/templates")
        self.assert_result(response, "10", "USD")
        response = self.json_get("/templates?country=Ghana")
        self.assert_result(response, "50", "GHS", bc="GH")
        response = self.json_get("/templates?country=Nigeria")
        self.assert_result(response, "2000", "NGN")
        response = self.json_get("/templates?country=Italy")
        self.assert_result(response, "10", "EUR")
        response = self.json_get("/templates?country=United Kingdom")
        self.assert_result(response, "10", "GBP")
        response = self.json_get("/templates?country=South Africa")
        self.assert_result(response, "300", "ZAR", bc="ZA")
        response = self.json_get("/templates?country=Kenya")
        self.assert_result(response, "800", "KES", bc="KE")

    def make_and_assert_call(self, country, rate, currency, bc="NG"):
        token = self.get_token({"shared_networks": {"country": country}})
        response = self.json_get(
            "/templates", HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assert_result(response, rate, currency, True, bc=bc)

    def test_templates_rates_based_on_countries_with_authorization(self):
        self.make_and_assert_call("Nigeria", "2000", "NGN")
        self.make_and_assert_call("Argentina", "10", "USD")
        self.make_and_assert_call("United States", "10", "USD")
        self.make_and_assert_call("Ghana", "50", "GHS", "GH")
        self.make_and_assert_call("Italy", "10", "EUR")
        self.make_and_assert_call("United Kingdom", "10", "GBP")
        self.make_and_assert_call("South Africa", "300", "ZAR", "ZA")
        self.make_and_assert_call("Kenya", "800", "KES", "KE")

    def test_templates_consist_of_purchased_version(self):
        token = self.get_token({"shared_networks": {"country": "Nigeria"}})
        response = self.json_get(
            "/templates", HTTP_AUTHORIZATION="Bearer {}".format(token))
        only_template = models.TemplatInfo.objects.first()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["data"],
            [{
                "id": only_template.pk,
                "paid": False,
                "name": "Blue Salmon",
                "price": "2000",
                "image": "http://google.com",
                "currency": "ngn",
                "base_country": "NG",
            }],
        )
        self.assertEqual(response.json()["rates"],
                         models.ReferralDiscount.OPTIONS)
        self.payment.made_payment = True
        self.payment.save()
        response = self.json_get(
            "/templates", HTTP_AUTHORIZATION="Bearer {}".format(token))
        only_template = models.TemplatInfo.objects.first()
        self.assertEqual(
            response.json()["data"],
            [{
                "id": only_template.pk,
                "paid": True,
                "name": "Blue Salmon",
                "price": "2000",
                "image": "http://google.com",
                "currency": "ngn",
                "base_country": "NG",
            }],
        )

    def test_generate_payment_instance(self):
        token = self.get_token({"shared_networks": {"country": "Nigeria"}})

        response = self.json_get(
            "/payment-info", HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "amount": "2000",
                "order": "ADESFG123453",
                "description": "Blue Salmon",
                "base_country": "NG",
                "currency": "ngn",
                "discount": 0,
                "paid": False,
                "thumbnail": "http://google.com",
            },
        )

    def test_get_payment_details_for_paid_receipts(self):
        self.payment.made_payment = True
        self.payment.amount = 2000
        self.payment.save()
        token = self.get_token({"shared_networks": {}})

        response = self.json_get(
            "/payment-details", HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "payment_details": [{
                    "date":
                    self.payment.modified.strftime("%B %d, %Y"),
                    "amount":
                    2000.0,
                    "base_country":
                    "NG",
                    "made_payment":
                    True,
                    "currency":
                    "usd",
                    "payment_method":
                    "Paystack",
                    "receipt":
                    f"https://testserver/download-receipt/template/{self.payment.order}",
                }]
            },
        )

    def test_get_payment_details_for_paid_plans(self):
        plan_payment = models.PlanPayment.objects.create(
            order="ADESFG123453", user=22, amount=2000, made_payment=True)
        token = self.get_token({"shared_networks": {}})

        response = self.json_get(
            "/payment-details?kind=plan",
            HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "payment_details": [{
                    "date":
                    plan_payment.modified.strftime("%B %d, %Y"),
                    "amount":
                    2000.0,
                    "base_country":
                    "NG",
                    "made_payment":
                    True,
                    "currency":
                    "usd",
                    "payment_method":
                    "Paystack",
                    "receipt":
                    f"https://testserver/download-receipt/plan/{plan_payment.order}",
                }]
            },
        )

    def test_get_payment_details_for_all(self):
        plan_payment = models.PlanPayment.objects.create(
            order="ADESFG123422", user=22, amount=2000, made_payment=True)
        self.payment.made_payment = True
        self.payment.amount = 2000
        self.payment.save()
        token = self.get_token({"shared_networks": {}})

        response = self.json_get(
            "/payment-details", HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "payment_details": [
                    {
                        "date":
                        plan_payment.modified.strftime("%B %d, %Y"),
                        "amount":
                        2000.0,
                        "base_country":
                        "NG",
                        "made_payment":
                        True,
                        "currency":
                        "usd",
                        "payment_method":
                        "Paystack",
                        "receipt":
                        f"https://testserver/download-receipt/plan/{plan_payment.order}",
                    },
                    {
                        "date":
                        self.payment.modified.strftime("%B %d, %Y"),
                        "amount":
                        2000.0,
                        "base_country":
                        "NG",
                        "made_payment":
                        True,
                        "currency":
                        "usd",
                        "payment_method":
                        "Paystack",
                        "receipt":
                        f"https://testserver/download-receipt/template/{self.payment.order}",
                    },
                ]
            },
        )


class PaystackTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.env = mock.patch.dict("os.environ",
                                   {"PAYSTACK_SECRET_KEY": "MY-SECRET-KEY"})
        # set secret key for this test
        # self.env.set()
        self.transaction_event_payload = """{  
   "event":"charge.success",
   "data":{  
      "id":302961,
      "domain":"live",
      "status":"success",
      "reference":"qTPrJoy9Bx",
      "amount":10000,
      "message":null,
      "gateway_response":"Approved by Financial Institution",
      "paid_at":"2016-09-30T21:10:19.000Z",
      "created_at":"2016-09-30T21:09:56.000Z",
      "channel":"card",
      "currency":"NGN",
      "ip_address":"41.242.49.37",
      "metadata":0,
      "log":{  
         "time_spent":16,
         "attempts":1,
         "authentication":"pin",
         "errors":0,
         "success":false,
         "mobile":false,
         "input":[  

         ],
         "channel":null,
         "history":[  
            {  
               "type":"input",
               "message":"Filled these fields: card number, card expiry, card cvv",
               "time":15
            },
            {  
               "type":"action",
               "message":"Attempted to pay",
               "time":15
            },
            {  
               "type":"auth",
               "message":"Authentication Required: pin",
               "time":16
            }
         ]
      },
      "fees":null,
      "customer":{  
         "id":68324,
         "first_name":"BoJack",
         "last_name":"Horseman",
         "email":"bojack@horseman.com",
         "customer_code":"CUS_qo38as2hpsgk2r0",
         "phone":null,
         "metadata":null,
         "risk_action":"default"
      },
      "authorization":{  
         "authorization_code":"AUTH_f5rnfq9p",
         "bin":"539999",
         "last4":"8877",
         "exp_month":"08",
         "exp_year":"2020",
         "card_type":"mastercard DEBIT",
         "bank":"Guaranty Trust Bank",
         "country_code":"NG",
         "brand":"mastercard"
      },
      "plan":{}
   }
}"""

    def get_token(self, extra={}):
        self.mock_auth.return_value = MockResponse({
            "user_id":
            22,
            "token":
            "jeojwiojwioejwijowjo",
            **extra
        })
        return "jeojwiojwioejwijowjo"

    def test_create_free_template(self):
        response = self.client.post(
            "/create-free-template",
            json.dumps({
                "user_id": 32,
                "personal-info": {}
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record = models.UserPayment.objects.first()
        self.assertTrue(record.made_payment)
        self.assertEqual(record.amount, 0)

    # def test_webhook(self):
    #     with self.env:  # using test env context
    #         data = json.loads(self.transaction_event_payload)
    #         signedhash = generate_digest(
    #             self.transaction_event_payload.encode("utf-8"))
    #         header_data = {"HTTP_X_PAYSTACK_SIGNATURE": signedhash}
    #         response = self.client.post(
    #             "/paystack/webhook/",
    #             self.transaction_event_payload,
    #             content_type="application/json",
    #             **header_data,
    #         )
    #         self.assertEqual(response.status_code, 200)

    def test_webhook_ravepay(self):
        pass

    def get_mock(self, mock_call, args):
        mock_instance = mock_call.return_value
        mock_instance.verify_payment.return_value = args
        return mock_instance
