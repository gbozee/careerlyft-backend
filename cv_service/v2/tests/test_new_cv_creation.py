from starlette.testclient import TestClient
from v2 import app
import pytest
from registration_service import models
from django.conf import settings
from aioresponses import aioresponses
import test_utils
from cv_utils.tests import MockResponse


@pytest.fixture
def mocked():
    with aioresponses() as m:
        yield m


# def get_mock(mock_call, args):
#     mock_instance = mock_call.return_value
#     mock_instance.verify_payment.return_value = args
#     return mock_instance


@pytest.fixture
def profile_details():
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


@pytest.fixture
def client():
    client = TestClient(app)
    return client


def get_token(subscribed=False, last_stop_point="mission-statement", extra={}):
    return {
        "user_id": 101,
        "token": "jeojwiojwioejwijowjo",
        "personal-info": {
            "email_subscribed": subscribed,
            "last_stop_point": last_stop_point,
        },
        **extra,
    }


def get_headers(**kwargs):
    headers = {}
    if "HTTP_AUTHORIZATION" in kwargs:
        headers["Authorization"] = kwargs.pop("HTTP_AUTHORIZATION")
    return headers


def json_post(url, data, **kwargs):
    client = TestClient(app)
    return client.post(url, json=data, headers=get_headers(**kwargs))


def json_get(url, **kwargs):
    client = TestClient(app)
    return client.get(url, headers=get_headers(**kwargs))


def json_delete(url, **kwargs):
    client = TestClient(app)
    return client.delete(url, headers=get_headers(**kwargs))


@pytest.fixture
def cv_instance():
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
    cv_data = models.CVProfile.objects.create(**data, user_id=101)
    return cv_data, data


def create_mock(mocker, status_code=200, extra={}):
    token = "jeojwiojwioejwijowjo"
    ma = mocker.patch("registration_service.utils.requests.post")
    ma.return_value = MockResponse(
        {
            "user_id": 101,
            "token": token,
            "personal-info": {
                "email_subscribed": False
            },
            **extra,
        },
        status_code=status_code,
    )
    return ma


@pytest.fixture
def mock_auth_s(mocker):
    def _mock_auth(subscribed=False,
                   last_stop_point="mission-statement",
                   extra={},
                   status_code=200):
        return create_mock(
            mocker,
            status_code,
            get_token(
                subscribed=subscribed,
                last_stop_point=last_stop_point,
                extra=extra),
        )

    return _mock_auth


@pytest.fixture
def mock_auth(mock_auth_s, profile_details):
    return mock_auth_s(extra={"personal-info": profile_details})
    # return create_mock(mocker, {"personal-info": profile_details})


@pytest.mark.django_db(transaction=True)
def test_fetching_profile_information(mock_auth, profile_details):
    response = json_get(
        "/get-profile",
        content_type="application/json",
        HTTP_AUTHORIZATION="Bearer {}".format(token),
    )
    test_utils.assertEqual(response.json(), {"data": {}})


@pytest.mark.django_db
def test_save_mission_statement(mock_auth):
    data = {
        "mission_statement": "This is the mission statement for the year",
        "last_stop_point": "mission-statement",
        "job_position": "Systems Engineering",
        "job_category": "Engineering & Management",
    }
    token = get_token()["token"]
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    mock_auth.assert_called_once_with(
        settings.AUTHENTICATION_SERVICE,
        json={
            "token": token,
            "last_stop_point": "mission-statement",
            "cv_details": True,
        },
    )

    record = models.CVProfile.objects.first()
    assert record.mission_statement == data["mission_statement"]
    assert record.job_position == data["job_position"]
    assert record.job_category == data["job_category"]
    assert record.cv_data["mission_statement"] == {
        "heading": "Career Profile",
        "body": data["mission_statement"],
    }
    assert record.user_id == 101
    response = json_post(
        "/cv-profile",
        {
            **data, "id": record.id,
            "mission_statement": "holla"
        },
        HTTP_AUTHORIZATION="Bearer {}".format(token),
    )
    assert models.CVProfile.objects.count() == 1
    record = models.CVProfile.objects.first()
    assert record.mission_statement == "holla"


# def


@pytest.mark.django_db
def test_save_mission_statement_when_subscribed_to_mailing_list(
        mocker, mock_auth_s):
    mock_mail = mocker.patch("registration_service.utils.mail")
    mock_auth_s(True)
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token(True))
    data = {
        "mission_statement": "This is the mission statement for the year",
        "last_stop_point": "mission-statement",
        "job_position": "Systems Engineering",
        "job_category": "Engineering & Management",
    }
    token = get_token()["token"]
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    record = models.CVProfile.objects.first()
    assert record.mission_statement == data["mission_statement"]
    assert record.job_position == data["job_position"]
    assert record.job_category == data["job_category"]
    assert record.cv_data["mission_statement"] == {
        "heading": "Career Profile",
        "body": data["mission_statement"],
    }
    mock_mail.complete_profile_steps.assert_called_once_with([{
        "email":
        None,
        "job_category":
        data["job_category"],
        "job_position":
        data["job_position"],
        "last_stop_point":
        data["last_stop_point"],
    }])


def test_when_invalid_token_is_passed(mock_auth_s):
    mock_auth_s(status_code=400)
    # mocked.post(settings.AUTHENTICATION_SERVICE, status=400, payload={})
    data = {"mission_statement": "This is the mission statement for the year"}
    token = "jeojwiojwioejwijowjo"

    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 403
    assert response.json() == {
        "errors": "This token is either invalid or expired"
    }


def test_when_no_token_is_passed():
    data = {"mission_statement": "This is the mission statement for the year"}
    response = json_post("/cv-profile", data)
    assert response.status_code == 403
    assert (response.json()["errors"] ==
            "Ensure to set the Authorization Header with your user token")


@pytest.mark.django_db
def test_save_work_experiences(mock_auth):
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    token = get_token()["token"]
    data = {
        "work_experiences": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }]
    }
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    record = models.CVProfile.objects.first()
    assert record.work_experiences == [{
        "name": "University of Olodo",
        "role": "systems Engineer",
        "start_date": "12/10/2017",
        "currently_work": True,
        'end_date': None
    }]

    assert record.cv_data["work_experience"] == {
        "heading":
        "Work Experience",
        "body": [
            models.work_experience_transform({
                "name": "University of Olodo",
                "role": "systems Engineer",
                "start_date": "12/10/2017",
                'end_date': None,
                "currently_work": True,
            })
        ],
    }


@pytest.mark.django_db
def test_save_education(mock_auth):
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())

    token = get_token()["token"]
    data = {
        "headline":
        "Systems Engineer",
        "educations": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
            "degree_level": "Third Class",
        }],
        "trainings": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }],
    }
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    record = models.CVProfile.objects.first()
    assert record.educations == [{
        "name": "University of Olodo",
        "role": "systems Engineer",
        "start_date": "12/10/2017",
        "currently_work": True,
        "degree_level": "Third Class",
    }]

    assert record.headline, "Systems Engineer"
    assert record.trainings == [{
        "name": "University of Olodo",
        "role": "systems Engineer",
        "start_date": "12/10/2017",
        "currently_work": True,
    }]

    assert record.cv_data["education"] == {
        "heading":
        "Education",
        "body": [
            models.work_experience_transform(
                {
                    "name": "University of Olodo",
                    "role": "systems Engineer",
                    "start_date": "12/10/2017",
                    "currently_work": True,
                    "degree_level": "Third Class",
                },
                kind="education",
            )
        ],
    }


@pytest.mark.django_db
def test_save_industry_skills(mock_auth):
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    token = get_token()["token"]
    data = {
        "industry_skills": [{
            "title":
            "UX Design",
            "description":
            "Creating User Interfaces for applications in a way that meets the users needs and business goals",
        }],
        "softwares": ["Photoshop", "Invision"],
    }
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    record = models.CVProfile.objects.first()
    assert record.industry_skills == [{
        "title":
        "UX Design",
        "description":
        "Creating User Interfaces for applications in a way that meets the users needs and business goals",
    }]

    assert record.softwares == ["Photoshop", "Invision"]
    assert record.cv_data["industry_skills"] == {
        "heading":
        "Industry Expertise",
        "body": [{
            "title":
            "UX Design",
            "description":
            "Creating User Interfaces for applications in a way that meets the users needs and business goals",
        }],
    }
    assert record.cv_data["software_skills"] == {
        "heading":
        "Software Skills",
        "body": [{
            "title": "All Softwares",
            "softwares": ["Photoshop", "Invision"]
        }],
    }


@pytest.mark.django_db
def test_awards_or_certifications(mock_auth):
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    token = get_token()["token"]
    data = {
        "certifications": [{
            "name": "University of Olodo",
            "organization": "systems Engineer",
            "yearOfCompletion": "2017",
        }]
    }
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    assert response.status_code == 200
    record = models.CVProfile.objects.first()
    assert record.certifications == [{
        "name": "University of Olodo",
        "organization": "systems Engineer",
        "yearOfCompletion": "2017",
    }]

    assert record.cv_data["certifications"] == {
        "heading":
        "Certifications",
        "body": [
            models.work_experience_transform(
                {
                    "name": "University of Olodo",
                    "organization": "systems Engineer",
                    "yearOfCompletion": "2017",
                },
                kind="certifications",
            )
        ],
    }


def assert_success_and_count(token, data, count=1):
    response = json_post(
        "/cv-profile", data, HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(models.CVProfile.objects.count(), count)
    return response.json()


@pytest.mark.django_db(transaction=True)
# @pytest.mark.django_db
def test_saves_on_uncompleted_profile_alone(mock_auth):
    token = get_token()["token"]
    # test_utils.assertEqual(models.CVProfile.objects.count(), 0)
    data = {
        "mission_statement": "This is the mission statement for the year",
        "last_stop_point": "mission-statement",
    }
    assert_success_and_count(token, data)
    data = {
        "work_experiences": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }]
    }
    assert_success_and_count(token, data)
    data = {
        "headline":
        "Systems Engineer",
        "educations": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }],
        "trainings": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }],
    }
    assert_success_and_count(token, data)
    data = {
        "industry_skills": [{
            "name": "University of Olodo",
            "role": "systems Engineer",
            "start_date": "12/10/2017",
            "currently_work": True,
        }],
        "softwares": ["Photoshop", "Invision"],
    }
    assert_success_and_count(token, data)
    data = {
        "certifications": [{
            "name": "University of Olodo",
            "organization": "systems Engineer",
            "yearOfCompletion": "2017",
        }],
        "completed":
        True,
    }
    assert_success_and_count(token, data)
    data = {
        "certifications": [{
            "name": "University of Olodo",
            "organization": "systems Engineer",
            "yearOfCompletion": "2017",
        }]
    }
    assert_success_and_count(token, data, 2)


token = get_token("token")


@pytest.mark.django_db(transaction=True)
# @pytest.mark.django_db
def test_end_point_to_get_uncompleted_profile(mock_auth):
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    # mocked.post(settings.AUTHENTICATION_SERVICE, payload=get_token())
    response = json_get(
        "/get-profile", HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)

    test_utils.assertEqual(response.json()["data"], {})
    data = {
        "certifications": [{
            "name": "University of Olodo",
            "organization": "systems Engineer",
            "yearOfCompletion": "2017",
            "date": "2017",
        }]
    }
    assert_success_and_count(token, data, 1)
    response = json_get(
        "/get-profile", HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    instance = models.CVProfile.objects.first()
    rst = response.json()["data"]
    test_utils.assertEqual(rst["modified"],
                           instance.modified.timestamp() * 1000)
    # test_utils.assertEqual(response.json()['data'], {
    #                  **data, "modified": instance.modified.timestamp()*1000})


@pytest.mark.django_db(transaction=True)
def test_get_particular_cv_profile(mock_auth, profile_details):
    data = {
        "certifications": [{
            "name": "University of Olodo",
            "organization": "systems Engineer",
            "yearOfCompletion": "2017",
        }]
    }
    result = assert_success_and_count(token, {**data, "completed": True}, 1)
    response = json_get(
        f'/get-profile/{result["id"]}',
        HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    instance = models.CVProfile.objects.first()
    test_utils.assertEqual(
        response.json()["data"],
        {
            **instance.cv_data,
            "pk": result["id"],
            "modified": instance.modified.timestamp() * 1000,
            "completed": True,
            "name": "",
            "headline": "",
            "job_category": None,
            "job_position": None,
            "level": None,
        },
    )
    instance.get_cv(profile_details)
    instance.job_position = "Accounting"
    instance.job_category = "Accounting"
    instance.save()
    test_utils.assertEqual(
        instance.as_json(),
        {
            **instance.cv_data,
            "pk": result["id"],
            "modified": instance.modified.timestamp() * 1000,
            "completed": True,
            "name": "hello world (Accounting) Resume",
        },
    )


@pytest.mark.django_db(transaction=True)
def test_delete_cv(mock_auth, cv_instance):
    result, _ = cv_instance
    test_utils.assertEqual(models.CVProfile.objects.count(), 1)
    response = json_delete(
        f"/get-profile/{result.pk}",
        HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(models.CVProfile.objects.count(), 0)


@pytest.mark.django_db(transaction=True)
def test_delete_cv_and_return_list(mock_auth, cv_instance):
    result, _ = cv_instance
    test_utils.assertEqual(models.CVProfile.objects.count(), 1)
    response = json_delete(
        f"/get-profile/{result.pk}?all=true",
        HTTP_AUTHORIZATION="Bearer {}".format(token),
    )
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(len(response.json()["data"]), 0)


@pytest.mark.django_db(transaction=True)
def test_duplicate_cv(mock_auth, cv_instance):
    result, _ = cv_instance
    test_utils.assertEqual(models.CVProfile.objects.count(), 1)
    response = json_get(
        f"/duplicate-cv/{result.pk}",
        HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    result_response = response.json()
    # import pdb ; pdb.set_trace()
    test_utils.assertEqual(result_response["data"]["headline"],
                           "Systems Engineer Copy")
    test_utils.assertEqual(models.CVProfile.objects.count(), 2)


@pytest.mark.django_db(transaction=True)
def test_duplicate_cv_and_return_list(mock_auth, cv_instance):
    result, _ = cv_instance
    test_utils.assertEqual(models.CVProfile.objects.count(), 1)
    response = json_get(
        f"/duplicate-cv/{result.pk}?all=true",
        HTTP_AUTHORIZATION="Bearer {}".format(token),
    )
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(len(response.json()["data"]), 2)
    response = json_get(
        f"/my-cvs?all=true", HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(len(response.json()["data"]), 2)
    response = json_delete(
        f"/get-profile", HTTP_AUTHORIZATION="Bearer {}".format(token))
    test_utils.assertEqual(response.status_code, 200)
    test_utils.assertEqual(len(response.json()["data"]), 0)
