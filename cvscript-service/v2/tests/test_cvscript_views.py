import pytest
import typing
from django.test import Client
from django_app import models


@pytest.mark.django_db(transaction=True)
def test_fetch_cv_scripts(
    client: Client,
    create_models: typing.Tuple[models.JobCategory, models.JobPosition],
    mocker,
):
    job_category, job_position = create_models
    cv_script = models.CVScript.objects.create(
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
    job_cv_script = models.JobCVScript.objects.create(
        script=cv_script, job_category=job_category
    )
    data = {"job-position": job_position.name, "job-category": job_category.name}
    response = client.get("/cv-scripts/mission-statement", params=data)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


@pytest.mark.django_db(transaction=True)
def test_fetch_cover_letter_scripts(
    client: Client, create_models: typing.Tuple[models.JobCategory, models.JobPosition]
):
    job_category, job_position = create_models
    cv_script = models.CVScript.objects.create(
        section=4,
        text=(
            "As a highly skilled and results-driven professional with X years "
            "of experience in quality assurance and validation—combined with a dedication "
            "to product quality excellence—I possess a breadth of knowledge and expertise "
            "that will allow me to contribute toward the success of your company."
        ),
    )
    job_cv_script = models.JobCVScript.objects.create(
        script=cv_script, job_category=job_category
    )
    data = {"job-position": job_position.name, "job-category": job_category.name}
    response = client.get("/cv-scripts/cover-letter", params=data)
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1
