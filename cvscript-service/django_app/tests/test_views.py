from django.test import TestCase
from unittest import mock
import json
from django.conf import settings
from django_app import models


class MockResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data


def create_test_category_and_job_position():
    job_category = models.JobCategory.objects.create(
        name="Engineering",
        keywords=["Hardware", "Software", "Full Stack"],
        software_skills=["Django", "React", "Vue"],
        industry_skills=["Software Design", "Analytics Development"],
    )
    job_position = models.JobPosition.objects.create(
        name="Systems Engineering",
        keywords=["Hardware", "Software", "Full Stack"],
        software_skills=["Django", "React", "Vue"],
        industry_skills=["Software Design", "Analytics Development"],
    )
    job_position.job_categories.add(job_category)
    return job_category, job_position


class CVScriptTestCase(TestCase):
    def setUp(self):
        self.job_category, self.job_position = create_test_category_and_job_position()
        self.cv_script = models.CVScript.objects.create(
            section=1,
            text=(
                "Organized, responsible, and driven "
                "[Human Resource Manager] with (15)+ years of experience "
                "in fast-moving environments. Track record of leading human "
                "resources teams to {Microsoft Office} business solutions that are on "
                "<Product Design>, <Fabrication>"
                "time and to budget. Ability to overhaul human resources "
                "procedures and processes to {Quick books} more cost-efficient "
                "solutions to businesses. *mechatronics#, *3d modelling# and *chassis design#"
            ),
        )
        self.job_cv_script = models.JobCVScript.objects.create(
            script=self.cv_script, job_category=self.job_category
        )
        self.patcher = mock.patch("django_app.utils.requests.post")
        self.patcher2 = mock.patch("django_app.utils.get_cvscript")
        self.mock_auth = self.patcher.start()
        self.mock_get_cvscript = self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def json_get(self, url, data=None, **kwargs):
        return self.client.get(url, data, content_type="application/json", **kwargs)

    def test_fetch_cv_scripts(self):
        data = {
            "job-position": self.job_position.name,
            "job-category": self.job_category.name,
        }
        response = self.json_get("/cv-scripts/mission-statement", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)

    def test_fetch_cv_scripts_with_token(self):
        token = self.get_token()
        self.mock_get_cvscript.return_value = {"result": ["hello world"]}

        data = {
            "job-position": self.job_position.name,
            "job-category": self.job_category.name,
        }
        response = self.json_get(
            "/cv-scripts/mission-statement?agent=True",
            data,
            HTTP_AUTHORIZATION="Bearer {}".format(token),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 1)
        self.assertEqual(response.json()["data"], ["hello world"])

    def test_when_no_token_is_passed(self):
        data = {"job-position": self.job_position.name}
        response = self.json_get("/cv-scripts/mission-statement", data)
        self.assertEqual(response.status_code, 200)

        # self.assertEqual(response.status_code, 403)
        # self.assertEqual(
        #     response.json()['errors'], "Ensure to set the Authorization Header with your user token")

    def test_when_user_token_is_passed(self):
        self.mock_auth.return_value = MockResponse(
            {"user_id": 101, "token": "jeojwiojwioejwijowjo"}, 200
        )
        self.mock_get_cvscript.return_value = {"result": ["hello world"]}
        token = "jeojwiojwioejwijowjo"

        response = self.json_get(
            "/cv-scripts/mission-statement",
            HTTP_AUTHORIZATION="Bearer {}".format(token),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], ["hello world"])
        self.mock_get_cvscript.assert_called_once_with(
            "mission_statement",
            f"{settings.CV_PROFILE_SERVICE}/v2/graphql",
            user_id=101,
            headers=None,
        )

    def test_when_invalid_token_is_passed(self):
        self.mock_auth.return_value = MockResponse({}, 400)
        data = {"job-position": self.job_position.name}
        token = "jeojwiojwioejwijowjo"
        response = self.json_get(
            "/cv-scripts/mission-statement",
            data,
            HTTP_AUTHORIZATION="Bearer {}".format(token),
        )
        self.assertEqual(response.status_code, 200)

        # self.assertEqual(response.status_code, 403)
        # self.assertEqual(
        #     response.json()['errors'], "This token is either invalid or expired")

    def get_token(self):
        self.mock_auth.return_value = MockResponse(
            {"user_id": 101, "token": "jeojwiojwioejwijowjo"}
        )
        return "jeojwiojwioejwijowjo"

    def test_get_categories(self):
        response = self.json_get("/job-categories")
        self.assertEqual(response.status_code, 200)

    def test_get_positions(self):
        data = {"job-category": self.job_category.name}
        response = self.json_get("/job-positions", data)
        self.assertEqual(len(response.json()["data"]), 1)

    def test_job_positions_for_user(self):
        self.mock_auth.return_value = MockResponse(
            {"user_id": 101, "token": "jeojwiojwioejwijowjo"}, 200
        )
        self.mock_get_cvscript.return_value = {"result": ["Systems Engineering"]}
        token = "jeojwiojwioejwijowjo"

        data = {"q": "sys"}
        response = self.json_get(
            "/job-positions", data, HTTP_AUTHORIZATION="Bearer {}".format(token)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": [{"name": "Systems Engineering"}]})
        self.mock_get_cvscript.assert_called_once_with(
            "job_position",
            f"{settings.CV_PROFILE_SERVICE}/v2/graphql",
            user_id=101,
            headers=None,
        )

    def test_get_positions_with_query_params_greater_than_three(self):

        data = {"q": "sys"}
        response = self.json_get("/job-positions", data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": [{"name": "Systems Engineering"}]})

    def test_get_positions_with_query_params_less_than_three(self):

        data = {"q": "sy"}
        response = self.json_get("/job-positions", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": []})


class MissingRecordTestCase(TestCase):
    def setUp(self):
        options = [
            ("Unilag", models.CompanyAndSchool.SCHOOL),
            ("Careerlyft", models.CompanyAndSchool.COMPANY),
            ("Systems Engineering", models.CompanyAndSchool.COURSE),
            ("B.Sc", models.CompanyAndSchool.DEGREE),
        ]
        records = [models.CompanyAndSchool(name=i[0], kind=i[1]) for i in options]
        models.CompanyAndSchool.objects.bulk_create(records)
        self.job_category, self.job_position = create_test_category_and_job_position()

    def test_when_job_position_does_not_exist(self):
        data = {"q": "Systems"}
        self.make_call("/job-positions", data, [{"name": "Systems Engineering"}])
        self.assertEqual(models.MissingRecord.objects.count(), 0)
        self.make_call("/job-positions", {"q": "Ensligh"}, [])
        self.assertEqual(models.MissingRecord.objects.count(), 1)
        record = models.MissingRecord.objects.first()
        self.assertEqual(record.name, "Ensligh")
        self.assertEqual(record.kind, models.CompanyAndSchool.JOB_POSITION)

    def make_call(self, endpoint, search, result):
        response = self.client.get(endpoint, search)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], result)

    def test_when_university_school_name_does_not_exist(self):
        self.make_call("/schools", {"q": "unil"}, ["Unilag"])
        self.assertEqual(models.MissingRecord.objects.count(), 0)
        self.make_call("/schools", {"q": "Ibad"}, [])
        self.assertEqual(models.MissingRecord.objects.count(), 1)
        record = models.MissingRecord.objects.first()
        self.assertEqual(record.name, "Ibad")
        self.assertEqual(record.kind, models.CompanyAndSchool.SCHOOL)


class JobCategoryAndPositionViewTestCase(TestCase):
    def setUp(self):
        self.job_category, self.job_position = create_test_category_and_job_position()
        self.cv_script = models.CVScript.objects.create(
            section=1,
            text=(
                "Organized, responsible, and driven "
                "[Human Resource Manager] with (15)+ years of experience "
                "in fast-moving environments. Track record of leading human "
                "resources teams to {Microsoft Office} business solutions that are on "
                "<Product Design>, <Fabrication>"
                "time and to budget. Ability to overhaul human resources "
                "procedures and processes to {Quick books} more cost-efficient "
                "solutions to businesses. *mechatronics#, *3d modelling# and *chassis design#"
            ),
        )
        self.job_cv_script = models.JobCVScript.objects.create(
            script=self.cv_script, job_category=self.job_category
        )
        self.patcher = mock.patch("django_app.utils.requests.post")
        self.mock_auth = self.patcher.start()

    def test_get_job_positions_and_category_endpoint(self):
        data = {"q": "Systems"}
        self.make_call("/job-positions", data, [{"name": "Systems Engineering"}])
        self.make_call(
            "/job-categories", {"q": "Systems Engineering"}, [{"name": "Engineering"}]
        )

    def make_call(self, endpoint, search, result):
        response = self.client.get(endpoint, search)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"], result)
