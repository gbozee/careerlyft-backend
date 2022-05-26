from django_app.wsgi import application
from cv_utils.starlette import initialize_router, Starlette
from v2 import app as asgi_app

app = initialize_router(
    [{"path": "/v2", "app": asgi_app}, {"path": "", "app": application, "wsgi": True}]
)
