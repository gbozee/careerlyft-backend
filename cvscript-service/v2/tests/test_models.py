import pytest
from django_app import models
import typing

@pytest.mark.django_db(transaction=True)
def test_mission_statement(
    cv_utils: typing.Tuple[typing.Any, typing.Any],
    create_models: typing.Tuple[models.JobCategory, models.JobPosition],
):
    mock_rand, mock_rand_choice = cv_utils
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
        script=cv_script, job_position=job_position
    )
    assert job_cv_script.script_content == (
        "Organized, responsible, and driven "
        f"{job_position.name} with 5+ years of experience "
        "in fast-moving environments. Track record of leading human "
        "resources teams to Django business solutions that are on "
        "Software Design, Analytics Development"
        "time and to budget. Ability to overhaul human resources "
        "procedures and processes to React more cost-efficient "
        "solutions to businesses. Hardware, Software and Full Stack"
    )


@pytest.mark.django_db(transaction=True)
def test_cv_script_creation_for_cover_letter(
    cv_utils: typing.Tuple[typing.Any, typing.Any],
    create_models: typing.Tuple[models.JobCategory, models.JobPosition],
):
    mock_rand, mock_rand_choice = cv_utils
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
        script=cv_script, job_position=job_position
    )
    assert job_cv_script.script_content == (
        "As a highly skilled and results-driven professional with X years "
        "of experience in quality assurance and validation—combined with a dedication "
        "to product quality excellence—I possess a breadth of knowledge and expertise "
        "that will allow me to contribute toward the success of your company."
    )
