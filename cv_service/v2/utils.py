from starlette.authentication import (
    AuthenticationBackend, AuthenticationError, SimpleUser,
    UnauthenticatedUser, BaseUser, AuthCredentials)
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.responses import PlainTextResponse
import base64
import binascii
import json
from registration_service import utils


class LoggedInUser(BaseUser):
    def __init__(self, result):
        self.result = result
        for key, value in result.get('personal-info').items():
            setattr(self, key, value)

    def keys(self):
        return self.__dict__.keys()

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def is_authenticated(self):
        return True

    @property
    def display_name(self):
        return self._display_name


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        # TODO: You'd want to verify the username and password here,
        #       possibly by installing `DatabaseMiddleware`
        #       and retrieving user information from `request.database`.
        return AuthCredentials(["authenticated"]), SimpleUser(username)

    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return
        auth_header = request.headers['Authorization']

        token = auth_header.replace("Bearer", "").replace("Token", "").strip()
        kwar = [token]
        kw = {}
        kw.update({"cv_details": True})
        if request.method == "POST":
            data = json.loads(request.body)
            last_stop_point = data.pop("last_stop_point", None)
            if last_stop_point:
                kw.update({"last_stop_point": last_stop_point})
        result = utils.authenticate(*kwar, **kw)
        if not result:
            raise AuthenticationError(
                'This token is either invalid or expired')
        return AuthCredentials(['authenticated']), LoggedInUser(result)
