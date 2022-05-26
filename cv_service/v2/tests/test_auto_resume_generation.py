import pytest
from registration_service.models import CVProfile


@pytest.fixture
def sample_response_cv():
    return {
        "work_experience": [
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
        ],
        "mission_statement": (
            "Full-stack Web Developer responsible for developing"
            "solutions using Python, and JavaScript. Adept at developing "
            "server-side logic, ensuring high performance and responsiveness "
            "to requests from the front-end. Track record of writing high quality "
            "softwares that deliver direct impact on the bottom line of the company."
        ),
        "industry_skills": [
            "Frontend Development",
            "Responsive Web Design",
            "Machine Learning",
            "Linux Administration",
            "Microservice Development",
        ],
        "software_skills": [
            "Django",
            "SQLAlchemy",
            "AngularJS",
            "C#",
            "Python",
            "HTML/CSS",
            "Figma",
        ],
        "education": [
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
        ],
        "projects": [
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
    }


def test_generate_user_resume():
    pass


def test_build_resume_function(sample_response_cv):
    result = CVProfile.build_user_resume(sample_response_cv)
    assert result == {
        "mission_statement": {
            "body": (
                "Full-stack Web Developer responsible for developing"
                "solutions using Python, and JavaScript. Adept at developing "
                "server-side logic, ensuring high performance and responsiveness "
                "to requests from the front-end. Track record of writing high quality "
                "softwares that deliver direct impact on the bottom line of the company."
            ),
            "heading": "Career Profile",
        },
        "work_experience": {
            "body": [
                {
                    "endDate": "2019-3",
                    "website": "https://careerlyft.com",
                    "position": "Fullstack Software Developer",
                    "startDate": "2018-3",
                    "highlights": "<ul><li>Built and maintains the micro-services used in the backend.</li><li>Provided support for multiple payment providers depending on client's country or preference.</li><li>Refactored the front end code-base, in order to speed up release times, when fixing bugs or deploying new features</li><li>Implemented a mono repository architecture for the different apps used in building the frontend.</li></ul>",
                    "company_name": "Careerlyft",
                    "website_link": "https://careerlyft.com",
                    "currentlyWorking": True,
                    "duration": "2018-2019",
                },
                {
                    "endDate": "2019-3",
                    "website": "https://tuteria-limited.com",
                    "position": "Co-Founder, Lead Developer",
                    "startDate": "2014-9",
                    "highlights": "<ul><li>Built the payment processing platform, used in handling payment to tutors, which paid out over 1000 tutors in the last 3 years.</li><li>Mentored software engineers in developing projects using best practices.</li><li>Wrote and maintained the initial version of the back-end code base for 2 years before getting new team members.</li><li>Upgraded the underlying payment data layer to support group lessons, without introducing a breaking change or regression.&nbsp;</li><li>Rebuilt the application process, involved in placing a parent request, on the website.</li></ul>",
                    "company_name": "Tuteria Limited",
                    "website_link": "https://tuteria-limited.com",
                    "currentlyWorking": False,
                    "duration": "2014-2019",
                },
            ],
            "heading": "Work Experience",
        },
        "industry_skills": {
            "body": [
                "Frontend Development",
                "Responsive Web Design",
                "Machine Learning",
                "Linux Administration",
                "Microservice Development",
            ],
            "heading": "Industry Expertise",
        },
        "software_skills": {
            "body": [
                {
                    "title": "All Softwares",
                    "softwares": [
                        "Django",
                        "SQLAlchemy",
                        "AngularJS",
                        "C#",
                        "Python",
                        "HTML/CSS",
                        "Figma",
                    ],
                }
            ],
            "heading": "Software Skills",
        },
        "education": {
            "body": [
                {
                    "cgpa": "4.5",
                    "course": "Chemical Engineering",
                    "degree": "Bachelor of Science",
                    "showCgpa": False,
                    "gradePoint": "5.00",
                    "school_name": "University of Cambridge",
                    "degree_level": "First Class",
                    "completion_year": "2023",
                }
            ],
            "heading": "Education",
        },
        "projects": {
            "body": [
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
            "heading": "Projects",
        },
    }
