# from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.background import BackgroundTask
from cv_utils.starlette import create_asgi_app, JSONResponse
from payment_service import services, utils
import requests
from starlette.requests import Request

app = create_asgi_app(
    debug=True, sentry_settings=services.settings.RAVEN_CONFIG['dsn'])


@app.exception_handler(HTTPException)
async def http_exception(request, exc):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.route("/")
async def homepage(request):
    alls = []
    return JSONResponse({"hello": "world", "alls": alls})


@app.route("/create-plan-payment", methods=["POST"])
@utils.async_login_required()
async def create_payment_plan(request):
    print(request.cleaned_body)
    if not hasattr(request, "cleaned_body"):
        return JSONResponse({"message": "Invalid data"}, status_code=400)
    if not hasattr(request, "pricing"):
        return JSONResponse({"message": "Invalid data"}, status_code=400)
    is_valid, result = services.create_payment_plan(
        request.user_id, request.cleaned_body, request.pricing,
        request.shared_networks)
    if is_valid:
        return JSONResponse(result, status_code=200)
    return JSONResponse(result, status_code=400)


@app.route("/create-payment", methods=["POST"])
@utils.async_login_required()
async def create_payment(request):
    if not hasattr(request, "cleaned_body"):
        return JSONResponse({"message": "Invalid data"}, status_code=400)
    is_valid, result = services.create_single_template_payment(
        request.user_id, request.cleaned_body, request.shared_networks)
    if is_valid:
        return JSONResponse(result, status_code=200)
    return JSONResponse(result, status_code=400)


async def process_payment(request, order, kind):
    return services.process_paystack_payment(request, order, kind=kind)


async def background_payment_actions(order, kind):
    services.update_payment_details(order, kind)


@app.route("/paystack/verify-payment/{order}/")
async def paystack_verify_payment(request:Request):
    order = request.path_params["order"]
    kind = request.query_params.get('kind')
    # url = determine_base_route(request._scope)
    # result = post_processing(
    #     f"{url}/v2/process-payment/paystack/{order}", dict(request.query_params)
    # )
    amount_only = kind != "agent"
    response = await services.verify_payment(
        request.query_params, order, amount_only=False)
    if response[0]:
        paystack_response = None
        if len(response) == 3:
            paystack_response = response[2]
        kind = services.process_paystack_payment(
            request.query_params, order, "paystack", data=paystack_response)
        task = BackgroundTask(background_payment_actions, order, kind)
        # task = BackgroundTask(services.update_payment_details, request.query_params, order, "paystack")
        return JSONResponse({"success": True}, background=task)
    return JSONResponse({"success": False}, status_code=400)


@app.route("/ravepay/verify-payment/{order}/")
async def verify_ravepay_payment(request):
    order = request.path_params["order"]
    response = await services.verify_payment(
        request.query_params, order, kind="ravepay")

    if response[0]:
        task = BackgroundTask(process_payment, request.query_params, order,
                              "ravepay")
        return JSONResponse({"success": True}, background=task)
    return JSONResponse({"success": False}, status_code=400)


@app.route("/process-payment/{order}")
async def post_process_payment_details(request):
    order = request.path_params["order"]
    task = BackgroundTask(background_payment_actions, order, "Pro")
    return JSONResponse({"success": True}, background=task)


def post_processing(url, query_params):
    response = requests.get(url, params=query_params)
    return True


def determine_base_route(scope):
    scheme = scope.get("scheme", "http")
    server = scope.get("server", None)
    path = scope.get("root_path", "") + scope["path"]
    query_string = scope["query_string"]

    host_header = None
    for key, value in scope["headers"]:
        if key == b"host":
            host_header = value.decode("latin-1")
            break

    if host_header is not None:
        url = "%s://%s" % (scheme, host_header)
    else:
        host, port = server
        default_port = {"http": 80, "https": 443, "ws": 80, "wss": 443}[scheme]
        if port == default_port:
            url = "%s://%s" % (scheme, host)
        else:
            url = "%s://%s:%s" % (scheme, host, port)
    return url
