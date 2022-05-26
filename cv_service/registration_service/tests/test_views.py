from django.test import TestCase
from unittest import mock
from registration_service.models import CVProfile
import json


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data


class CVBuildTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.patcher = mock.patch("registration_service.utils.requests.post")
        self.mock_auth = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @property
    def profile_details(self):
        return {
            "first_name":
            "hello",
            "last_name":
            "world",
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
            "email":
            "James@example.com",
        }

    def json_post(self, url, data, **kwargs):
        return self.client.post(
            url, json.dumps(data), content_type="application/json", **kwargs)

    def get_token(self, extra={}):
        self.mock_auth.return_value = MockResponse({
            "user_id":
            101,
            "token":
            "jeojwiojwioejwijowjo",
            "personal-info": {
                "email_subscribed": False
            },
            **extra,
        })
        return "jeojwiojwioejwijowjo"

    def assert_success_and_count(self, token, data, count=1):
        response = self.json_post(
            "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CVProfile.objects.count(), count)
        return response.json()

    def create_cv_instance(self):
        data = {
            "mission_statement":
            "This is the mission statement for the year",
            "work_experiences": [
                {
                    "name": "University of Olodo",
                    "role": "systems Engineer",
                    "start_date": "2017-10",
                    "end_date": "2018-2",
                },
                {
                    "name":
                    "Compal Electronics",
                    "role":
                    "Frontend Engineer",
                    "highlights":
                    "<ul>↵<li>Generated positive cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                    "start_date":
                    "2017-06",
                    "currently_work":
                    True,
                },
            ],
            "headline":
            "Systems Engineer",
            "educations": [{
                "cgpa": "4.80",
                "course": "Music Psychology",
                "degree": "Bachelor of Music - BMus",
                "degreeLevel": "Second class, Upper",
                "gradePoint": "5.00",
                "school": "University of North Bengal",
                "showCgpa": True,
                "yearOfCompletion": "2015",
            }],
            "trainings": [{
                "name": "University of Olodo",
                "role": "systems Engineer",
                "start_date": "12/10/2017",
                "currently_work": True,
            }],
            "industry_skills": ["Installation", "Designing"],
            "softwares": ["Photoshop", "Invision"],
            "certifications": [{
                "name": "Cisco certified professional",
                "organization": "Cisco Systems, Inc.",
                "yearOfCompletion": "2016",
            }],
            "completed":
            True,
        }
        cv_data = CVProfile.objects.create(**data, user_id=101)
        return cv_data, data

    def test_transform_profile_data_to_cv(self):
        cv_data, data = self.create_cv_instance()
        result = cv_data.get_cv(self.profile_details)
        self.assertEqual(
            result["personal_info"],
            {
                "first_name": self.profile_details["first_name"],
                "last_name": self.profile_details["last_name"],
                "country": self.profile_details["country"],
                "photo_url": self.profile_details["photo_url"],
                "email": self.profile_details["email"],
                "phone": self.profile_details["phone"],
                "social_link_url": None,
                "social_link": self.profile_details["social_link"],
                "address": self.profile_details["address"],
                "headline": data["headline"],
            },
        )
        self.assertEqual(
            result["mission_statement"],
            {
                "heading": "Career Profile",
                "body": data["mission_statement"]
            },
        )
        self.assertEqual(
            result["work_experience"],
            {
                "heading":
                "Work Experience",
                "body": [
                    {
                        "company_name": "University of Olodo",
                        "position": "systems Engineer",
                        "startDate": "2017-10",
                        "currentlyWorking": False,
                        "endDate": "2018-2",
                        "highlights": "",
                        "duration": "2017-2018",
                    },
                    {
                        "company_name":
                        "Compal Electronics",
                        "position":
                        "Frontend Engineer",
                        "startDate":
                        "2017-06",
                        "currentlyWorking":
                        True,
                        "endDate":
                        "",
                        "highlights":
                        "<ul>↵<li>Generated positive cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                        "duration":
                        "2017-Current",
                    },
                ],
            },
        )
        self.assertEqual(
            result["education"],
            {
                "heading":
                "Education",
                "body": [{
                    "cgpa": "4.80",
                    "course": "Music Psychology",
                    "degree": "BMus",
                    "gradePoint": "5.00",
                    "school_name": "University of North Bengal",
                    "showCgpa": True,
                    "completion_year": "2015",
                }],
            },
        )
        self.assertEqual(result["training"], [])
        self.assertEqual(
            result["certifications"],
            {
                "heading":
                "Certifications",
                "body": [{
                    "title": "Cisco certified professional",
                    "company": "Cisco Systems, Inc.",
                    "yearOfCompletion": "2016",
                    "date": "2016",
                }],
            },
        )
        # self.assertEqual(cv_data.get_cv(self.profile_details), {
        #     'schema_version': "1.0.0",
        #     'about_user': {

        #     },
        #     'software_skills': {
        #         "heading": "Software Skills",
        #         "body": ["Photoshop", "Invision"]
        #     },
        #     'industry_skills': {
        #         "heading": "Special Skills",
        #         "body": [
        #             {
        #                 "title": "Installation",
        #                 "description": ""
        #             },
        #             {
        #                 'title': "Designing",
        #                 'description': ""
        #             }
        #         ]
        #     }
        # })

    def test_save_completed_cv(self):
        token = self.get_token()
        cv_data, _ = self.create_cv_instance()
        data = {"cv": {"age": "holla"}}
        response = self.json_post(
            f"/update-cv/{cv_data.pk}",
            data,
            HTTP_AUTHORIZATION="Bearer {}".format(token),
        )
        result = {
            "age": "holla",
            "completed": True,
            "headline": "Systems Engineer",
            "job_category": None,
            "job_position": None,
            "level": None,
            "name": "",
        }
        for key, value in result.items():
            self.assertEqual(response.json()["data"][key], value)

    # def test_save_cv_thumbnail(self):
    #     cv_data, _ = self.create_cv_instance()
    #     response = self.json_post(f"save-thumbnail/{cv_data.pk}",data={})
