from django.db import models

from cv_utils import payment
from django.contrib.postgres.fields import JSONField


class PlanMixin(object):
    pass


class Plan(models.Model):
    name = models.CharField(max_length=255)
    data = JSONField(default=payment.PricingMixin.PLAN_OPTIONS)
    kind = models.CharField(
        max_length=50,
        choices=[('client', 'client'), ('agent', 'agent')],
        default="client")
    resume_allowed = models.IntegerField(default=1, null=True)
    plan_details = JSONField(default={})

    @classmethod
    def get_plans(cls, kind="client"):
        if kind == 'client':
            pro_plan = cls.objects.filter(
                kind='client', name__iexact="Pro").first()
            free_plan = cls.objects.filter(
                kind='client', name__iexact="Free").first()
            result = {}
            if pro_plan and free_plan:
                plans = {pro_plan.name: {**pro_plan.data["amount"]}}
                result = {
                    "plans": plans,
                    "discount": pro_plan.data["discount"],
                    "resume_allowed": {
                        free_plan.name: free_plan.resume_allowed,
                        pro_plan.name: pro_plan.get_resume_allowed(),
                    },
                }
        else:
            pro_plans = cls.objects.filter(kind='agent').exclude(
                name__icontains='free').all()
            result = {}
            plans = {x.name: x.data['amount'] for x in pro_plans}
            resume_allowed = {x.name: x.resume_allowed for x in pro_plans}

            def extend_details(dd, key="plan"):
                uu = dd or {}
                if uu.get('annually'):
                    uu['annual'] = uu['annually']
                return {x: uu[x][key] for x in uu.keys()}

            codes = {x.name: extend_details(x.plan_details) for x in pro_plans}
            ids = {
                x.name: extend_details(x.plan_details, "plan_id")
                for x in pro_plans
            }
            result = {}
            if len(pro_plans) > 0:
                result = {
                    "plans": plans,
                    'discount': pro_plans[0].data['discount'],
                    'resume_allowed': resume_allowed,
                    'plan_code': codes,
                    'plan_id': ids
                }
        return result

    def get_resume_allowed(self):
        result = self.resume_allowed
        if self.name == "Free":
            return result
        if self.kind == "agent":
            return self.resume_allowed
        return "unlimited"
