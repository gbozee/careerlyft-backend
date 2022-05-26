import os
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Router
from cv_utils.starlette import create_asgi_app
from urllib.parse import unquote
import asyncio
import aiohttp

mini_app = Starlette()


@mini_app.route("/shortener", methods=["POST"])
async def link_shortener(request):
    async with aiohttp.ClientSession() as client:
        body = await request.json()
        original = await client.post("https://link-shortener.now.sh", json=body)
        body = await original.json()
        return JSONResponse(body)


class Proxy:
    def __init__(self, base_url, path, max_concurrency=20):
        self.base_url = base_url
        self.path = path
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrency)

    def __call__(self, scope):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return _ProxyResponder(
            scope, self.base_url, self.path, self.session, self.semaphore
        )


class _ProxyResponder:
    def __init__(self, scope, base_url, path, session, semaphore):
        assert scope["type"] == "http"
        self.scope = scope
        self.base_url = base_url
        self.path = path
        self.session = session
        self.semaphore = semaphore

    async def __call__(self, receive, send):
        # import pdb
        # pdb.set_trace()
        request = Request(self.scope, receive)
        method = request.method
        path = request.url.path.split(self.path)[1]
        url = self.base_url + path
        headers = request.headers.mutablecopy()
        del headers["host"]
        # headers["connection"] = "keep-alive"
        data = await request.body()
        kwargs = {
            "" "method": method,
            "url": url,
            "data": data,
            "params": dict(request.query_params),
            "headers": headers,
        }
        # import pdb
        # pdb.set_trace()
        print(kwargs)
        async with self.semaphore:
            original = await self.session.request(**kwargs)
            body = await original.read()
        response = Response(body, status_code=original.status, headers=original.headers)
        response.headers["access-control-allow-origin"] = "*"
        response.headers[
            "vary"
        ] = "Origin, Access-Control-Request-Headers, Access-Control-Request-Method"
        await response(receive, send)


endpoints = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:8001"),
    "cvscript-endpoint": os.getenv("CVSCRIPT_SERVICE_URL", "http://localhost:8002"),
    "payment-endpoint": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
    "cv_profile": os.getenv("CV_PROFILE_SERVICE_URL", "http://localhost:8004"),
}
router = Router(
    [
        Mount(f"/{key}", app=Proxy(value, path=f"/{key}"))
        for key, value in endpoints.items()
    ]
    + [Mount("", app=mini_app)]
)
app = create_asgi_app()
# app = Starlette()
# app.add_middleware(
#     CORSMiddleware, allow_methods=["*"], allow_origins=["*"], allow_headers=["*"]
# )
app.mount("", router)
