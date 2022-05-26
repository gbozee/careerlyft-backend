import graphene
from graphene_utils import utils

class Query(graphene.ObjectType):
    payment_details = utils.GenericScalar()
    get_customers = ""
    get_resumes = ""


schema = graphene.Schema(query=Query, auto_camelcase=False)
