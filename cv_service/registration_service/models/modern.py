from django.db import models
from django.utils.translation import ugettext_lazy as _


class AgentCustomer(models.Model):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    dob = models.CharField(max_length=100, blank=True, null=True)
    agent_id = models.IntegerField()

    @classmethod
    def get_agent_customers(cls, agent_id):
        return cls.objects.filter(agent_id=agent_id)

    @property
    def as_json(self):
        fields = [
            'first_name', 'last_name', 'email', 'address', 'phone',
            'photo_url', 'website', 'country'
        ]
        result = {}
        for k in fields:
            result[k] = getattr(self, k, None)
        result['social_link_url'] = self.website
        return result
