from unittest import mock
from django.test import TestCase
from authentication_service.utils import send_mail
from django.conf import settings
import json
from cv_utils.mail import SENDGRID_TEMPLATES as sendgrid_templates


class MockResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class MailTestCase(TestCase):
    def setUp(self):
        self.patcher = mock.patch("cv_utils.mail.requests.post")
        self.mock_mail = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def assert_mock_call(self, kind, params):
        self.mock_mail.assert_called_once_with(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": "Bearer {}".format(settings.SENDGRID_API_KEY),
                "content-type": "application/json",
            },
            data=json.dumps({**params, "template_id": sendgrid_templates[kind]["id"]}),
        )

    def test_welcome_email(self):
        self.mock_mail.return_value = MockResponse({})
        send_mail(
            "welcome_email",
            {"first_name": "Peter", "link": "http://google.com"},
            "peterolayinka97@gmail.com",
        )

        self.assert_mock_call(
            "welcome_email",
            {
                "from": {"email": "hello@careerlyft.com", "name": "Careerlyft"},
                "personalizations": [
                    {
                        "to": [{"email": "peterolayinka97@gmail.com"}],
                        "substitutions": {
                            "%create_resume_url%": "http://google.com",
                            "%first_name%": "Peter",
                        },
                    }
                ],
            },
        )

    def test_forgot_email(self):
        self.mock_mail.return_value = MockResponse({})
        send_mail(
            "forgot_password",
            {
                "email": "peterolayinka97@gmail.com",
                "first_name": "Peter",
                "link": "http://google.com",
            },
            "peterolayinka97@gmail.com",
        )

        self.assert_mock_call(
            "forgot_password",
            {
                "from": {"email": "hello@careerlyft.com", "name": "Careerlyft"},
                "personalizations": [
                    {
                        "to": [{"email": "peterolayinka97@gmail.com"}],
                        "substitutions": {
                            "%reset_password_url%": "http://google.com",
                            "%first_name%": "Peter",
                            "%email%": "peterolayinka97@gmail.com",
                        },
                    }
                ],
            },
        )

    def test_verify_email(self):
        self.mock_mail.return_value = MockResponse({})
        send_mail(
            "verify_email",
            {"first_name": "Peter", "link": "http://google.com"},
            "peterolayinka97@gmail.com",
        )

        self.assert_mock_call(
            "verify_email",
            {
                "from": {"email": "hello@careerlyft.com", "name": "Careerlyft"},
                "personalizations": [
                    {
                        "to": [{"email": "peterolayinka97@gmail.com"}],
                        "substitutions": {
                            "%confirm_email_url%": "http://google.com",
                            "%first_name%": "Peter",
                        },
                    }
                ],
            },
        )

    def test_drop_off_email(self):
        self.mock_mail.return_value = MockResponse({})
        send_mail(
            "drop_off_email",
            {
                "first_name": "Peter",
                "link": "http://google.com",
                "last_stop_point": "mission_statement",
                "job_position": "Systems Engineer"
            },
            "peterolayinka97@gmail.com",
        )

        self.assert_mock_call(
            "drop_off_email",
            {
                "from": {"email": "hello@careerlyft.com", "name": "Careerlyft"},
                "personalizations": [
                    {
                        "to": [{"email": "peterolayinka97@gmail.com"}],
                        "substitutions": {
                            "%first_name%": "Peter",
                            "%return_url%": "http://google.com",
                            "%last_stop_point%": "mission_statement",
                            "%job_position%": "Systems Engineer"
                        },
                    }
                ],
            },
        )
