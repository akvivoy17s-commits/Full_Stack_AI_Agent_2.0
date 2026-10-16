from flask import Blueprint

from .. import auth_service
from ..deps import AUTH_LIMIT, current_user, get_db, json_body, rate_limit

limited = rate_limit(AUTH_LIMIT)


def make_blueprint() -> Blueprint:
    bp = Blueprint("auth", __name__)

    @bp.post("/register")
    @limited
    def register():
        """Create an account (body: email, name, password)"""
        return auth_service.register(get_db(), json_body()), 201

    @bp.post("/login")
    @limited
    def login():
        """Sign in (body: email, password)"""
        return auth_service.login(get_db(), json_body())

    @bp.post("/refresh")
    @limited
    def refresh():
        """Exchange a refresh token for new tokens (single use)"""
        return auth_service.refresh(get_db(), json_body())

    @bp.post("/logout")
    def logout():
        """Sign out (body: refreshToken, optional)"""
        user = current_user()
        auth_service.logout(get_db(), user, json_body())
        return "", 204

    @bp.get("/me")
    def me():
        """The signed-in user"""
        return auth_service.me(get_db(), current_user())

    return bp
