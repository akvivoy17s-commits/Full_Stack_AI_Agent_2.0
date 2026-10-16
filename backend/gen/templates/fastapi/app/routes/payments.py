from fastapi import APIRouter, Depends, Request
from starlette.concurrency import run_in_threadpool

from ..deps import current_user, get_db

router = APIRouter()


@router.post("/intent", summary="Start a payment for one of your pending orders (amount read from the order)", status_code=201)
def intent(body: dict, user=Depends(current_user), db=Depends(get_db)):
    from .. import payments_core
    return payments_core.create_intent(db, user["id"], (body or {}).get("orderId"))


@router.post("/webhook", summary="Payment provider webhook (signature verified)")
async def webhook(request: Request, db=Depends(get_db)):
    from .. import payments_core
    raw = await request.body()                       # signature is computed over the exact raw bytes
    await run_in_threadpool(payments_core.handle_webhook, db, raw, dict(request.headers))
    return {"received": True}
