from admin_service.admin import admin, ServicesModelAdmin
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.utils.safestring import mark_safe

# Register your models here.
from .models import (
    CVScript,
    JobCategory,
    JobPosition,
    DjangoAppJobcvscript,
    CompanyAndSchool,
    Miscellaneous,
)


@admin.register(Miscellaneous)
class MiscellaneousAdmin(ServicesModelAdmin):
    list_display = ["details", "kind"]
    search_fields = ["details__name", "details__related"]


@admin.register(CompanyAndSchool)
class CompanyAndSchoolAdmin(ServicesModelAdmin):
    list_display = ["name", "kind"]
    list_filter = ["kind"]
    search_fields = ["name"]


@admin.register(CVScript)
class CVScriptAdmin(ServicesModelAdmin):
    list_display = ["text"]
    list_filter = ["section"]

    # def get_queryset(self, request):
    #     return super().get_queryset(request).select_related("job_position")


@admin.register(JobCategory)
class JobCategoryAdmin(ServicesModelAdmin):
    pass


class JobCategoryFilter(admin.SimpleListFilter):
    title = _("JobCategory")
    parameter_name = "job_category"

    def lookups(self, request, model_admin):
        return JobCategory.s_objects.values_list("name", "name")

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(job_categories__name=self.value())
        return queryset


class CVScriptExistFilter(admin.SimpleListFilter):
    title = _("With CVScript")
    parameter_name = "cv_script"

    def lookups(self, request, model_admin):
        return (("Yes", "Yes"), ("No", "No"))

    def queryset(self, request, queryset):
        if self.value():
            queryset = queryset.annotate(cvscript_count=models.Count("cvscripts"))
            if self.value() == "Yes":
                return queryset.filter(cvscript_count__gt=0)
            if self.value() == "No":
                return queryset.filter(cvscript_count=0)
        return queryset


class JobCategoryCVScriptCoverFilter(admin.SimpleListFilter):
    title = _("Has Job Category CVScript Cover")
    parameter_name = "j_c_cover"

    def lookups(self, request, model_admin):
        return (("Yes", "Yes"), ("No", "No"))

    def queryset(self, request, queryset):
        if self.value():
            script_with_job_categories = (
                DjangoAppJobcvscript.s_objects.exclude(job_category=None)
                .values_list("job_category_id", flat=True)
                .distinct()
            )
            if self.value() == "Yes":
                return queryset.filter(
                    job_categories__id__in=list(script_with_job_categories)
                )
            if self.value() == "No":
                return queryset.exclude(
                    job_categories__id__in=list(script_with_job_categories)
                )
        return queryset


@admin.register(JobPosition)
class JobPositionAdmin(ServicesModelAdmin):
    list_display = [
        "name",
        "mission_script",
        "industry_script",
        "software_script",
        "work_script",
    ]
    list_filter = [
        CVScriptExistFilter,
        JobCategoryCVScriptCoverFilter,
        JobCategoryFilter,
    ]
    search_fields = ["name", "job_categories__name"]

    def query_params(self, obj):
        return f"?job-position={obj.name}"

    def mission_script(self, obj):
        params = self.query_params(obj)
        return mark_safe(
            f'<a target="_blank" href="{settings.CVSCRIPT_SERVICE}/cv-scripts/mission-statement{params}">Fetch MS</a>'
        )

    def industry_script(self, obj):
        params = self.query_params(obj)
        jj = obj.job_categories.all()
        job_category = jj[0]
        return mark_safe(
            f'<a target="_blank" href="{settings.CVSCRIPT_SERVICE}/industry-skills{params}&job-category={job_category}">Fetch Industry</a>'
        )

    def software_script(self, obj):
        params = self.query_params(obj)
        return mark_safe(
            f'<a target="_blank" href="{settings.CVSCRIPT_SERVICE}/softwares{params}">Fetch Softwares</a>'
        )

    def work_script(self, obj):
        params = self.query_params(obj)
        return mark_safe(
            f'<a target="_blank" href="{settings.CVSCRIPT_SERVICE}/cv-scripts/work-achievement{params}">Fetch WE</a>'
        )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("job_categories")
