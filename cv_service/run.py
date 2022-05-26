from registration_service.wsgi import application
from v2 import app as asgi_app
from cv_utils.starlette import initialize_router

# import sentry_sdk
# from sentry_sdk.integrations.logging import LoggingIntegration

# # All of this is already happening by default!
# sentry_logging = LoggingIntegration(
#     level=logging.INFO,        # Capture info and above as breadcrumbs
#     event_level=logging.ERROR  # Send errors as events
# )
# sentry_sdk.init(
#     dsn="https://d92fffd7b35347d3b7941e92d0c9954d@sentry.io/1255801",
#     integrations=[sentry_logging]
# )
app = initialize_router([{
    "path": "/v2",
    "app": asgi_app
}, {
    "path": "",
    "app": application,
    "wsgi": True
}])
