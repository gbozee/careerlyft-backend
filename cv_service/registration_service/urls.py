import json

from django.http import Http404, JsonResponse, HttpResponse
from django.urls import path

from . import utils, services
from .models import CVProfile


def update_cv_server(request):
    data = json.loads(request.body)
    body = data.get("data")
    user_id = data.get("user_id")
    personal_info = data.get("personal-info")
    completed = data.get("completed", False)
    status_msg, result = services.process_uncompleted_cv(
        user_id, body, personal_info, completed=completed)
    if status_msg:
        return JsonResponse(result, status=200)
    return JsonResponse(result, status=400)


@utils.login_required(True)
def update_cv(request):
    data = request.cleaned_body
    personal_info = request.user
    user_id = request.user_id
    completed = request.cleaned_body.get("completed", False)
    status_msg, result = services.process_uncompleted_cv(
        request.user_id, data, personal_info, completed=completed)
    if status_msg:
        return JsonResponse(result, status=200)
    return JsonResponse(result, status=400)


@utils.login_required(True)
def update_cv_with_id(request, cv_id):
    instance = CVProfile.objects.get(pk=cv_id)
    status_msg, result = services.process_cv(
        instance,
        request,
        completed=instance.completed
        or request.cleaned_body.get("completed", False),
    )
    if status_msg:
        return JsonResponse(result, status=200)
    return JsonResponse(result, status=400)


@utils.login_required(True)
def get_cv(request, cv_id=None):
    data = services.process_cv_retrieval(request.method, request.GET,
                                         request.user_id, cv_id, request.user)
    if not data:
        raise Http404("data not found")
    return JsonResponse(data)
    # if request.method == "GET":
    #     data = get_data(
    #         request.GET, request.user_id, cv_id=cv_id, personal_info=request.user
    #     )
    #     if data is None:
    #         raise Http404("data not found")
    #     return JsonResponse({"data": data})
    # if request.method == "DELETE":
    #     data = delete_data(request.GET, request.user_id, cv_id=cv_id)
    #     return JsonResponse({"deleted": True, "data": data})


@utils.login_required()
def duplicate_cv(request, cv_id):
    data = services.duplicate_cv_instance(request.GET, cv_id, request.user_id)
    return JsonResponse({"data": data})


def save_cv_thumbnail(request, cv_id):
    data = json.loads(request.body)
    CVProfile.save_thumbnail(cv_id, data["image"])
    return JsonResponse({"saved": True})


# TEST DATA


def sample_view(request):
    return JsonResponse({"hello": "world"})


def download_cv(request, cv_id):
    instance = CVProfile.objects.get(pk=cv_id)
    wrapper = instance.download_cv()
    if wrapper:
        response = HttpResponse(wrapper, content_type="application/pdf")
        response[
            "Content-Disposition"] = f"attachment; filename={instance.headline}.pdf"
        return response
    return HttpResponse("Error downloading receipt", status=400)


@utils.login_required(True)
def save_completed_cv(request, cv_id):
    data = json.loads(request.body)
    result = CVProfile.save_cv_instance(cv_id, request.user_id, data["cv"])
    if result:
        return JsonResponse({"data": result})
    return JsonResponse({"error": "The CVID doesn't exists"}, status=400)


urlpatterns = [
    path("", sample_view),
    path("cv-profile-server", update_cv_server, name="update-cv-server"),
    path("cv-profile/<cv_id>", update_cv_with_id, name="update_cv_with_id"),
    path("save-thumbnail/<cv_id>", save_cv_thumbnail, name="save-thumbnail"),
    path("update-cv/<cv_id>", save_completed_cv, name="update-completed-cv"),
    path("download-cv/<cv_id>", download_cv, name="download_cv")
    # path('admin/', admin.site.urls),
]
