import os
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask
from starlette.exceptions import HTTPException
from registration_service import utils, services
from cv_utils.starlette import create_asgi_app
from . import schema, agent_cv_service

app = create_asgi_app(
    debug=True, schema=schema.schema, auth_validation=agent_cv_service.validateToken
)


@app.exception_handler(HTTPException)
async def http_exception(request, exc):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


def callback(*args, **kwargs):
    pass


@app.route("/cv-profile", methods=["POST"])
@utils.async_login_required(True)
async def update_cv(request):
    data = request.cleaned_body
    personal_info = request.user_data
    user_id = request.user_id
    completed = request.cleaned_body.get("completed", False)
    status_msg, result = await services.async_process_uncompleted_cv(
        request.user_id, data, personal_info, callback=callback, completed=completed
    )
    if status_msg:
        task = BackgroundTask(
            services.mailing_func, personal_info, user_id, completed, result
        )
        return JSONResponse(result, status_code=200, background=task)
    return JSONResponse(result, status_code=400)


async def process_profile(request, cv_id=None):
    data = await services.async_process_cv_retrieval(
        request.method, request.query_params, request.user_id, cv_id, request.user_data
    )
    if not data:
        return JSONResponse({"msg": "data not found"}, status_code=404)
    return JSONResponse(data)


@app.route("/get-profile", methods=["GET", "DELETE"])
@utils.async_login_required(True)
async def get_cv(request):
    return await process_profile(request)


@app.route("/get-profile/{cv_id}", methods=["GET", "DELETE"])
@utils.async_login_required(True)
async def get_cv_with_id(request):
    # import pdb ; pdb.set_trace()
    return await process_profile(request, **request.path_params)


@app.route("/resumes/{cv_id}", methods=["GET"])
def get_cv_details(request):
    token = request.query_params.get("token")
    if not token:
        return JSONResponse({"msg": "data not found"}, status_code=404)
    result = agent_cv_service.getResumeDetail(request.path_params["cv_id"], token)
    if not result:
        return JSONResponse({"msg": "data not found"}, status_code=404)

    return JSONResponse(result)


@app.route("/admin-bot/get-cv/{cv_id}", methods=["GET"])
async def admin_get_cv_by_id(request):
    cv_id = request.path_params.get("cv_id")
    agent = request.query_params.get("agent")
    user_id, result = await services.get_cv_by_id(cv_id)
    plan = await services.get_user_plan(user_id, agent)
    return JSONResponse({"data": result, **plan}, status_code=200)


@app.route("/my-cvs", methods=["GET", "DELETE", "POST", "OPTIONS"])
@utils.async_login_required(True)
async def get_my_cvs(request):
    return await process_profile(request)


@app.route("/duplicate-cv/{cv_id}", methods=["GET"])
@utils.async_login_required()
async def duplicate_cv(request):
    cv_id = request.path_params["cv_id"]
    data = await services.async_duplicate_cv_instance(
        request.query_params, cv_id, request.user_id
    )
    return JSONResponse({"data": data})


@app.route("/")
async def homepage(request):
    alls = []
    return JSONResponse({"hello": "world", "alls": alls})


DEBUG = os.getenv("DJANGO_DEBUG", "True")

# if DEBUG == "True":
# app = DebugMiddleware(app)
