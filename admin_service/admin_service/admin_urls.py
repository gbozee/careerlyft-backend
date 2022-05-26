from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from cvscripts.models import JobCategory, JobPosition, CVScript, DjangoAppJobcvscript


def job_position_details(request, pk):
    instance = JobPosition.s_objects.filter(pk=pk).first()
    return JsonResponse(instance.as_json)


def job_category_details(request, pk):
    instance = JobCategory.s_objects.filter(pk=pk).first()
    return JsonResponse(instance.as_json)


urlpatterns = [
    path("job-positions/<pk>/", job_position_details, name="job_positions"),
    path("job-categories/<pk>/", job_category_details, name="job_categories"),
]
