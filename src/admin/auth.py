from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from config import settings


class AdminAuth(AuthenticationBackend):
    """
    Authentication backend for SQLAdmin administration panel.
    Protects /admin routes using session-based authentication.
    """

    def __init__(self, secret_key: str = None):
        super().__init__(secret_key=secret_key or settings.SECRET_KEY)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            request.session.update({
                "token": "admin-token",
                "user_id": username,
            })
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token or token != "admin-token":
            return False
        return True
