from fastapi import APIRouter, Depends

from ..deps import current_user, get_db

router = APIRouter()


@router.post("", summary="Create an order from cart items (server-side prices and stock)", status_code=201)
def checkout(body: dict, user=Depends(current_user), db=Depends(get_db)):
    from .. import checkout_core
    return {"order": checkout_core.create_order(db, user["id"], (body or {}).get("items"))}
