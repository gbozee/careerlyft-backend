import pytest
from registration_service.models import CVProfile
from cv_utils.client import get_cvscript


def create_resumes(user_id, **kwargs):
    data = {
        "mission_statement": "This is the mission statement for the year",
        "work_experiences": [
            {
                "name": "University of Olodo",
                "role": "systems Engineer",
                "start_date": "2017-10",
                "end_date": "2018-2",
            },
            {
                "name": "Compal Electronics",
                "role": "Frontend Engineer",
                "highlights": "<ul>↵<li>Generated positive cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                "start_date": "2017-06",
                "currently_work": True,
            },
        ],
        "headline": "Systems Engineer",
        "educations": [
            {
                "cgpa": "4.80",
                "course": "Music Psychology",
                "degree": "Bachelor of Music - BMus",
                "degreeLevel": "Second class, Upper",
                "gradePoint": "5.00",
                "school": "University of North Bengal",
                "showCgpa": True,
                "yearOfCompletion": "2015",
            }
        ],
        "industry_skills": ["Installation", "Designing"],
        "softwares": ["Photoshop", "Invision"],
        "certifications": [
            {
                "name": "Cisco certified professional",
                "organization": "Cisco Systems, Inc.",
                "yearOfCompletion": "2016",
            }
        ],
        "completed": True,
        "job_position": "Frontend Developer",
        "job_category": "IT and Software",
    }

    data2 = {
        "mission_statement": "This is the second mission statement for the year",
        "work_experiences": [
            {
                "name": "University of Olodo",
                "role": "systems Engineer",
                "start_date": "2017-10",
                "highlights": "<ul>↵<li>Negative positive cash flow in first fou…tering $545,000 in sales in year one.</li><li>Region positive cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                "end_date": "2018-2",
            },
            {
                "name": "Compal Electronics",
                "role": "Frontend Engineer",
                "highlights": "<ul>↵<li>Generated sample cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                "start_date": "2017-06",
                "currently_work": True,
            },
        ],
        "headline": "Systems Engineer",
        "educations": [
            {
                "cgpa": "4.80",
                "course": "Music Psychology",
                "degree": "Bachelor of Music - BMus",
                "degreeLevel": "Second class, Upper",
                "gradePoint": "5.00",
                "school": "University of North Bengal",
                "showCgpa": True,
                "yearOfCompletion": "2015",
            }
        ],
        "industry_skills": ["Backend Development", "Designing"],
        "softwares": ["Django", "Flask"],
        "certifications": [
            {
                "name": "Cisco certified professional",
                "organization": "Cisco Systems, Inc.",
                "yearOfCompletion": "2016",
            }
        ],
        "completed": True,
        "job_position": "Backend Developer",
        "job_category": "IT and Software",
    }
    result = CVProfile.objects.create(**data, user_id=user_id, **kwargs)
    result.rebuild_as_json()
    result = CVProfile.objects.create(**data2, user_id=user_id, **kwargs)
    result.rebuild_as_json()


@pytest.mark.django_db(transaction=True)
def test_cvscript_for_mission_statement(user_cvscripts_call):
    create_resumes(1)
    result = user_cvscripts_call("mission_statement", user_id=1)
    data = result["result"]
    assert sorted(data) == sorted(
        [
            "This is the mission statement for the year",
            "This is the second mission statement for the year",
        ]
    )
    # get mission_statement for specific role
    result = user_cvscripts_call(
        "mission_statement", user_id=1, job_position="Frontend Developer"
    )
    assert sorted(result["result"]) == sorted(
        ["This is the mission statement for the year"]
    )


@pytest.mark.django_db(transaction=True)
def test_cv_script_for_work_experience(user_cvscripts_call):
    create_resumes(1)
    result = user_cvscripts_call("work_experience", user_id=1)
    data = result
    assert sorted(data["result"]) == sorted(
        [
            "Negative positive cash flow in first fou…tering $545,000 in sales in year one.",
            "Generated positive cash flow in first fou…tering $545,000 in sales in year one.",
            "Generated sample cash flow in first fou…tering $545,000 in sales in year one.",
            "Region positive cash flow in first fou…tering $545,000 in sales in year one.",
        ]
    )


@pytest.mark.django_db(transaction=True)
def test_cv_scripts_for_industry_skills(user_cvscripts_call):
    create_resumes(1)
    result = user_cvscripts_call("industry_skills", user_id=1)
    data = result
    assert sorted(data["result"]) == sorted(
        ["Installation", "Designing", "Backend Development"]
    )


@pytest.mark.django_db(transaction=True)
def test_cv_scripts_for_software_skills(user_cvscripts_call):
    create_resumes(1)
    result = user_cvscripts_call("software_skills", user_id=1)
    data = result
    assert sorted(data["result"]) == sorted(
        ["Photoshop", "Invision", "Django", "Flask"]
    )


@pytest.mark.django_db(transaction=True)
def test_get_job_positions(user_cvscripts_call, client):
    create_resumes(1)
    result = user_cvscripts_call("job_position", user_id=1)
    assert sorted(result["result"]) == sorted(
        ["Frontend Developer", "Backend Developer"]
    )
    result = get_cvscript("job_position", client=client, user_id=1)
    assert sorted(result["result"]) == sorted(
        ["Frontend Developer", "Backend Developer"]
    )


@pytest.mark.django_db(transaction=True)
def test_shared_client_helper(client):
    create_resumes(1)
    response = get_cvscript("software_skills", client=client, user_id=1)
    result = response
    assert sorted(result["result"]) == sorted(
        ["Photoshop", "Invision", "Django", "Flask"]
    )
    result = get_cvscript(
        "software_skills", client=client, user_id=1, job_position="Frontend Developer"
    )
    assert sorted(result["result"]) == sorted(["Photoshop", "Invision"])
