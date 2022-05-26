from v2.agent_cv_service import AgentCustomer, CVProfile
import pytest


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
    result = CVProfile.objects.create(**data, customer=customer)
    return data, result


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


@pytest.mark.django_db(transaction=True)
def test_get_agent_resumes(agent_data, resumes_call):
    customer = create_customers(agent_data["pk"])
    data, _ = create_resumes(customer)
    result = resumes_call()
    first_result = result["data"][0]
    assert result["count"] == 1
    assert result["page"] == 1
    assert first_result["personal_info"] == {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "address": "Eleja Road ikeja",
        "country": "Nigeria",
        "phone": "(234) 80330022332",
        "photo_url": "http://www.google.com",
        "social_link_url": "http://facebook.com",
        "website": "http://facebook.com",
        "headline": "Systems Engineer",
        'id': customer.pk
    }
    assert first_result["mission_statement"] == {
        "heading": "Career Profile",
        "body": data["mission_statement"],
    }
    assert first_result["work_experience"] == {
        "heading": "Work Experience",
        "body": [
            {
                "company_name": "University of Olodo",
                "position": "systems Engineer",
                "startDate": "2017-10",
                "currentlyWorking": False,
                "endDate": "2018-2",
                "highlights": '',
                "duration": "2017-2018",
            },
            {
                "company_name": "Compal Electronics",
                "position": "Frontend Engineer",
                "startDate": "2017-06",
                "currentlyWorking": True,
                "endDate": None,
                "highlights": "<ul>↵<li>Generated positive cash flow in first fou…tering $545,000 in sales in year one.</li>↵</ul>↵",
                "duration": "2017-Current",
            },
        ],
    }


@pytest.mark.django_db(transaction=True)
def test_get_agent_customers(agent_data, customers_call):
    create_customers(agent_data["pk"])
    result = customers_call()
    all_customers = AgentCustomer.objects.filter(agent_id=agent_data["pk"])
    assert result == {
        "data": [
            {
                "first_name": x.first_name,
                "last_name": x.last_name,
                "email": x.email,
                "id": x.pk,
            }
            for x in all_customers
        ],
        "page": 1,
        "count": 2,
    }


@pytest.mark.django_db(transaction=True)
def test_get_agent_customer_when_not_authorized(customers_call):
    result = customers_call(None)
    assert "Invalid credentials" == result[0]["message"]


@pytest.mark.django_db(transaction=True)
def test_agent_create_new_customer(agent_data, customers_create):
    assert AgentCustomer.objects.count() == 0
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "address": "Eleja Road ikeja",
        "phone": "(234) 80330022332",
        "photo_url": "http://www.google.com",
        "website": "http://facebook.com",
        "dob": "1994-12-10",
    }
    result = customers_create(data=data)
    record = AgentCustomer.objects.first()
    assert result == {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "id": record.pk,
    }
    assert AgentCustomer.objects.count() == 1
    assert record.agent_id == agent_data["pk"]


@pytest.mark.django_db(transaction=True)
def test_agent_edit_customer(agent_data, customers_create):
    first_customer = create_customers(agent_data["pk"])
    assert first_customer.first_name == "John"
    assert AgentCustomer.objects.count() == 2
    result = customers_create(
        id=first_customer.pk, data={"first_name": "Judas", "email": "jude@example.com"}
    )
    assert result == {
        "first_name": "Judas",
        "last_name": "Doe",
        "email": "jude@example.com",
        "id": first_customer.pk,
    }
    assert AgentCustomer.objects.count() == 2
    assert AgentCustomer.objects.get(pk=first_customer.pk).first_name == "Judas"


@pytest.mark.django_db(transaction=True)
def test_agent_delete_customer(agent_data, customer_delete):
    first_customer = create_customers(agent_data["pk"])
    assert AgentCustomer.objects.count() == 2
    customer_delete(first_customer.pk)
    assert AgentCustomer.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_agent_add_new_resume(agent_data, resume_add):
    first_customer = create_customers(agent_data["pk"])
    assert CVProfile.objects.count() == 0
    result = resume_add(
        {
            "level": "Experienced",
            "job_category": "Marketing and Advertising",
            "job_position": "Digital Marketing",
            "headline": "Experienced, Digital Marketing",
            "customer_email": first_customer.email,
        }
    )
    assert CVProfile.objects.count() == 1
    assert result["level"] == "Experienced"
    assert result["customer_id"] == first_customer.pk
    assert result["job_position"] == "Digital Marketing"
    assert result["personal_info"] == {
        "id": first_customer.pk,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "address": "Eleja Road ikeja",
        "country": "Nigeria",
        "phone": "(234) 80330022332",
        "photo_url": "http://www.google.com",
        "social_link_url": "http://facebook.com",
        "website": "http://facebook.com",
        "headline": "Experienced, Digital Marketing",
    }


@pytest.mark.django_db(transaction=True)
def test_agent_delete_resume(agent_data, resume_delete):
    first_customer = create_customers(agent_data["pk"])
    _, data = create_resumes(first_customer)
    assert CVProfile.objects.count() == 1
    resume_delete(data.pk)
    assert CVProfile.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_agent_save_cv_data(agent_data, resume_save):
    first_customer = create_customers(agent_data["pk"])
    _, data = create_resumes(first_customer)
    json_data = data.rebuild_and_json()
    json_data['thumbnail'] = "http://www.google.com"
    json_data['headline'] = 'headline10'
    result = resume_save(json_data, data.pk)
    assert result['thumbnail'] == 'http://www.google.com'
    assert result['headline'] == 'headline10'
    assert result["personal_info"] == {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "address": "Eleja Road ikeja",
        "country": "Nigeria",
        "phone": "(234) 80330022332",
        "photo_url": "http://www.google.com",
        "social_link_url": "http://facebook.com",
        "website": "http://facebook.com",
        "headline": "headline10",
        'id': first_customer.pk
    }


@pytest.mark.django_db(transaction=True)
def test_agent_duplicate_resume(agent_data, resume_add):
    first_customer = create_customers(agent_data["pk"])
    raw_data, cv_record = create_resumes(first_customer)

    assert CVProfile.objects.count() == 1
    result = resume_add(resume_id=cv_record.pk)
    assert CVProfile.objects.count() == 2
    assert result["pk"] != cv_record.pk


@pytest.mark.django_db(transaction=True)
def test_agent_fetch_cv_detail(resume_fetch, agent_data):
    first_customer = create_customers(agent_data["pk"])
    raw_data, cv_record = create_resumes(first_customer)
    result = resume_fetch(cv_record.pk)
    assert result["personal_info"] == {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "address": "Eleja Road ikeja",
        "country": "Nigeria",
        "phone": "(234) 80330022332",
        "photo_url": "http://www.google.com",
        "social_link_url": "http://facebook.com",
        "website": "http://facebook.com",
        "headline": "Systems Engineer",
        "id": first_customer.pk,
    }


@pytest.mark.django_db(transaction=True)
def test_agent_fetch_when_token_not_passed(resume_fetch, agent_data):
    first_customer = create_customers(agent_data["pk"])
    raw_data, cv_record = create_resumes(first_customer)
    result = resume_fetch(cv_record.pk, token=None)
    assert result == {"msg": "data not found"}

