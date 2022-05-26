import graphene
from starlette.exceptions import HTTPException
from graphene_utils import utils
from . import agent_cv_service
from cv_utils import client as client_api
from registration_service import services

shared_fields = [
    ("first_name", str),
    ("last_name", str),
    ("email", str),
    ("phone", str),
    ("photo_url", str),
    ("website", str),
    ("country", str),
    ("address", str),
    ("dob", str),
]
CustomerType = utils.createGrapheneClass("Customer", [*shared_fields, ("id", int)])

CVSCriptType = utils.createGrapheneClass("CVScript", [("result", "json")])


def buildPagination(name, klass):
    return utils.createGrapheneClass(
        name, [("data", klass), ("page", int), ("count", int), ("error", str)]
    )


CustomerPagination = buildPagination("CustomerType", graphene.List(CustomerType))
ResumePagination = buildPagination("ResumeType", "json")

CustomerInputType = utils.createGrapheneInputClass("CustomerInputType", shared_fields)
ResumeInput = utils.createGrapheneInputClass(
    "ResumeInput",
    [
        ("level", str),
        ("job_category", str),
        ("headline", str),
        ("job_position", str),
        ("customer_email", str),
    ],
)


def get_agent(info):
    request = info.context["request"]
    if request.user.is_authenticated:
        agent = request.user.username["user_id"]
        return agent
    raise agent_cv_service.ValidationError("Invalid credentials")


class Query(graphene.ObjectType):
    getCustomers = graphene.Field(
        CustomerPagination,
        per_page=graphene.Int(default_value=50),
        current_page=graphene.Int(default_value=1),
    )

    addOrEditCustomer = graphene.Field(
        CustomerType,
        details=CustomerInputType(required=True),
        customer_id=graphene.Int(),
    )

    deleteCustomer = graphene.Field(
        graphene.Boolean, customer_id=graphene.Int(required=True)
    )

    getResumes = graphene.Field(
        ResumePagination,
        per_page=graphene.Int(default_value=50),
        current_page=graphene.Int(default_value=1),
        customer_id=graphene.Int(),
    )

    createOrDuplicateResume = graphene.Field(
        utils.GenericScalar, details=ResumeInput(), cv_id=graphene.Int()
    )

    deleteResume = graphene.Field(graphene.Boolean, cv_id=graphene.Int(required=True))

    saveResume = graphene.Field(
        utils.GenericScalar,
        details=graphene.types.json.JSONString(required=True),
        cv_id=graphene.Int(required=True),
    )

    getCVScript = graphene.Field(
        CVSCriptType,
        kind=graphene.String(required=True),
        user_id=graphene.Int(),
        job_position=graphene.String(),
        job_category=graphene.String(),
    )
    generateResume = graphene.Field(utils.GenericScalar, job_position=graphene.String())

    def resolve_getCustomers(self, info, **kwargs):
        agent = get_agent(info)
        result = agent_cv_service.getCustomers(agent, **kwargs)
        return {
            "data": result["items"],
            "page": kwargs["current_page"],
            "count": result["count"],
        }

    def resolve_addOrEditCustomer(self, info, **kwargs):
        agent = get_agent(info)
        return agent_cv_service.createCustomer(
            agent, kwargs["details"], customer_id=kwargs.get("customer_id")
        )

    def resolve_deleteCustomer(self, info, **kwargs):
        agent = get_agent(info)
        result = agent_cv_service.deleteCustomer(agent, kwargs["customer_id"])
        return result

    def resolve_getResumes(self, info, **kwargs):
        agent = get_agent(info)
        result = agent_cv_service.getResumes(agent, **kwargs)
        return {
            "data": result["items"],
            "page": kwargs["current_page"],
            "count": result["count"],
        }

    def resolve_createOrDuplicateResume(self, info, **kwargs):
        agent = get_agent(info)
        result = agent_cv_service.createOrDuplicateResume(agent, **kwargs)
        return result

    def resolve_deleteResume(self, info, **kwargs):
        agent = get_agent(info)
        return agent_cv_service.deleteResume(agent, kwargs["cv_id"])

    def resolve_saveResume(self, info, **kwargs):
        agent = get_agent(info)
        return agent_cv_service.saveResume(agent, kwargs["details"], kwargs["cv_id"])

    def resolve_getCVScript(self, info, **kwargs):
        user_id = kwargs.pop("user_id", None)
        if user_id:
            return services.get_cv_scripts(user_id, **kwargs)
        agent = get_agent(info)
        return agent_cv_service.get_cv_scripts(agent, **kwargs)

    def resolve_generateResume(self, info, **kwargs):
        job_position = kwargs["job_position"]
        supported_positions = client_api.get_supported_positions(
            agent_cv_service.settings.CVSCRIPT_GRAPHQL_ENDPOINT
        )
        if job_position not in supported_positions:
            raise HTTPException(403, details="")
        generated_data = client_api.generate_resume(kwargs["job_position"])
        

# class Mutation(graphene.ObjectType):
#     pass

schema = graphene.Schema(query=Query, auto_camelcase=False)
