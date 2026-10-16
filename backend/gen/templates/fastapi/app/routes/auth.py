from typing import Any

from fastapi import APIRouter, Body, Depends, Response

from .. import auth_service
from ..deps import AUTH_LIMIT, current_user, get_db, rate_limit

router = APIRouter()
limited = [Depends(rate_limit(AUTH_LIMIT))]


@router.post("/register", status_code=201, dependencies=limited, summary="Create an account (body: email, name, password)")
def register(body: Any = Body(None), db=Depends(get_db)):
    return auth_service.register(db, body)


@router.post("/login", dependencies=limited, summary="Sign in (body: email, password)")
def login(body: Any = Body(None), db=Depends(get_db)):
    return auth_service.login(db, body)


@router.post("/refresh", dependencies=limited, summary="Exchange a refresh token for new tokens (single use)")
def refresh(body: Any = Body(None), db=Depends(get_db)):
    return auth_service.refresh(db, body)


@router.post("/logout", status_code=204, response_class=Response, summary="Sign out (body: refreshToken, optional)")
def logout(body: Any = Body(None), db=Depends(get_db), user: dict = Depends(current_user)):
    auth_service.logout(db, user, body)
    return Response(status_code=204)


@router.get("/me", summary="The signed-in user")
def me(db=Depends(get_db), user: dict = Depends(current_user)):
    return auth_service.me(db, user)
