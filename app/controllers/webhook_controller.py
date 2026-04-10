from fastapi import APIRouter

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.post("/receive")
async def receive_payload(data: dict):
    return {"status": "received", "data": data}


@router.get("/status")
async def get_status():
    return {"status": "active"}
