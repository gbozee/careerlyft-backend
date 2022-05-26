import re
import typing
import itertools
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils.functional import cached_property
from django.db.models import Q
import random
from cv_utils import CVScriptModelMixin, JobCVScriptModelMixin
from cv_utils.utils import classproperty
from django.template.defaultfilters import slugify
from django_app.utils import randomizer


class ModelMixin(object):
    """Mixin object to set related class properties"""

    @classproperty
    def s_objects(cls):
        return cls.objects

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.pk}>"


class Job(ModelMixin, models.Model):
    name = models.CharField(max_length=200, null=True, db_index=True)
    keywords = ArrayField(models.CharField(max_length=200, blank=True), null=True)
    software_skills = ArrayField(
        models.CharField(max_length=200, blank=True), null=True
    )
    industry_skills = ArrayField(
        models.CharField(max_length=200, blank=True), null=True
    )

    class Meta:
        abstract = True

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"

    @classmethod
    def get_arrayfield_value(cls, field, job_position=None):
        jps = []
        if job_position:
            jps = job_position.split(",")
        # if not job_position:
        #     return []
        if len(jps):
            name_filter = Q()
            for name in jps:
                name_filter |= Q(name__icontains=name)
            result = cls.objects.filter(name_filter)
            result = result.values_list(field, flat=True)
            result = itertools.chain(
                *[o for o in result if o]
            )  # flatten out the list of list
            return list(set(result))
        return []


class JobCategory(Job):
    @classmethod
    def get_all_categories(cls, *args):
        return cls.objects.values(*args)


class JobPosition(Job, ModelMixin):
    job_categories = models.ManyToManyField(JobCategory)

    @classmethod
    def get_positions(cls, job_category=None, search_param=None):
        if search_param:
            if len(search_param) < 3:
                return []
        JobPositionCategory = cls.job_categories.through
        queryset = JobPositionCategory.objects.all()
        if job_category:
            queryset = queryset.filter(jobcategory__name__iexact=job_category)
        if search_param:
            queryset = queryset.filter(jobposition__name__icontains=search_param)
            if not queryset.exists():
                from django_app.models import MissingRecord

                MissingRecord.objects.create(
                    kind=MissingRecord.JOB_POSITION, name=search_param
                )
        return queryset.annotate(name=models.F("jobposition__name")).values("name")

    @classmethod
    def get_skills(cls, job_position=None, randomize=False) -> typing.List[str]:
        default_result = cls.get_arrayfield_value("software_skills", job_position)
        jps = cls.s_objects.filter(name__icontains=job_position).first()
        cat_result = []
        if jps:
            categories = jps.job_categories.values_list("name", flat=True)
            cat_result = JobCategory.get_arrayfield_value(
                "software_skills", ",".join(categories)
            )
        new_list = default_result + cat_result
        return list(set(new_list))

    @classmethod
    def get_industry_skills(cls, job_position=None, job_positions=None):
        return cls.get_arrayfield_value("industry_skills", job_position)

    @classmethod
    def get_job_categories(cls, job_position):
        job = cls.objects.filter(name__istartswith=job_position).first()
        if job:
            return job.job_categories.values("name")
        return []

    def generate_career_profile(self):
        result = JobCVScript.randomize_cvscript("mission-statement", self.name, 1)
        return result

    def generate_industry_skills(self, count=3):
        data = JobCVScript.randomize_cvscript("industry-skills", self.name, count)
        return data

    def generate_software_skills(self, group=False, count=3):
        from .generic import Miscellaneous

        skills = JobPosition.get_skills(self.name)
        r_skills = randomizer(skills, count)
        if not group:
            return r_skills
        groupings = Miscellaneous.create_software_groupings(self.name, r_skills)
        return groupings

    def generate_educations(self, count=1):
        from .generic import CompanyAndSchool

        courses = CompanyAndSchool.courses_by_role(self.name, random=True, count=count)
        degrees = CompanyAndSchool.degrees_by_role(self.name, random=True, count=count)
        schools = CompanyAndSchool.schools_by_role(self.name, random=True, count=count)
        result = [
            {
                "cgpa": "4.5",
                "course": courses[x],
                "degree": degrees[x],
                "showCgpa": False,
                "gradePoint": "5.00",
                "school_name": schools[x],
                "degree_level": "First Class",
                "completion_year": "2023",
            }
            for x in range(count)
        ]
        return result

    def generate_projects(self):
        from .generic import Miscellaneous

        projects = Miscellaneous.related_projects(self.name)
        return projects

    def generate_work_experiences(self, company_names: typing.List[str], count=1):
        from .generic import CompanyAndSchool, Miscellaneous

        companies = CompanyAndSchool.companies_by_industry(
            company_names, random=True, count=count
        )
        job_positions = Miscellaneous.related_job_positions(
            self.name, random=True, count=count
        )
        company_website = [f"https://{slugify(c)}.com" for c in companies]
        result = [
            {
                **generate_start_year(),
                "website": company_website[x],
                "position": job_positions[x],
                "highlights": as_ul(
                    JobCVScript.randomize_cvscript("work-achievement", self.name, 4)
                ),
                "isCollapsed": True,
                "company_name": companies[x],
                "website_link": company_website[x],
            }
            for x in range(count)
        ]
        return result


def generate_start_year():
    start_year = random.choice(range(2016, 2020))
    start_month = random.choice(range(12))
    return {
        "endDate": f"{start_year+1}-{start_month}",
        "startDate": f"{start_year}-{start_month}",
        "currentlyWorking": random.choice([True, False]),
    }


class CVScript(models.Model, ModelMixin, CVScriptModelMixin):
    SECTION_CHOICES = (
        (1, "Mission Statement"),
        (2, "Work Achievement"),
        (3, "Industry Skills"),
        (4, "Cover Letter"),
    )
    text = models.TextField()
    section = models.IntegerField(choices=SECTION_CHOICES, default=1)

    def __repr__(self):
        return f"<CVScript: {self.text}>"


def as_ul(arr: typing.List[str]):
    arr_as_string = "".join([f"<li>{x}</li>" for x in arr])
    return f"<ul>{arr_as_string}</ul>"


class JobCVScript(JobCVScriptModelMixin, models.Model, ModelMixin):
    script = models.ForeignKey(CVScript, on_delete=models.SET_NULL, null=True)
    job_position = models.ForeignKey(JobPosition, null=True, on_delete=models.SET_NULL)
    job_category = models.ForeignKey(JobCategory, null=True, on_delete=models.SET_NULL)
    level = models.CharField(max_length=200, null=True, db_index=True)
    # s_objects = models.Manager()
    klass = JobPosition

    @classmethod
    def randomize_cvscript(cls, section, name, count=1):
        scripts = cls.get_scripts(section, name)
        result = randomizer(scripts, count)
        return result

