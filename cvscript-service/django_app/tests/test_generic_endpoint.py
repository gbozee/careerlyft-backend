from django.test import TestCase
from unittest import mock
import json
from django.conf import settings
from django_app.models import CompanyAndSchool


class GenericEndpointTestCase(TestCase):

    def setUp(self):
        CompanyAndSchool.objects.create(
            name='English High School', kind=CompanyAndSchool.SCHOOL)

    def test_returns_response(self):
        response = self.client.get("/schools", {'q': 'eng'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': ['English High School']})

    def test_fails_when_query_param_less_than_three(self):
        response = self.client.get("/schools", {'q': 'en'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'message':'3 or more characters are required'})

    def test_throw_404_error(self):
        response = self.client.get("/ygfewgfuwe", {'q': 'en3'})
        self.assertEqual(response.status_code, 404)
        