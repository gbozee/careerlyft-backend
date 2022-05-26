import pytest
from registration_service.models import CVProfile, AgentCustomer
from cv_utils.client import get_cvscript


def create_customers(agent_id):
    AgentCustomer.objects.bulk_create(
        [
            AgentCustomer(**x, agent_id=agent_id)
            for x in [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john@example.com",
                    "address": "Eleja Road ikeja",
                    "country": "Nigeria",
                    "phone": "(234) 80330022332",
                    "photo_url": "http://www.google.com",
                    "website": "http://facebook.com",
                },
                {
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@example.com",
                    "phone": "(234) 80330022432",
                    "country": "Nigeria",
                    "address": "Eleja Road ikeja",
                    "photo_url": "http://www.google.com",
                    "website": "http://facebook.com",
                },
            ]
        ]
    )
    return AgentCustomer.objects.first()


def create_resumes(customer):
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
    }
    result = CVProfile.objects.create(**data, customer=customer)
    result.rebuild_as_json()
    result = CVProfile.objects.create(**data2, customer=customer)
    result.rebuild_as_json()


@pytest.mark.django_db(transaction=True)
def test_cvscript_for_mission_statement(user_cvscripts_call, agent_data):
    customer = create_customers(agent_data["pk"])
    create_resumes(customer)
    result = user_cvscripts_call("mission_statement", token="100001")
    data = result["result"]
    assert sorted(data) == sorted(
        [
            "This is the mission statement for the year",
            "This is the second mission statement for the year",
        ]
    )


@pytest.mark.django_db(transaction=True)
def test_cv_script_for_work_experience(user_cvscripts_call, agent_data):
    customer = create_customers(agent_data["pk"])
    create_resumes(customer)
    result = user_cvscripts_call("work_experience", token="100001")
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
def test_cv_scripts_for_industry_skills(user_cvscripts_call, agent_data):
    customer = create_customers(agent_data["pk"])
    create_resumes(customer)
    result = user_cvscripts_call("industry_skills", token="100001")
    data = result
    assert sorted(data["result"]) == sorted(
        ["Installation", "Designing", "Backend Development"]
    )


@pytest.mark.django_db(transaction=True)
def test_cv_scripts_for_software_skills(user_cvscripts_call, agent_data):
    customer = create_customers(agent_data["pk"])
    create_resumes(customer)
    result = user_cvscripts_call("software_skills", token="100001")
    data = result
    assert sorted(data["result"]) == sorted(
        ["Photoshop", "Invision", "Django", "Flask"]
    )


@pytest.mark.django_db(transaction=True)
def test_shared_client_helper(client, agent_data, authorized):
    customer = create_customers(agent_data["pk"])
    token = "100001"
    auth = authorized(token)
    create_resumes(customer)
    response = get_cvscript(
        "software_skills", client=client, headers={"Authorization": f"Token {token}"}
    )
    result = response
    assert sorted(result["result"]) == sorted(
        ["Photoshop", "Invision", "Django", "Flask"]
    )

