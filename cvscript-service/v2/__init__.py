from cv_utils.starlette import initialize_router, create_asgi_app, Starlette
from starlette.responses import JSONResponse
from .schema import schema

app = create_asgi_app(schema=schema)


@app.route("/")
async def home(request):
    return JSONResponse({"message": "hello world"})
