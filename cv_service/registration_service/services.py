import json
import re
import django

django.setup()
from django import forms
from django.http import Http404, JsonResponse
from django.urls import path
from cv_utils.starlette import sync_to_async, database_sync_to_async, async_to_sync
from . import utils
from .models import CVProfile


class CVForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # old_id = args[0].get('id')
        # instance = None
        # if old_id:
        #     instance = CVProfile.objects.filter(pk=old_id).first()
        super().__init__(*args, **kwargs)
        for field in self.Meta.fields:
            self.fields[field].required = False

    class Meta:
        model = CVProfile
        fields = [
            "mission_statement",
            "work_experiences",
            "industry_skills",
            "softwares",
            "certifications",
            "educations",
            "trainings",
            "headline",
            "job_position",
            "job_category",
            "level",
        ]

    def save(self, user_id, completed=False, personal_info=None):
        instance = super().save(commit=False)
        instance.user_id = user_id
        instance.completed = completed
        instance.cv_data = instance.get_cv(personal_info or {})
        instance.save()
        instance.rebuild_as_json()
        result = {"id": instance.id}
        for key in self.data.keys():
            result[key] = getattr(instance, key)
        return result


def mailing_func(personal_info, user_id, completed, result):
    if personal_info.get("email_subscribed"):
        utils.update_mailing_list(
            personal_info.get("email"),
            user_id,
            completed,
            data={**result, **personal_info},
        )


def _process_cv(
    instance, old_data, personal_info, user_id, callback=mailing_func, **kwargs
):
    new_data = {}
    data = old_data
    if instance:
        for i in CVForm.Meta.fields:
            new_data[i] = getattr(instance, i)
        data = {**new_data, **old_data}
    form = CVForm(data, instance=instance)
    if form.is_valid():
        result = form.save(user_id, personal_info=personal_info, **kwargs)
        callback(personal_info, user_id, kwargs.get("completed"), result)
        # utils.update_mailing_list()
        return True, result
    return False, {"errors": form.errors}


def process_cv(instance, request, **kwargs):
    data = request.cleaned_body
    personal_info = request.user
    user_id = request.user_id
    return _process_cv(instance, data, personal_info, user_id, **kwargs)


# @database_sync_to_async
def process_uncompleted_cv(user_id, data, personal_info, completed=False, **kwargs):
    instance = CVProfile.get_uncompleted_instance(user_id=user_id)
    return _process_cv(
        instance, data, personal_info, user_id, completed=completed, **kwargs
    )


def get_data(query_params, user_id, cv_id=None, personal_info=None, _all=False):
    if query_params.get("all"):
        data = CVProfile.all_user_cvs(user_id)
    else:
        data = CVProfile.get_last_profile(
            user_id=user_id, cv_id=cv_id, personal_info=personal_info
        )
    return data


def delete_data(query_params, user_id, cv_id=None):
    if cv_id:
        CVProfile.delete_cv(cv_id, user_id)
        data = []
        if query_params.get("all"):
            data = CVProfile.all_user_cvs(user_id)
    else:
        CVProfile.objects.filter(user_id=user_id).delete()
        data = []
    return data


def process_cv_retrieval(method, query_params, user_id, cv_id, personal_info):
    if method == "GET":
        data = get_data(query_params, user_id, cv_id=cv_id, personal_info=personal_info)
        if data is None:
            return None
        return {"data": data}
    if method == "DELETE":
        data = delete_data(query_params, user_id, cv_id=cv_id)
        return {"deleted": True, "data": data}


def duplicate_cv_instance(query_params, cv_id, user_id):
    job_position = query_params.get("job_position")
    job_category = query_params.get("job_category")
    data = CVProfile.duplicate_cv(
        cv_id, user_id, job_position=job_position, job_category=job_category
    )
    if query_params.get("all"):
        data = CVProfile.all_user_cvs(user_id)
    return data


@database_sync_to_async
def async_process_cv_retrieval(*args):
    return process_cv_retrieval(*args)


@database_sync_to_async
def get_cv_by_id(cv_id):
    return CVProfile.get_cv_by_id(cv_id)


@database_sync_to_async
def async_process_uncompleted_cv(
    user_id, data, personal_info, completed=False, **kwargs
):
    return process_uncompleted_cv(
        user_id, data, personal_info, completed=completed, **kwargs
    )


@sync_to_async
def get_user_plan(user_id, agent=None):
    return utils.get_user_plan(user_id, agent)


@database_sync_to_async
def async_duplicate_cv_instance(*args):
    return duplicate_cv_instance(*args)


def get_cv_scripts(user_id, **kwargs):
    instances = CVProfile.objects.filter(user_id=user_id)
    return instances.get_cv_scripts(**kwargs)

