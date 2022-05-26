from run import app
import pytest
from starlette.testclient import TestClient
from django_app import models

@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def generate_resume(graphql_call):
    def _generate_resume(job_position, field, child_params=""):
        params = [{"type": "String!", "value": job_position, "field": "job_position"}]
        result = graphql_call(
            mutationName="get_resume",
            params=params,
            fields=f"{field}{child_params}",
            headers=None,
        )
        if result:
            return result[field]

    return _generate_resume


@pytest.fixture
def supported_job_positions(graphql_call):
    def _supported_job_positions():
        result = graphql_call(
            mutationName="supported_job_positions", params=[], fields="", headers=None
        )
        return result

    return _supported_job_positions



@pytest.fixture
def create_models():
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


@pytest.fixture
def cv_utils(mocker):
    mock_rand = mocker.patch("cv_utils.get_rand")
    mock_rand_choice = mocker.patch("cv_utils.get_choices")
    mock_rand.return_value = 5
    mock_rand_choice.side_effect = [
        ["Django", "React"],
        ["Hardware", "Software", "Full Stack"],
        ["Software Design", "Analytics Development"],
    ]
    return mock_rand, mock_rand_choice



from cv_utils.tests import *
