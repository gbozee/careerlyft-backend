from typing import List
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.paginator import Paginator
from django.conf import settings
from functools import reduce
from django_app.utils import randomizer
from itertools import zip_longest


class Record(models.Model):
    SCHOOL = 1
    COMPANY = 2
    COURSE = 3
    DEGREE = 4
    JOB_POSITION = 5
    SOFTWARE = 6
    CERTIFICATION = 7
    AFFILIATION = 8
    CHOICES = (
        (SCHOOL, "Schools"),
        (COMPANY, "Companies"),
        (COURSE, "Courses"),
        (DEGREE, "Degrees"),
        (JOB_POSITION, "Job Positions"),
        (SOFTWARE, "Softwares"),
        (CERTIFICATION, "Certification"),
        (AFFILIATION, "Affiliations"),
    )
    name = models.CharField(max_length=200, null=True, db_index=True)
    kind = models.IntegerField(choices=CHOICES)

    class Meta:
        abstract = True


class CompanyAndSchool(Record):
    job_category = models.CharField(max_length=200, blank=True, null=True)

    def __repr__(self):
        return f"<CompanyAndSchool: {self.name}>"

    @classmethod
    def courses_by_role(cls, job_name: str, random=False, count=1):
        courses = cls.objects.filter(kind=cls.COURSE).values_list("name", flat=True)
        if random:
            return randomizer(courses, count)
        return courses

    @classmethod
    def degrees_by_role(cls, job_name: str, random=False, count=1):
        degrees = cls.objects.filter(kind=cls.DEGREE).values_list("name", flat=True)
        degrees = [named_degree(x) for x in degrees]
        if random:
            return randomizer(degrees, count)
        return degrees

    @classmethod
    def schools_by_role(cls, job_name: str, random=False, count=1):
        schools = cls.objects.filter(kind=cls.SCHOOL).values_list("name", flat=True)
        if random:
            return randomizer(schools, count)
        return schools

    @classmethod
    def companies_by_industry(
        cls, search_params: List[str], random=False, count=1
    ) -> List[str]:
        filters = reduce(
            lambda a, b: a | b,
            [models.Q(**{"name__icontains": x}) for x in search_params],
        )
        companies = (
            cls.objects.filter(kind=cls.COMPANY)
            .filter(filters)
            .values_list("name", flat=True)
        )
        if random:
            return randomizer(companies, count)

        return companies

    @classmethod
    def bulk_create_action(cls, kind, data):
        if kind in [cls.CERTIFICATION, cls.AFFILIATION]:
            new_data = [cls(kind=kind, **x) for x in data if x]
        else:
            new_data = [cls(kind=kind, name=x) for x in data if x]
        return cls.objects.bulk_create(new_data)

    @classmethod
    def get_queryset(cls, kind, search_param, per_page=25):

        options = {
            "degrees": [cls.DEGREE],
            "schools": [cls.SCHOOL],
            "courses": [cls.COURSE],
            "companies": [cls.COMPANY, cls.SCHOOL, cls.AFFILIATION],
        }
        found_kind = options.get(kind)
        if not found_kind or not search_param:
            return None
        if len(search_param) < 3 and found_kind[0] != cls.DEGREE:
            return (None,)
        filters = {"kind__in": found_kind, "name__icontains": search_param}
        result = cls.objects.filter(**filters).values_list("name", flat=True)
        if not result.exists():
            MissingRecord.objects.get_or_create(kind=found_kind[0], name=search_param)
        if found_kind == cls.DEGREE:
            result = [get_label_and_value(x) for x in result]
        paginator = Paginator(result, per_page)
        return paginator.page(1).object_list

    @classmethod
    def get_section(cls, section):
        result = cls.objects.filter(kind=section).values_list("name", flat=True)
        return list(result)


def get_label_and_value(x):
    result = x.split("-")
    if len(result) > 1:
        return {"name": result[0].strip(), "abv": result[1].strip()}
    return {"name": x, "abv": x}


class MissingRecord(Record):
    # job_category = models.CharField(max_length=200, db_index=True)

    def __repr__(self):
        return f"<Missing Record: {self.name}>"


class MiscellaneousQueryset(models.QuerySet):
    def get_result_for_job_position(self, job_name, kind=None):
        _kind = kind
        if not _kind:
            _kind = Miscellaneous.JOB_POSITION
        filters = models.Q(details__name__iexact=job_name) | models.Q(
            details__related__contains=job_name
        )
        return self.filter(kind=_kind).filter(filters)

    def roles_that_support_resume_generation(self):
        data = self.filter(kind=Miscellaneous.JOB_POSITION)
        result = []
        for i in data:
            for o in merge_skills(i):
                result.append(o)
        return list(set(result))


def merge_skills(result, job_name=None):
    details = result.details.get("related") or []
    name = result.details.get("name") or job_name
    details.append(name)
    return details


class Miscellaneous(models.Model):
    PROJECT = "project"
    JOB_POSITION = "jobs"
    kind = models.CharField(
        max_length=15, choices=((PROJECT, PROJECT), (JOB_POSITION, JOB_POSITION))
    )
    details = JSONField(blank=True)
    objects = MiscellaneousQueryset.as_manager()

    @classmethod
    def related_job_positions(cls, job_name: str, random=False, count=1):
        result = cls.objects.get_result_for_job_position(job_name).first()
        if result:
            details = merge_skills(result, job_name)

            # details = result.details.get("related") or []
            # name = result.details.get("name") or job_name
            # details.append(name)
            values = list(set([x for x in details if x != job_name]))
            if random:
                return randomizer(values, count)
            return values

        return []

    @classmethod
    def related_projects(cls, job_name: str):
        result = cls.objects.get_result_for_job_position(
            job_name, kind=cls.PROJECT
        ).first()
        if result:
            return result.details.get("data") or []
        return []

    @classmethod
    def create_software_groupings(cls, job_name: str, softwares: List[str]):
        result = cls.objects.get_result_for_job_position(job_name).first()
        if result:
            groups = result.details.get("groups") or []
            if len(groups) == 0:
                return softwares
            classifications = grouper(softwares, len(groups))
            data = {
                x: [o for o in classifications[i] if o] for i, x in enumerate(groups)
            }
            return data
        return softwares


def grouper(iterable, n, fillvalue=None):
    group_count = len(iterable) // n
    modulo = len(iterable) % n
    if modulo > 0:
        group_count += 1
    args = [iter(iterable)] * group_count
    result = [list(x) for x in zip_longest(*args, fillvalue=fillvalue)]
    # if modulo == 0:
    #     return result
    # result[0].append(iterable[-1])
    return result


def named_degree(degree: str):
    splitter = degree.split("-")
    if len(splitter) > 1:
        return {"long": splitter[0].strip(), "short": splitter[1].strip()}
    return {"long": splitter[0].strip(), "short": splitter[0][:4]}
