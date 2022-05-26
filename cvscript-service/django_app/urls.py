"""django_app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.views.decorators.cache import cache_page
from .utils import JsonResponse
from django.http import Http404
from . import views


def sample_request(request):
    return JsonResponse({"message": "hello world"})


urlpatterns = [
    path("", sample_request),
    path("job-categories", views.get_job_categories, name="job-categories"),
    path("job-positions", views.get_job_position, name="job-positions"),
    path('cv-scripts/keywords', views.get_keywords, name='keywords'),
    path("cv-scripts/<section>", views.get_cv_script, name="cv-scripts"),
    path("softwares", views.get_softwares, name="softwares"),
    path(
        "certifications",
        cache_page(60 * 60 * 24)(views.get_certificates),
        name="certifications",
    ),
    path("industry-skills", views.get_industry_skills, name="industry_skills"),
    path("<path>",
         cache_page(60 * 60 * 24)(views.get_fetch_generic_data)),
]
