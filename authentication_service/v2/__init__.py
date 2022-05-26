from starlette.responses import JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException
from cv_utils.starlette import create_asgi_app
from authentication_service import services
from .schema import schema
from . import agent_service

app = create_asgi_app(
    debug=True, auth_validation=agent_service.validateToken, schema=schema
)


@app.exception_handler(HTTPException)
async def http_exception(request, exc):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.route("/plans")
def get_plans_view(request):
    result = services.get_plans(kind=request.query_params.get("kind"))
    return JSONResponse(result)


@app.route("/user-plan/{user_id}")
def get_user_plan(request):
    params = request.query_params.get("agent")
    result = services.get_user_plan(
        request.path_params["user_id"], agent=params, _all_fields=True
    )
    return JSONResponse({"plan": result["name"], "expires": result.get("expires")})


@app.route("/verify-email-callback")
def email_verification(request):
    q_params = request.query_params
    email = q_params.get("email")
    token = q_params.get("token")
    callback_url = q_params.get("callback_url")
    if callback_url:
        return RedirectResponse(url=callback_url)
    verified = agent_service.validateToken(token)
    if verified:
        url = agent_service.afterUserEmailVerification(verified, email)
        return RedirectResponse(url=url)
    raise HTTPException("Invalid access")


@app.route("/")
async def homepage(request):
    alls = []
    return JSONResponse({"hello": "world", "alls": alls})
