from django.core.paginator import Paginator
from django.http import Http404
from django.core.cache import cache
from .utils import JsonResponse, login_required, get_user_cvscripts
from . import models


def get_item_from_cache(cache_name, func, timeout=60 * 60 * 24):
    category = cache.get(cache_name)
    if not category:
        category = func()
        cache.set(cache_name, category, timeout)
    return category


def get_job_categories(request):
    query_param = request.GET.get("q")

    def query_specific():
        categories = models.JobPosition.get_job_categories(query_param)
        return list(categories)

    def generic():
        categories = models.JobCategory.get_all_categories("name")
        return list(categories)

    if query_param:
        categories = get_item_from_cache(f"JOB_CATEGORY_{query_param}", query_specific)
    else:
        categories = get_item_from_cache(f"ALL_JOB_CATEGORIES", generic)
    return JsonResponse({"data": categories})


def get_job_position(request):
    job_category = request.GET.get("job-category")
    search_param = request.GET.get("q")
    agent = request.GET.get("agent")
    token = request.META.get("HTTP_AUTHORIZATION")
    cache_name = f"JOB_POSITION_{search_param}"

    def callback():
        data = models.JobPosition.get_positions(None, search_param)
        return list(data)

    token = request.META.get("HTTP_AUTHORIZATION")
    if token:
        token = token.replace("Bearer", "").replace("Token", "").strip()
        positions = get_user_cvscripts(token, "job_position", agent=bool(agent))
        positions = [{"name": x} for x in positions]
    else:
        positions = get_item_from_cache(cache_name, callback)

    # positions = models.JobPosition.get_positions(job_category, search_param)
    return JsonResponse({"data": positions})


# @login_required()
def get_cv_script(request, section):
    job_position = request.GET.get("job-position")
    job_category = request.GET.get("job-category")
    agent = request.GET.get("agent")
    page = request.GET.get("page", 1)
    token = request.META.get("HTTP_AUTHORIZATION")
    if token:
        token = token.replace("Bearer", "").replace("Token", "").strip()
        options = {
            "mission-statement": "mission_statement",
            "work-achievement": "work_experience",
            "industry-skills": "industry_skills",
            # "cover-letter": "cover_letter"
        }
        scripts = get_user_cvscripts(
            token,
            options[section],
            agent=bool(agent),
            job_position=job_position,
            job_category=job_category,
        )
    else:
        scripts = models.JobCVScript.get_scripts(section, job_position, job_category)

    per_page = request.GET.get("per_page", 100)
    paginator = Paginator(list(scripts), per_page)
    _page = paginator.page(int(page))
    response = {
        "data": _page.object_list,
        "count": paginator.count,
        "total_num_of_pages": paginator.num_pages,
        "current_page": page,
    }
    return JsonResponse(response)


def get_fetch_generic_data(request, path):
    search_param = request.GET.get("q")
    per_page = request.GET.get("per_page", 25)
    try:
        result = models.CompanyAndSchool.get_queryset(
            path, search_param, per_page=int(per_page)
        )
    except ValueError:
        return JsonResponse(
            {"message": "input an integer for the per_page param"}, status=400
        )

    if result is None:
        raise Http404("This page is missing")
    if isinstance(result, tuple):
        return JsonResponse(
            {"message": "3 or more characters are required"}, status=400
        )
    return JsonResponse({"data": list(result)})


def shared_arraylist_implementation(request, kind="softwares"):
    options = {
        "softwares": models.JobPosition.get_skills,
        "industry": models.JobPosition.get_industry_skills,
    }
    job_position = request.GET.get("job-position")
    specific_skills = options[kind](job_position)
    return job_position, specific_skills


def get_softwares(request):
    token = request.META.get("HTTP_AUTHORIZATION")
    agent = request.GET.get("agent")
    if token:
        token = token.replace("Bearer", "").replace("Token", "").strip()
        data = get_user_cvscripts(
            token,
            "software_skills",
            agent=bool(agent),
            job_position=request.GET.get("job-position"),
        )
    else:
        job_position, specific_skills = shared_arraylist_implementation(request)
        generic_skills = models.CompanyAndSchool.get_section(
            models.CompanyAndSchool.SOFTWARE
        )
        data = list(set(generic_skills + specific_skills))
    return JsonResponse({"data": data})


def get_certificates(request):
    certificates = models.CompanyAndSchool.get_section(
        models.CompanyAndSchool.CERTIFICATION
    )
    return JsonResponse({"data": list(certificates)})


def get_keywords(request):
    job_position = request.GET.get("job-position")
    job_category = request.GET.get("job-category")
    data = []
    if job_position:
        xx = models.JobPosition.objects.filter(name__iexact=job_position).values_list(
            "keywords", flat=True
        )
        data = data + [x for y in xx if y for x in y]
    if job_category:
        xx = models.JobCategory.objects.filter(
            name__icontains=job_category
        ).values_list("keywords", flat=True)
        data = data + [x for y in xx if y for x in y]
    scripts = get_item_from_cache(
        f"KEY_WORDS_{job_position}_{job_category}", lambda: list(set(data))
    )
    return JsonResponse({"data": scripts})


def get_industry_skills(request):
    job_position = request.GET.get("job-position")
    job_category = request.GET.get("job-category")
    agent = request.GET.get("agent")

    def generic():
        scripts = models.JobCVScript.split_industry_skills(job_position, job_category)
        return scripts

    token = request.META.get("HTTP_AUTHORIZATION")
    if token:
        token = token.replace("Bearer", "").replace("Token", "").strip()
        scripts = get_user_cvscripts(
            token,
            "industry_skills",
            agent=bool(agent),
            job_position=job_position,
            job_category=job_category,
        )
    else:
        scripts = get_item_from_cache(
            f"INDUSTRY_SKILLS_{job_position}_{job_category}", generic
        )

    response = {"data": scripts}
    return JsonResponse(response)
