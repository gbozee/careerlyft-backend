import pytest

from django_app import models


@pytest.fixture
def job_position():
    _, _job_position = create_test_category_and_job_position()
    create_company_and_schools()
    create_related_jobs(_job_position)
    create_projects(_job_position)
    create_cvscript(_job_position)
    return _job_position


def create_test_category_and_job_position():
    job_category = models.JobCategory.objects.create(
        name="Engineering",
        keywords=["Hardware", "Software", "Full Stack"],
        software_skills=["Django", "React", "Vue", "HTML/CSS", "JavaScript", "Python"],
        industry_skills=["Software Design", "Analytics Development"],
    )
    _job_position = models.JobPosition.objects.create(
        name="Systems Engineering",
        keywords=["Hardware", "Software", "Full Stack"],
        software_skills=["Django", "React", "Vue"],
        industry_skills=["Software Design", "Analytics Development"],
    )
    _job_position.job_categories.add(job_category)
    return job_category, _job_position


def create_company_and_schools():
    for i in ["Careerlyft", "Tuteria Limited"]:
        models.CompanyAndSchool.objects.create(name=i, kind=2)

    for i in ["Chemical Engineering"]:
        models.CompanyAndSchool.objects.create(name=i, kind=3)

    for i in ["University of Cambridge"]:
        models.CompanyAndSchool.objects.create(name=i, kind=1)

    for i in ["Bachelor of Science - B.Sc"]:
        models.CompanyAndSchool.objects.create(name=i, kind=4)


def create_related_jobs(_job_position):
    models.Miscellaneous.objects.create(
        kind=models.Miscellaneous.JOB_POSITION,
        details={
            "name": _job_position.name,
            "related": ["Fullstack Software Developer", "Co-Founder, Lead Developer"],
            "groups": ["Frontend", "Backend"],
        },
    )


def create_projects(_job_position):
    models.Miscellaneous.objects.create(
        kind=models.Miscellaneous.PROJECT,
        details={
            "name": _job_position.name,
            "related": ["Fullstack Software Developer", "Co-Founder, Lead Developer"],
            "data": [
                {
                    "url": "",
                    "date": "",
                    "year": "",
                    "title": "Now-Python-Asgi",
                    "projectURL": "https://github.com/gbozee/now-python-asgi",
                    "company_name": "Github",
                    "projectAchievement": "<p>Python builder for ASGI applications on Zeit Now</p>",
                },
                {
                    "url": "",
                    "date": "",
                    "year": "",
                    "title": "Graphene Utils",
                    "projectURL": "https://github.com/gbozee/graphene-utils",
                    "company_name": "Github",
                    "projectAchievement": "<p>An helper library that makes working with the graphene library, in python, pleasant.</p>",
                },
            ],
        },
    )


def create_job_cvscripts(section, texts, **kwargs):
    """Helper method to create job cv scripts for specific sections"""
    cv_script2 = []
    for t in texts:
        cv_script2.append(
            models.JobCVScript(
                **{
                    "script": models.CVScript.objects.create(section=section, text=t),
                    **kwargs,
                }
            )
        )
    models.JobCVScript.objects.bulk_create(cv_script2)


def create_cvscript(value, field="job_position"):
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
    models.JobCVScript.objects.create(**{"script": cv_script, field: value})
    create_job_cvscripts(
        2,
        (
            "Built and maintains the micro-services used in the backend. ",
            "Provided support for multiple payment providers depending on client's country or preference. ",
            "Refactored the front end code-base, in order to speed up release times, when fixing bugs or deploying new features ",
            "Implemented a mono repository architecture for the different apps used in building the frontend ",
            "Built the payment processing platform, used in handling payment to tutors, which paid out over 1000 tutors in the last 3 years. ",
            "Mentored software engineers in developing projects using best practices. ",
            "Wrote and maintained the initial version of the back-end code base for 2 years before getting new team members. ",
            "Upgraded the underlying payment data layer to support group lessons, without introducing a breaking change or regression.&nbsp; ",
            "Rebuilt the application process, involved in placing a parent request, on the website. ",
        ),
        **{field: value},
    )
    create_job_cvscripts(
        3,
        (
            "2D Animation ",
            "Search Engine Optimization (SEO) ",
            "Concept Development ",
            "Test Driven Development ",
            "Construction ",
            "Plumbing Design ",
            "Database Design ",
            "Animal husbandry ",
            "Client Relationship: Meet with and maintain close relations with key clients ",
        ),
        **{field: value},
    )


def test_when_job_position_supports_cv_generation():
    pass


def as_ul(arr):
    arr_as_string = "".join([f"<li>{x}</li>" for x in arr])
    return f"<ul>{arr_as_string}</ul>"


@pytest.mark.django_db(transaction=True)
def test_relevant_generation_of_work_experience_for_job_position(
    job_position, generate_resume, mocker
):
    mock_highlights = mocker.patch("django_app.models.cvscript.randomizer")
    mock_highlights.side_effect = [
        [
            "Built and maintains the micro-services used in the backend.",
            "Provided support for multiple payment providers depending on client's country or preference.",
            "Refactored the front end code-base, in order to speed up release times, when fixing bugs or deploying new features",
            "Implemented a mono repository architecture for the different apps used in building the frontend.",
        ],
        [
            "Built the payment processing platform, used in handling payment to tutors, which paid out over 1000 tutors in the last 3 years.",
            "Mentored software engineers in developing projects using best practices.",
            "Wrote and maintained the initial version of the back-end code base for 2 years before getting new team members.",
            "Upgraded the underlying payment data layer to support group lessons, without introducing a breaking change or regression.&nbsp;",
            "Rebuilt the application process, involved in placing a parent request, on the website.",
        ],
    ]
    mock_company_and_related_positions = mocker.patch(
        "django_app.models.generic.randomizer"
    )
    mock_company_and_related_positions.side_effect = [
        ["Careerlyft", "Tuteria Limited"],
        ["Fullstack Software Developer", "Co-Founder, Lead Developer"],
    ]
    mock_durations = mocker.patch("django_app.models.cvscript.generate_start_year")
    mock_durations.side_effect = [
        {"endDate": "2019-3", "startDate": "2018-3", "currentlyWorking": True},
        {"startDate": "2014-9", "endDate": "2019-3", "currentlyWorking": False},
    ]
    result = generate_resume(
        job_position.name, "work_experience", child_params='(companies:["Care","Tut"])'
    )
    assert result == [
        {
            "endDate": "2019-3",
            "website": "https://careerlyft.com",
            "position": "Fullstack Software Developer",
            "startDate": "2018-3",
            "highlights": "<ul><li>Built and maintains the micro-services used in the backend.</li><li>Provided support for multiple payment providers depending on client's country or preference.</li><li>Refactored the front end code-base, in order to speed up release times, when fixing bugs or deploying new features</li><li>Implemented a mono repository architecture for the different apps used in building the frontend.</li></ul>",
            "isCollapsed": True,
            "company_name": "Careerlyft",
            "website_link": "https://careerlyft.com",
            "currentlyWorking": True,
        },
        {
            "endDate": "2019-3",
            "website": "https://tuteria-limited.com",
            "position": "Co-Founder, Lead Developer",
            "startDate": "2014-9",
            "highlights": "<ul><li>Built the payment processing platform, used in handling payment to tutors, which paid out over 1000 tutors in the last 3 years.</li><li>Mentored software engineers in developing projects using best practices.</li><li>Wrote and maintained the initial version of the back-end code base for 2 years before getting new team members.</li><li>Upgraded the underlying payment data layer to support group lessons, without introducing a breaking change or regression.&nbsp;</li><li>Rebuilt the application process, involved in placing a parent request, on the website.</li></ul>",
            "isCollapsed": True,
            "company_name": "Tuteria Limited",
            "website_link": "https://tuteria-limited.com",
            "currentlyWorking": False,
        },
    ]


@pytest.mark.django_db(transaction=True)
def test_relevant_generation_of_career_profile_for_job_position(
    job_position, generate_resume, mocker
):
    mock_career_profile = mocker.patch("django_app.models.cvscript.randomizer")
    mock_career_profile.return_value = (
        "Full-stack Web Developer responsible for developing"
        "solutions using Python, and JavaScript. Adept at developing "
        "server-side logic, ensuring high performance and responsiveness "
        "to requests from the front-end. Track record of writing high quality "
        "softwares that deliver direct impact on the bottom line of the company."
    )
    result = generate_resume(job_position.name, "mission_statement")
    assert result == (
        "Full-stack Web Developer responsible for developing"
        "solutions using Python, and JavaScript. Adept at developing "
        "server-side logic, ensuring high performance and responsiveness "
        "to requests from the front-end. Track record of writing high quality "
        "softwares that deliver direct impact on the bottom line of the company."
    )


@pytest.mark.django_db(transaction=True)
def test_relevant_industry_skills_for_job_position(
    job_position, generate_resume, mocker
):
    mock_industry_skills = mocker.patch("django_app.models.cvscript.randomizer")

    mock_industry_skills.side_effect = [
        [
            "Frontend Development",
            "Responsive Web Design",
            "Machine Learning",
            "Linux Administration",
            "Microservice Development",
        ]
    ]
    result = generate_resume(job_position.name, "industry_skills")
    assert result == [
        "Frontend Development",
        "Responsive Web Design",
        "Machine Learning",
        "Linux Administration",
        "Microservice Development",
    ]


@pytest.mark.django_db(transaction=True)
def test_relevant_software_skills_for_job_position(
    job_position, generate_resume, mocker
):
    mock_software_skills = mocker.patch("django_app.models.cvscript.randomizer")
    mock_grouper = mocker.patch("django_app.models.generic.grouper")

    mock_software_skills.side_effect = [
        ["Django", "SQLAlchemy", "AngularJS", "C#", "Python", "HTML/CSS", "Figma"],
        ["Django", "SQLAlchemy", "AngularJS", "C#", "Python", "HTML/CSS", "Figma"],
    ]
    mock_grouper.side_effect = [
        [["Django", "SQLAlchemy", "C#", "Python"], ["AngularJS", "HTML/CSS", "Figma"]]
    ]
    result = generate_resume(job_position.name, "software_skills")
    assert result == (
        ["Django", "SQLAlchemy", "AngularJS", "C#", "Python", "HTML/CSS", "Figma"]
    )
    result = generate_resume(
        job_position.name, "software_skills", child_params="(groups:true)"
    )
    assert sorted(result) == sorted(
        {
            "Backend": ["Django", "SQLAlchemy", "C#", "Python"],
            "Frontend": ["AngularJS", "HTML/CSS", "Figma"],
        }
    )


@pytest.mark.django_db(transaction=True)
def test_relevant_education_for_job_position(job_position, generate_resume, mocker):
    result = generate_resume(job_position.name, "education")
    assert result == [
        {
            "cgpa": "4.5",
            "course": "Chemical Engineering",
            "degree": {"long": "Bachelor of Science", "short": "B.Sc"},
            "showCgpa": False,
            "gradePoint": "5.00",
            "school_name": "University of Cambridge",
            "degree_level": "First Class",
            "completion_year": "2023",
        }
    ]


@pytest.mark.django_db(transaction=True)
def test_relevant_projects_for_job_position(job_position, generate_resume):
    result = generate_resume(job_position.name, "projects")
    assert result == (
        [
            {
                "url": "",
                "date": "",
                "year": "",
                "title": "Now-Python-Asgi",
                "projectURL": "https://github.com/gbozee/now-python-asgi",
                "company_name": "Github",
                "projectAchievement": "<p>Python builder for ASGI applications on Zeit Now</p>",
            },
            {
                "url": "",
                "date": "",
                "year": "",
                "title": "Graphene Utils",
                "projectURL": "https://github.com/gbozee/graphene-utils",
                "company_name": "Github",
                "projectAchievement": "<p>An helper library that makes working with the graphene library, in python, pleasant.</p>",
            },
        ]
    )


@pytest.mark.django_db(transaction=True)
def test_get_list_of_supported_job_positions(supported_job_positions, job_position):
    models.Miscellaneous.objects.create(
        kind=models.Miscellaneous.JOB_POSITION,
        details={
            "name": "Accountant",
            "related": ["Banker", "President"],
            "groups": ["Frontend", "Backend"],
        },
    )
    result = supported_job_positions()
    assert sorted(result) == sorted(
        [
            "Systems Engineering",
            "Fullstack Software Developer",
            "Co-Founder, Lead Developer",
            "Accountant",
            "Banker",
            "President",
        ]
    )

