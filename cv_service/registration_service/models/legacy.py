import re
from django.db import models
from .fields import TimeStampedModel
from django.contrib.postgres.fields import JSONField
import requests
from django.conf import settings


def clean_work_experiences(html_ul):
    regex = re.compile("<.*?>|↵")
    result = [x for x in regex.split(html_ul) if x]
    return result


def clean_softwares(data):
    aa = [o for y in data for o in y["softwares"]]
    return aa


def clean_industry_skills(x):
    if type(x) == dict:
        return x.get("title")
    return x


class CVProfileQuerySet(models.QuerySet):
    def get_cv_scripts(self, kind=None, job_position=None, job_category=None):
        instances = self.all()
        if job_position:
            instances = instances.filter(job_position__iexact=job_position)
        if job_category:
            instances = instances.filter(job_category__iexact=job_category)
        results = [x.as_json() for x in instances]
        options = {
            "mission_statement": lambda x: x["body"] if x else "",
            "work_experience": lambda x: [
                a
                for q in [
                    clean_work_experiences(o.get("highlights"))
                    for o in x["body"]
                    if x and o.get("highlights")
                ]
                for a in q
            ],
            "industry_skills": lambda x: x["body"] if x else [],
            "software_skills": lambda x: clean_softwares(x["body"]) if x else [],
            "job_position": lambda x: x,
            "job_category": lambda x: x,
        }
        no_body = [x.get(kind) for x in results]
        data = [options[kind](x) for x in no_body]
        clean_func = {
            "mission_statement": lambda x: x,
            "work_experience": lambda x: [a for o in x for a in o],
            "industry_skills": lambda x: [
                u for u in [clean_industry_skills(a) for o in x for a in o] if u
            ],
            "software_skills": lambda x: [a for o in x for a in o],
            "job_position": lambda x: x,
            "job_category": lambda x: x,
        }
        data = clean_func[kind](data)
        data = [x for x in data if x.strip() not in ["", "\n"]]
        return {"result": list(set(data))}


class CVProfile(TimeStampedModel):
    mission_statement = models.TextField(blank=True)
    user_id = models.IntegerField(null=True, blank=True)
    work_experiences = JSONField(null=True)
    industry_skills = JSONField(null=True)
    softwares = JSONField(null=True)
    certifications = JSONField(null=True)
    educations = JSONField(null=True)
    trainings = JSONField(null=True)
    headline = models.CharField(blank=True, max_length=200)
    completed = models.BooleanField(default=False)
    thumbnail = models.TextField(blank=True, null=True)
    job_position = models.CharField(max_length=70, null=True, blank=True)
    job_category = models.CharField(max_length=70, null=True, blank=True)
    cv_data = JSONField(null=True)
    level = models.CharField(blank=True, null=True, max_length=200)
    customer = models.ForeignKey(
        "registration_service.AgentCustomer",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    objects = CVProfileQuerySet.as_manager()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.user_id}>"

    @classmethod
    def get_uncompleted_instance(cls, user_id=None):
        if not user_id:
            return None
        return cls.objects.filter(user_id=user_id, completed=False).first()

    @classmethod
    def get_last_profile(cls, user_id, cv_id=None, personal_info=None):
        if cv_id:
            instance = cls.objects.filter(user_id=user_id, pk=cv_id).first()
            if not instance:
                return None
        else:
            instance = cls.get_uncompleted_instance(user_id=user_id)
            if not instance:
                return {}
        if instance.cv_data:
            instance.rebuild_as_json()
        return instance.as_json(personal_info=personal_info)

    @classmethod
    def get_cv_by_id(cls, cv_id):
        instance = cls.objects.filter(pk=cv_id).first()
        if instance:
            as_json = instance.as_json()
            user_id = instance.user_id
            if instance.customer:
                user_id = instance.customer_id
            return user_id, as_json
        return None

    def as_json(self, personal_info=None):
        result = self.cv_data or {}
        result["pk"] = self.pk
        result["modified"] = self.modified.timestamp() * 1000
        result["completed"] = self.completed
        result["name"] = result.get("name") or self.compose_name()
        result["job_position"] = self.job_position
        result["job_category"] = self.job_category
        result["level"] = self.level
        if result.get("personal_info"):
            personal_info = result["personal_info"]
            if not personal_info.get("headline"):
                personal_info["headline"] = self.headline
                result["personal_info"] = personal_info

        if self.customer:
            old_info = result.get("personal_info") or {}
            old_headline = old_info.pop("headline", None)
            personal_info = {
                **self.customer.as_json,
                "id": self.customer.pk,
                "headline": self.headline,
                **old_info,
            }
            result["customer_id"] = self.customer.pk
            result["personal_info"] = personal_info
        result["headline"] = self.headline
        return result

    def rebuild_as_json(self):
        result = self.as_json()
        data = {}
        for key in [
            "work_experience",
            "education",
            "software_skills",
            "industry_skills",
            "mission_statement",
            "certifications",
        ]:
            data[key] = result.get(key)
        work_experience = data["work_experience"] or {"body": []}
        if len(work_experience) == 0 or not data["work_experience"]:
            self.get_cv(result.get("personal_info"))

    def compose_name(self):
        if self.customer:
            personal_info = self.customer.as_json
        else:
            personal_info = (self.cv_data or {}).get("personal_info", {})
        if self.job_position and personal_info.get("first_name"):
            first_name = personal_info["first_name"]
            last_name = personal_info["last_name"]
            return f"{first_name} {last_name} ({self.job_position}) Resume"
        return ""

    def generate_headline(self):
        return self.headline

    def mission_statement_display(self):
        return mission_statement_display(self.mission_statement)

    def work_experience_display(self):
        return work_experience_display(self.work_experiences)

    def education_display(self):
        return education_display(self.educations)

    def industry_skills_display(self):
        return industry_skills_display(self.industry_skills)

    def software_skills_display(self):
        return software_skills_display(self.softwares)

    def awards_display(self):
        award_d = self.certifications or []

        return {
            "heading": "Certifications",
            "body": [
                work_experience_transform(x, kind="certifications") for x in award_d
            ],
        }

    def get_cv(self, personal_info):
        personal_info = personal_info or {}
        self.cv_data = {
            "personal_info": {
                **personal_info,
                "headline": self.generate_headline(),
                "social_link_url": personal_info.get("social_link_url"),
            },
            "mission_statement": self.mission_statement_display(),
            "work_experience": self.work_experience_display(),
            "training": [],
            "industry_skills": self.industry_skills_display(),
            "software_skills": self.software_skills_display(),
            "education": self.education_display(),
            "certifications": self.awards_display(),
        }
        self.save()
        return self.cv_data

    @classmethod
    def build_user_resume(cls, data):
        return {
            "mission_statement": mission_statement_display(data["mission_statement"]),
            "work_experience": work_experience_display(data["work_experience"]),
            "industry_skills": industry_skills_display(data["industry_skills"]),
            "software_skills": software_skills_display(data["software_skills"]),
            "education": education_display(data["education"]),
            "projects": project_display(data.get("projects"))
            # "certifications": self.awards_display(),
        }

    @classmethod
    def save_cv_instance(cls, cv_id, user_id=None, data=None, agent_id=None):
        if user_id:
            instance = cls.objects.filter(pk=cv_id, user_id=user_id).first()
        else:
            instance = cls.objects.filter(pk=cv_id, customer__agent_id=agent_id).first()
        if instance:
            headline = data.get("headline")
            job_position = data.get("job_position")
            if headline:
                instance.headline = headline
            if job_position:
                instance.job_position = job_position
            instance.cv_data = data
            instance.save()
            return instance.as_json()

    @classmethod
    def delete_cv(cls, cv_id, user_id, all=None):
        cls.objects.filter(pk=cv_id, user_id=user_id).delete()

    @classmethod
    def duplicate_cv(
        cls, cv_id, user_id=None, job_position=None, job_category=None, agent_id=None
    ):
        if user_id:
            instance = cls.objects.filter(pk=cv_id, user_id=user_id)
        else:
            instance = cls.objects.filter(pk=cv_id, customer__agent_id=agent_id)
        values = [
            "mission_statement",
            "work_experiences",
            "industry_skills",
            "softwares",
            "certifications",
            "educations",
            "trainings",
            "headline",
            "cv_data",
            "job_position",
            "level",
            "job_category",
            "completed",
        ]
        if user_id:
            values.append("user_id")
        else:
            values.append("customer_id")
        instance = instance.values(*values).first()
        position = instance.pop("job_position")
        category = instance.pop("job_category")
        headline = f"{instance.pop('headline')} Copy"
        position = job_position or position
        category = job_category or category
        new_instance = cls(
            headline=headline, job_position=position, job_category=category, **instance
        )
        new_instance.save()
        return {"pk": new_instance.pk, **new_instance.rebuild_and_json()}

    def rebuild_and_json(self):
        self.rebuild_as_json()
        return self.as_json()

    @classmethod
    def all_user_cvs(cls, user_id=None, agent_id=None):
        if user_id:
            instances = cls.objects.filter(user_id=user_id)
        else:
            instances = cls.objects.filter(customer__agent_id=agent_id)
        return [x.rebuild_and_json() for x in instances.order_by("-modified")]

    @classmethod
    def save_thumbnail(cls, cv_id, image):
        cls.objects.filter(pk=cv_id).update(thumbnail=image)

    def download_cv(self):
        defaults = self.cv_data.get("settings") or {}
        cvData = self.cv_data.get("pages")
        userData = self.cv_data or {}
        template = defaults.get("name")
        response = requests.post(
            f"{settings.PDF_SERVICE}/api/generate-asset",
            json={
                "defaults": defaults,
                "cvData": cvData,
                "userData": userData,
                "template": template,
            },
        )
        if response.status_code == 200:
            bty = BytesIO(response.content)
            return FileWrapper(bty)
        return


def work_experience_transform(x, kind="work_experience"):
    if kind == "certifications":
        return {
            "title": x["name"],
            "company": x["organization"],
            "date": x["yearOfCompletion"],
            "yearOfCompletion": x["yearOfCompletion"],
        }
    if kind == "projects":
        return x
    if kind == "education":
        deg = x.get("degree")
        is_dict = False
        if type(deg) == dict:
            degree = deg["long"]
            is_dict = True
        else:
            degree = x.get("degree", "-").split("-")
        resulsts = {
            "cgpa": x.get("cgpa"),
            "course": x.get("course"),
            # might not exist,
            "degree": degree[1].strip() if len(degree) > 1 else degree[0],
            "gradePoint": x.get("gradePoint"),
            "school_name": x.get("school_name") or x.get("school"),
            "showCgpa": x.get("showCgpa", False),
            "completion_year": x.get("completion_year") or x.get("yearOfCompletion"),
        }
        if is_dict:
            resulsts["degree"] = degree
        if x.get("degree_level"):
            resulsts["degree_level"] = x.get("degree_level")

        return resulsts
    fields = ["start_date", "end_date", "name", "role", "currently_work"]
    actual = ["startDate", "endDate", "company_name", "position", "currentlyWorking"]
    for i, j in enumerate(fields):
        if not x.get(j):
            x[j] = x.get(actual[i])
    duration = x["start_date"].split("-")[0]
    if x.get("end_date"):
        duration = f"{duration}-{x['end_date'].split('-')[0]}"
    else:
        duration = f"{duration}-Current"
    result = {
        "company_name": x["name"],
        "position": x["role"],
        "startDate": x["start_date"],
        "endDate": x.get("end_date", ""),
        "highlights": x.get("highlights", ""),
        "currentlyWorking": x.get("currently_work", False) or False,
        "duration": duration,
    }
    for u in ["website", "website_link"]:
        if x.get(u):
            result[u] = x[u]
    return result


def generate_headline(headline):
    return headline


def mission_statement_display(mission_statement):
    return {"heading": "Career Profile", "body": mission_statement}


def work_experience_display(work_experiences):
    w_e = work_experiences or []
    return {
        "heading": "Work Experience",
        "body": [work_experience_transform(x) for x in w_e],
    }


def education_display(educations):
    education_d = educations or []
    return {
        "heading": "Education",
        "body": [work_experience_transform(x, kind="education") for x in education_d],
    }


def industry_skills_display(industry_skills):
    return {"heading": "Industry Expertise", "body": industry_skills or []}


def software_skills_display(softwares):
    return {
        "heading": "Software Skills",
        "body": [{"title": "All Softwares", "softwares": softwares or []}],
    }


def project_display(projects):
    p_ro = projects or []
    return {
        "heading": "Projects",
        "body": [work_experience_transform(x, kind="projects") for x in p_ro],
    }
