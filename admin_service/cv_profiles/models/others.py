from django.db import models
from django.contrib.postgres.fields import JSONField
from . import users

# Create your models here.


class AgentCustomer(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo_url = models.CharField(max_length=200, blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    agent = models.ForeignKey(
        users.Agent,
        db_column='agent_id',
        null=True,
        on_delete=models.SET_NULL)

    class Meta:
        managed = False
        db_table = 'registration_service_agentcustomer'


class RegistrationServiceCvprofile(models.Model):
    created = models.DateTimeField(
        auto_now_add=True, blank=True, editable=False)
    modified = models.DateTimeField(auto_now=True, blank=True, editable=False)
    mission_statement = models.TextField(blank=True)
    # user_id = models.IntegerField()
    user = models.ForeignKey(
        users.Customer,
        db_column='user_id',
        null=True,
        on_delete=models.SET_NULL,blank=True)
    certifications = JSONField(null=True, blank=True)
    educations = JSONField(null=True, blank=True)
    industry_skills = JSONField(null=True, blank=True)
    softwares = JSONField(null=True, blank=True)
    trainings = JSONField(null=True, blank=True)
    work_experiences = JSONField(null=True, blank=True)
    headline = models.CharField(max_length=200, blank=True)
    completed = models.BooleanField(default=False)
    cv_data = JSONField(null=True, blank=True)
    thumbnail = models.TextField(blank=True, null=True)
    job_position = models.CharField(max_length=70, null=True, blank=True)
    job_category = models.CharField(max_length=70, null=True, blank=True)
    level = models.CharField(blank=True, null=True, max_length=200)
    customer = models.ForeignKey(
        AgentCustomer, models.DO_NOTHING, blank=True, null=True)

    objects = users.CustomerManager()

    class Meta:
        managed = False
        db_table = 'registration_service_cvprofile'

    # @property
    # def user(self):
    #     return Customer.objects.get(pk=self.user_id)
