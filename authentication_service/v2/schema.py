import graphene
from graphene_utils import utils
from . import agent_service

Agent = utils.createGrapheneClass(
    'Agent',
    [("pk", int), ('first_name', str), ('company_name', str), ('email', str),
     ('first_name', str), ('last_name', str), ('country', str), ('phone', str),
     ('website', str), ('company_size', str), ('plan', 'json'),
     ("email_subscribed", bool), ("feature_notification", bool),
     ('business_id', str), ("verified_email", bool), ('is_owner', bool),
     ('preferences', 'json')])

Response = utils.createGrapheneClass('Response', [
    ("token", str),
    ("personal_info", graphene.Field(Agent)),
    ("errors", utils.GenericScalar()),
])

AgentSignupDetail = utils.createGrapheneInputClass(
    "AgentSignupDetail",
    [("email", str), ("company_name", str), ("password", str),
     ('first_name', str), ('last_name', str), ('country', str), ('phone', str),
     ('website', str), ('company_size', str), ('is_owner', bool),
     ('preferences', 'json')],
)
Plans = utils.createGrapheneClass(
    'Plans', [("plans", "json"), ("discount", int), ("resume_allowed", "json"),
              ("plan_code", "json"), ("plan_id", "json")])


def build_url(components):
    # if components.port:
    #     return f"{components.scheme}://{components.netloc}:{components.port}"
    return f"{components.scheme}://{components.netloc}"


class AgentSignupMutation(utils.BaseMutation):
    fields = [
        ("token", str),
        ("personal_info", graphene.Field(Agent)),
        ('errors', 'json'),
    ]
    form_fields = {
        "details": AgentSignupDetail(required=True),
        "step": graphene.Int(required=True),
    }

    def callback(self, info, **kwargs):
        step = kwargs["step"]
        details = kwargs['details']
        required_steps = {
            1: ['email', 'company_name', 'password'],
            2: ['first_name', 'last_name', 'country', 'phone']
        }
        is_valid = all([x for x in details if x in required_steps[step]])
        request = info.context['request']
        background = info.context['background']
        if is_valid:
            if step == 1:
                result = agent_service.agentSignup(**details)
                if result:
                    domain = build_url(request.url.components)
                    background.add_task(agent_service.send_verify_email,
                                        domain, result)
            else:
                user = request.user.username
                result = agent_service.updatePersonalInfo(user, details)
            if result:
                return result
        return {'errors': ["The email provided already exists"]}


class Mutation(graphene.ObjectType):
    agentSignupOrUpdate = AgentSignupMutation.Field()


class Query(graphene.ObjectType):
    agentLogin = graphene.Field(
        Response,
        email=graphene.String(required=True),
        password=graphene.String(required=True),
    )
    agentResetPassword = graphene.Field(
        graphene.Boolean,
        email=graphene.String(),
        token=graphene.String(),
        callback_url=graphene.String(),
        password=graphene.String())
    agentValidateToken = graphene.Field(
        graphene.Boolean, email=graphene.String(required=True))
    agentDetails = graphene.Field(Agent)
    agentDeleteAccount = graphene.Boolean()
    getPlans = graphene.Field(Plans, kind=graphene.String(required=True))
    agentUpdatePlan = graphene.Field(
        Agent,
        plan=graphene.String(required=True),
        currency=graphene.String(required=True),
        duration=graphene.String(required=True),
        date=graphene.String(required=True),
        paystack_details=graphene.types.json.JSONString(),
        email=graphene.String())
    agentQuickbooksUpdate = graphene.Field(
        graphene.Boolean,
        details=graphene.types.json.JSONString(required=True),
        email=graphene.String(required=True))

    def resolve_agentLogin(self, info, **kwargs):
        result = agent_service.agentLogin(**kwargs)
        if result:
            return result
        return {'errors': ["Invalid credentials"]}

    def resolve_agentResetPassword(self, info, **kwargs):
        request = info.context['request']
        if 'password' in kwargs and 'token' in kwargs:
            result = agent_service.resetPassword(kwargs['token'],
                                                 kwargs['password'])
            return result
        else:
            domain = build_url(request.url.components)
            result = agent_service.initiateResetPassword(domain, **kwargs)
            background = info.context['background']
            if result:
                background.add_task(agent_service.utils.send_mail,
                                    "forgot_password", result, kwargs['email'])
                return True
        return False

    def resolve_agentValidateToken(self, info, **kwargs):
        request = info.context['request']
        if request.user.is_authenticated:
            return request.user.username['user'].email.lower() == kwargs[
                'email'].lower()
        return False

    def resolve_agentDetails(self, info, **kwargs):
        request = info.context['request']
        if request.user.is_authenticated:
            return request.user.username['user'].as_json

    def resolve_agentDeleteAccount(self, info, **kwargs):
        request = info.context['request']
        background = info.context['background']
        if request.user.is_authenticated:
            data = request.user.username
            background.add_task(agent_service.deleteAccount, data)
            return True
        return False

    def resolve_getPlans(self, info, **kwargs):
        result = agent_service.get_plans(kind=kwargs.get("kind"))
        return result

    def resolve_agentUpdatePlan(self, info, **kwargs):
        request = info.context['request']
        email = get_email(kwargs)
        if email:
            return agent_service.update_plan(kwargs, email=email)
        if request.user.is_authenticated:
            user = request.user.username['user']
            return agent_service.update_plan(kwargs, user)
        return False

    def resolve_agentQuickbooksUpdate(self, info, **kwargs):
        email = get_email(kwargs)
        if email:
            return agent_service.update_user_details(email, kwargs['details'])


def get_email(kwargs):
    email = kwargs.pop('email', None)
    if email:
        result = email.split("---subscription")
        if len(result) > 1:
            return result[0]


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
