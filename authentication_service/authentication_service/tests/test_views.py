from unittest import mock
import json
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import reverse
from rest_framework import status
from rest_framework.test import APITestCase as TestCase
from rest_framework_jwt import utils, views

from authentication_service.models import User


class SignupTestCase(TestCase):
    def setUp(self):
        self.data = {
            "contact_address":
            "Lagos Street, Abuja, Nigeria",
            "country":
            "Nigeria",
            "email":
            "jamie@example.com",
            "first_name":
            "Jamie",
            "last_name":
            "Logan",
            "phone_number":
            "23407035209988",
            "photo_url":
            "https://res.cloudinary.com/techcre8/image/upload/v1520758110/sg12hwp6fjkkdx11geka.jpg",
            "social_link":
            "www.google.com",
            "social_network":
            "website",
            "password":
            "password",
        }
        self.patcher = mock.patch("authentication_service.services.send_mail")
        self.send_mail = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def verify_token(self, token):
        response = self.client.post(
            "/api-token-verify", {"token": token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def assert_user_fields(self, user, with_password=True):
        self.assertEqual(user.country, self.data["country"])
        self.assertEqual(user.first_name, self.data["first_name"])
        self.assertEqual(user.last_name, self.data["last_name"])
        self.assertEqual(user.phone_number, self.data["phone_number"])
        self.assertEqual(user.contact_address, self.data["contact_address"])
        self.assertEqual(
            user.social,
            {
                "link": self.data["social_link"],
                "network": self.data["social_network"]
            },
        )
        if with_password:
            self.assertTrue(user.check_password(self.data["password"]))

    def assert_verification_email_sent(self, response, user, callback_url):
        data = response.json()
        self.assertEqual(data["user_id"], user.pk)
        self.assertIsNotNone(data["token"])
        self.verify_token(data["token"])
        request = response.wsgi_request
        link = (
            reverse("verify_email_link") +
            f"?email={user.email}&token={data['token']}&callback_url={callback_url}"
        )
        self.send_mail.assert_any_call(
            "verify_email",
            {
                "first_name": user.first_name,
                "link": request.build_absolute_uri(link)
            },
            user.email,
        )
        return link

    @mock.patch("authentication_service.utils.requests.post")
    def test_signup(self, mock_post):
        response = self.client.post(
            "/signup",
            {
                **self.data,
                "callback": "http://google.com",
                "about_details": {
                    "hello": "world",
                    "biola": "is_here"
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # call1 = mock.call(
        #     f"{settings.CV_SERVICE_URL}/cv-profile",
        #     json={"hello": "world", "biola": "is_here"},
        #     headers={"Authorization": f"Bearer {response.json()['token']}"},
        # )
        user = User.objects.first()
        call2 = mock.call(
            "http://localhost:8000/cv-profile-server",
            json={
                "data": {
                    "hello": "world",
                    "biola": "is_here"
                },
                "user_id": user.pk,
                "personal-info": {
                    "first_name":
                    "Jamie",
                    "last_name":
                    "Logan",
                    "country":
                    "Nigeria",
                    "photo_url":
                    "https://res.cloudinary.com/techcre8/image/upload/v1520758110/sg12hwp6fjkkdx11geka.jpg",
                    "email":
                    "jamie@example.com",
                    "dob":
                    None,
                    "feature_notification":
                    True,
                    "phone":
                    "23407035209988",
                    "address":
                    "Lagos Street, Abuja, Nigeria",
                    "location":
                    "Lagos Street, Abuja, Nigeria",
                    "social_link": {
                        "url": "www.google.com",
                        "name": "website"
                    },
                    "social_link_url":
                    "www.google.com",
                    "email_subscribed":
                    False,
                    "last_stop_point":
                    None,
                    'verified_email':
                    False,
                    "plan": {
                        "name": "Free",
                        "currency": "ngn",
                        "duration": None,
                        "expiry_date": None,
                        "last_renewed": None,
                        "resume_allowed": 1,
                    },
                },
            },
        )
        mock_post.assert_has_calls([call2])
        # mock_post.assert_called_once_with(
        #     f"{settings.CV_SERVICE_URL}/cv-profile",
        #     json={"hello": "world", "biola": "is_here"},
        #     headers={"Authorization": f"Bearer {response.json()['token']}"},
        # )
        user = User.objects.get(email=self.data["email"])
        self.assert_user_fields(user)
        link = self.assert_verification_email_sent(response, user,
                                                   "http://google.com")
        self.assertFalse(user.verified_email)
        self.assert_valid_verification_link(link, "https://app.careerlyft.com",
                                            user.last_stop_point or "")
        self.assertTrue(User.objects.get(email=user.email).verified_email)
        response = self.client.post("/signup", self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["errors"]["email"],
            ["You have an account with us already, Login instead"],
        )

    def test_signup_with_just_email_and_password(self):
        response = self.client.post(
            "/signup",
            {
                "email": self.data["email"],
                "password": self.data["password"]
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @mock.patch("authentication_service.utils.requests.post")
    def test_camel_case_should_also_update_user_details(self, mock_post):
        user = User.objects.create(
            email=self.data["email"],
            first_name=self.data["first_name"],
            username=self.data["email"],
        )
        new_data = {
            "contactAddress":
            "Avenida Corrientes 1213, Buenos Aires, Argentina",
            "country":
            "Nigeria",
            "email":
            self.data["email"],
            "firstName":
            "Tioluwani",
            "lastName":
            "Kolawole",
            "last_stop_point":
            "personal_info",
            "password":
            "password",
            "dob":
            "2018-10-5",
            "phoneNumber":
            "2347035209922",
            "photoUrl":
            "https://media.licdn.com/dms/image/C4D03AQGh_IDtPB8qoA/profile-displayphoto-shrink_100_100/0?e=1526738400&v=alpha&t=tLCQT2M_Q_EtKNz6uEQJcO0kKVyl-C9OeNVpm2se6cA",
            "socialNetwork":
            "linkedin",
            "socialLink":
            "linkedin.com",
            "about_details": {
                "hello": "world",
                "biola": "is_here"
            },
        }
        token = user.get_new_token()
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token)
        response = self.client.post("/personal-info", new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=self.data["email"])
        self.assertEqual(user.country, new_data["country"])
        self.assertEqual(user.first_name, new_data["firstName"])
        self.assertEqual(user.last_name, new_data["lastName"])
        self.assertEqual(user.phone_number, new_data["phoneNumber"])
        self.assertEqual(user.contact_address, new_data["contactAddress"])
        self.assertEqual(
            user.social,
            {
                "link": new_data["socialLink"],
                "network": new_data["socialNetwork"]
            },
        )
        mock_post.assert_called_once_with(
            f"{settings.CV_SERVICE_URL}/cv-profile-server",
            json={
                "data": {
                    "hello": "world",
                    "biola": "is_here"
                },
                "user_id": user.pk,
                "personal-info": {
                    "first_name":
                    "Tioluwani",
                    "last_name":
                    "Kolawole",
                    "country":
                    "Nigeria",
                    "photo_url":
                    "https://media.licdn.com/dms/image/C4D03AQGh_IDtPB8qoA/profile-displayphoto-shrink_100_100/0?e=1526738400&v=alpha&t=tLCQT2M_Q_EtKNz6uEQJcO0kKVyl-C9OeNVpm2se6cA",
                    "email":
                    "jamie@example.com",
                    "phone":
                    "2347035209922",
                    "dob":
                    "2018-10-5",
                    "address":
                    "Avenida Corrientes 1213, Buenos Aires, Argentina",
                    "location":
                    "Avenida Corrientes 1213, Buenos Aires, Argentina",
                    "social_link": {
                        "url": "linkedin.com",
                        "name": "linkedin"
                    },
                    "social_link_url":
                    "linkedin.com",
                    "feature_notification":
                    False,
                    "email_subscribed":
                    False,
                    "verified_email":
                    False,
                    "last_stop_point":
                    None,
                    "plan": {
                        "name": "Free",
                        "currency": "ngn",
                        "duration": None,
                        "expiry_date": None,
                        "last_renewed": None,
                        "resume_allowed": 1,
                    },
                },
            },
        )

    def test_user_already_exists_uses_different_end_point(self):
        user = User.objects.create(
            email=self.data["email"],
            first_name=self.data["first_name"],
            username=self.data["email"],
        )
        new_data = self.data.copy()
        del new_data["password"]
        response = self.client.post("/personal-info", new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + user.get_new_token())
        response = self.client.post("/personal-info", new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=self.data["email"])
        self.assert_user_fields(user, False)

    def assert_forgot_password_email_sent(self, request, user, callback):
        link = "{}?callback_url={}".format(
            reverse("reset_password_redirect", args=["IOkewojew"]), callback)
        self.send_mail.assert_called_once_with(
            "forgot_password",
            {
                "link": "{}{}".format(settings.BASE_URL, link),
                "first_name": user.first_name,
                "email": user.email,
            },
            user.email,
        )
        return link

    # Todo: To change to token instead of email.
    @mock.patch("authentication_service.forms.get_payload")
    @mock.patch("authentication_service.models.User.get_new_token")
    def test_change_password(self, mock_token, mock_get_email):
        mock_token.return_value = "IOkewojew"
        mock_get_email.return_value = "a@example.com"
        user = User.objects.create(
            email="a@example.com",
            first_name="Aola",
            username="a@example.com",
            last_name="AAA",
        )
        response = self.client.post(
            "/reset-password",
            {
                "email": user.email,
                "callback": "http://youtube.com"
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        link = self.assert_forgot_password_email_sent(settings.BASE_URL, user,
                                                      "http://youtube.com")
        new_response = self.client.get(link)
        self.assertEqual(new_response.status_code,
                         status.HTTP_301_MOVED_PERMANENTLY)
        self.assertEqual(new_response.url, "{}?token={}".format(
            "http://youtube.com", "IOkewojew"))
        # self.assertEqual(
        #     new_response.url, "{}?email={}".format("http://youtube.com", user.email)
        # )

    def test_verify_password(self):
        user = User.objects.create(
            email="a@example.com",
            first_name="Aola",
            username="a@example.com",
            last_name="AAA",
        )
        response = self.client.post(
            "/reset-password",
            {
                "email": user.email,
                "password": "samadina"
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"],
                         "password has been updated")
        new_user = User.objects.get(email=user.email)
        self.assertTrue(new_user.check_password("samadina"))

    def test_raise_error_when_invalid_redirect_url(self):
        response = self.client.get(
            reverse("verify_email_link") +
            "?email=olodo@example.com&token=3232323")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_invalid_social_link_without_network(self):
        new_data = {**self.data}
        del new_data["social_link"]
        response = self.client.post("/signup", new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # data = response.json()
        # self.assertEqual(data['errors'], {
        #                  'social_link': ["Ensure both social_netowrk and social_link is sent."]})

    def assert_valid_verification_link(self, link, callback_url,
                                       last_stop_point):
        response = self.client.get(link)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, "{}?last_stop_point={}".format(
            callback_url, last_stop_point))
        self.send_mail.assert_any_call(
            "welcome_email",
            {
                "link":
                "{}".format(settings.CLIENT_URL, settings.CLIENT_WELCOME_PATH),
                "first_name":
                self.data["first_name"],
            },
            self.data["email"],
        )


class AuthenticationViewTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.username = "b@example.com"
        self.password = "password"
        self.user = User.objects.create_user(
            username=self.username,
            email=self.username,
            password=self.password,
            last_stop_point="mission-statement",
        )
        self.data = {"email": self.username, "password": self.password}

    @mock.patch("authentication_service.utils.requests.get")
    def test_login_valid(self, mock_get):
        mock_get.return_value = MockResponse({"data": {"hello": "world"}})
        response = self.client.post("/login", self.data, format="json")
        decoded_payload = utils.jwt_decode_handler(response.data["token"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(decoded_payload["username"], self.username)
        self.assertEqual(response.data["last_stop_point"], "mission-statement")
        # self.assertEqual(response.data['user'], self.username)

    @mock.patch("authentication_service.utils.requests.get")
    def test_authenticate_returns_personal_info_as_well_as_last_cv(
            self, mock_get):
        mock_get.return_value = MockResponse({"data": {"hello": "world"}})
        response = self.client.post("/login", self.data, format="json")
        decoded_payload = utils.jwt_decode_handler(response.data["token"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get.assert_called_once_with(
            settings.CV_SERVICE_DELETE_URL,
            headers={"Authorization": f"Bearer {response.data['token']}"},
        )
        self.assertEqual(response.data["working_cv"], {"hello": "world"})
        self.assertEqual(response.data["personal_info"], self.user.as_json)

    def test_login_invalid(self):
        response = self.client.post("/login", {
            "email": "jj@example.com",
            "password": self.password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # import pdb ; pdb.set_trace()
        self.assertEqual(
            response.data["errors"][0],
            "Looks like you don't have an account with us, sign up by creating your first Resume",
        )
        response = self.client.post("/login", {
            "email": self.username,
            "password": "ororo"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # import pdb ; pdb.set_trace()
        self.assertEqual(response.data["errors"][0],
                         "Your password is incorrect, try again")
        # response = self.client.post('/login', {
        #     'email': "hello@example.com",
        #     'password': ""
        # })
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # # import pdb ; pdb.set_trace()
        # self.assertEqual(response.data['errors'][0],
        #                  'Your email and password combination is incorrect, try again')

    def get_token(self):
        response = self.client.post("/login", self.data, format="json")
        return response.data["token"]

    @mock.patch("authentication_service.utils.requests.get")
    def test_authenticate_token_valid(self, mock_get):
        mock_get.return_value = MockResponse({"data": {"hello": "world"}})

        orig_token = self.get_token()

        response = self.client.post(
            "/api-token-verify", {"token": orig_token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], orig_token)

    @mock.patch("authentication_service.utils.requests.get")
    def test_authenticate_token_valid_with_meta_true_flag_passed(
            self, mock_get):
        mock_get.return_value = MockResponse({"data": {"hello": "world"}})

        orig_token = self.get_token()

        response = self.client.post(
            "/api-token-verify?meta=1", {"token": orig_token}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], orig_token)
        metadata = response.data["metadata"]
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata[0]["email"], self.username)

    def test_authenticate_token_valid_with_last_stop_point_passed(self):
        token = self.user.get_new_token()
        response = self.client.post(
            "/api-token-verify?user_details=facebook",
            {
                "token": token,
                "last_stop_point": "story-statement",
                "shared_network": "facebook",
                "user_details": "true",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["token"], token)
        self.assertEqual(
            response.data["shared_networks"],
            {
                "first_name": "",
                "last_name": "",
                "country": None,
                "email": "b@example.com",
                "phone_number": None,
                "dob": None,
                "feature_notification": True,
                "contact_address": None,
                "networks": ["facebook"],
                "email_subscribed": False,
                "quickbooks_customer_details": {},
            },
        )
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.last_stop_point, "story-statement")
        self.assertEqual(user.shared_networks, ["facebook"])

    def test_authenticate_token_invalid_expired(self):
        pass

    def test_can_update_record_of_user_with_extra_info(self):
        response = self.client.post(
            "/save-custom-data",
            json.dumps({
                "user_id": self.user.pk,
                "data": {
                    "quickbooks_customer_details": {
                        "id": "232",
                        "name": "the queen",
                    }
                },
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record = User.objects.first()
        self.assertEqual(
            record.other_details,
            {
                "quickbooks_customer_details": {
                    "id": "232",
                    "name": "the queen"
                }
            },
        )

    def test_fetch_cv_details_on_verifying_token(self):
        self.update_user_data()
        token = self.user.get_new_token()
        response = self.client.post("/api-token-verify", {
            "token": token,
            "cv_details": True
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["personal-info"],
            self.get_personal_info({
                "email_subscribed": False,
                "feature_notification": True,
                "dob": None,
                "last_stop_point": "mission-statement",
                "verified_email": False
            }),
        )

    def update_user_data(self):
        data = {
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
        }
        for key, value in data.items():
            setattr(self.user, key, value)
        self.user.save()

    def get_personal_info(self, extra=None):
        data = extra or {}
        return {
            "first_name":
            self.user.first_name,
            "last_name":
            self.user.last_name,
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
            self.user.email,
            "social_link_url":
            "http://www.kola.com",
            **data,
            "plan": {
                "name": "Free",
                "currency": "ngn",
                "duration": None,
                "expiry_date": None,
                "last_renewed": None,
                "resume_allowed": 1,
            },
        }

    def test_get_profile_data(self):
        self.update_user_data()
        response = self.client.get("")
        self.client.credentials(
            HTTP_AUTHORIZATION="Token " + self.user.get_new_token())
        response = self.client.get("/personal-info", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            self.get_personal_info({
                "email_subscribed": False,
                "dob": None,
                "feature_notification": True,
                "last_stop_point": "mission-statement",
                "verified_email": False
            }),
        )

    @mock.patch("authentication_service.services.requests.delete")
    def test_delete_account_endpoint(self, mock_post):
        mock_post.return_value = MockResponse({})
        self.assertEqual(User.objects.count(), 1)
        token = self.user.get_new_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.delete("/personal-info", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        mock_post.assert_called_once_with(
            settings.CV_SERVICE_DELETE_URL,
            headers={"Authorization": f"Bearer {token}"})


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data
