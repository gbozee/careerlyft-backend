import graphene
from graphene_utils import utils
from django_app.models import JobCVScript, JobPosition, Miscellaneous


class ResumeType(graphene.ObjectType):
    def __init__(self, *args, **kwargs):
        self.job_position = kwargs.pop("job_position")
        super().__init__(*args, **kwargs)

    work_experience = graphene.Field(
        utils.GenericScalar,
        max_count=graphene.Int(default_value=2, required=False),
        companies=graphene.List(
            graphene.String,
            required=False,
            default_value=["Fac", "Goog", "Link", "Micr"],
        ),
    )
    education = graphene.Field(
        utils.GenericScalar, max_count=graphene.Int(default_value=1, required=False)
    )
    industry_skills = graphene.Field(
        utils.GenericScalar, max_count=graphene.Int(default_value=5, required=False)
    )
    software_skills = graphene.Field(
        utils.GenericScalar,
        max_count=graphene.Int(default_value=5, required=False),
        groups=graphene.Boolean(default_value=False, required=False),
    )
    mission_statement = graphene.Field(utils.GenericScalar)
    projects = graphene.Field(utils.GenericScalar)

    def resolve_work_experience(self, info, **kwargs):
        return self.job_position.generate_work_experiences(
            kwargs["companies"], count=kwargs["max_count"]
        )

    def resolve_mission_statement(self, info, **kwargs):
        return self.job_position.generate_career_profile()

    def resolve_industry_skills(self, info, **kwargs):
        return self.job_position.generate_industry_skills(count=kwargs["max_count"])

    def resolve_software_skills(self, info, **kwargs):
        return self.job_position.generate_software_skills(
            group=kwargs["groups"], count=kwargs["max_count"]
        )

    def resolve_education(self, info, **kwargs):
        return self.job_position.generate_educations(count=kwargs["max_count"])

    def resolve_projects(self, info, **kwargs):
        return self.job_position.generate_projects()



class Query(graphene.ObjectType):
    get_resume = graphene.Field(ResumeType, job_position=graphene.String(required=True))
    supported_job_positions = graphene.Field(utils.GenericScalar)

    def resolve_get_resume(self, info, **kwargs):
        job_position = JobPosition.objects.filter(name__iexact=kwargs["job_position"]).first()
        if not job_position:
            return None
        return ResumeType(job_position=job_position)

    def resolve_supported_job_positions(self, info, **kwargs):
        result = Miscellaneous.objects.roles_that_support_resume_generation()
        return result


schema = graphene.Schema(query=Query, auto_camelcase=False)

