from django.db import models
from cv_utils.utils import classproperty
from cv_utils import CVScriptModelMixin, JobCVScriptModelMixin
import itertools
from django.db.models import F
from admin_service.utils import SharedMixin
from django.contrib.postgres.fields import JSONField

# Create your models here.


class CompanyAndSchool(models.Model, SharedMixin):
    name = models.CharField(max_length=200)
    kind = models.IntegerField()
    job_category = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "django_app_companyandschool"

    def __str__(self):
        return self.name


class Miscellaneous(models.Model, SharedMixin):
    PROJECT = "project"
    JOB_POSITION = "jobs"
    kind = models.CharField(
        max_length=15, choices=((PROJECT, PROJECT), (JOB_POSITION, JOB_POSITION))
    )
    details = JSONField(blank=True)

    def __str__(self):
        return f" {self.details['name']}-{self.kind}"

    class Meta:
        managed = False
        db_table = "django_app_miscellaneous"


class CVScript(models.Model, SharedMixin, CVScriptModelMixin):
    SECTION_CHOICES = (
        (1, "Mission Statement"),
        (2, "Work Achievement"),
        (3, "Industry Skills"),
    )

    text = models.TextField()
    section = models.IntegerField(choices=SECTION_CHOICES, default=1)

    class Meta:
        managed = False
        db_table = "django_app_cvscript"


class JobCategory(models.Model, SharedMixin):
    name = models.CharField(max_length=200)
    # This field type is a guess.
    industry_skills = models.TextField(blank=True, null=True)
    # This field type is a guess.
    keywords = models.TextField(blank=True, null=True)
    # This field type is a guess.
    software_skills = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "django_app_jobcategory"

    @property
    def as_json(self):
        instance = {}
        for key in ["id", "name", "keywords", "software_skills", "industry_skills"]:
            instance[key] = getattr(self, key)
        cv_scripts = DjangoAppJobcvscript.get_scripts(
            job_category_id=self.id, name=self.name
        )
        return {**instance, "cvscripts": cv_scripts}


class DjangoAppJobcvscript(models.Model, SharedMixin, JobCVScriptModelMixin):
    level = models.CharField(max_length=200, blank=True, null=True)
    job_category = models.ForeignKey(
        JobCategory, models.DO_NOTHING, blank=True, null=True
    )
    job_position = models.ForeignKey(
        "JobPosition",
        models.DO_NOTHING,
        blank=True,
        null=True,
        related_name="cvscripts",
    )
    script = models.ForeignKey(CVScript, models.DO_NOTHING, blank=True, null=True)

    @classproperty
    def klass(cls):
        return JobPosition

    @classmethod
    def get_scripts(cls, **kwargs):
        name = kwargs.pop("name", None)
        ids = cls.s_objects.filter(**kwargs).select_related("script")
        param = kwargs.get("job_position_id")
        callback = (
            lambda x: x.script_content
            if param
            else x.script_content_using_default(name)
        )
        cv_scripts = [
            {"text": callback(x), "section": x.script.get_section_display()}
            for x in ids
        ]
        return group(cv_scripts)

    class Meta:
        managed = False
        db_table = "django_app_jobcvscript"


class JobPosition(models.Model, SharedMixin):
    name = models.CharField(max_length=200)
    # This field type is a guess.
    keywords = models.TextField(blank=True, null=True)
    # This field type is a guess.
    software_skills = models.TextField(blank=True, null=True)
    # This field type is a guess.
    industry_skills = models.TextField(blank=True, null=True)
    job_categories = models.ManyToManyField(JobCategory)

    class Meta:
        managed = False
        db_table = "django_app_jobposition"

    @property
    def as_json(self):
        instance = {}
        for key in ["id", "name", "keywords", "software_skills", "industry_skills"]:
            instance[key] = getattr(self, key)
        categories = (
            JobPosition.job_categories.through.objects.using("services")
            .filter(jobposition_id=instance["id"])
            .annotate(name=F("jobcategory__name"))
            .annotate(cid=F("jobcategory__id"))
            .values("name", "cid")
        )
        cv_scripts = DjangoAppJobcvscript.get_scripts(job_position_id=instance["id"])
        return {**instance, "job_categories": list(categories), "cvscripts": cv_scripts}


class JobPositionAndCategories(models.Model, SharedMixin):
    jobposition = models.ForeignKey(JobPosition, models.DO_NOTHING)
    jobcategory = models.ForeignKey(JobCategory, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = "django_app_jobposition_job_categories"
        unique_together = (("jobposition", "jobcategory"),)


class MissingRecord(models.Model, SharedMixin):
    name = models.CharField(max_length=200)
    kind = models.IntegerField()

    class Meta:
        managed = False
        db_table = "django_app_missingrecord"


def group(data, keyfunc=lambda x: x["section"], key="text"):
    groups = []
    uniquekeys = []
    data = sorted(data, key=keyfunc)
    for k, g in itertools.groupby(data, keyfunc):
        groups.append(list(g))  # Store group iterator as a list
        uniquekeys.append(k)
    result = {}
    for i, o in enumerate(uniquekeys):
        result[o] = [x[key] for x in groups[i]]
    return result
