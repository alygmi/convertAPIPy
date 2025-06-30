from fastapi import APIRouter, Header, Query, HTTPException
from services.payout_services import PayoutService
import time

router = APIRouter()
payout_service = PayoutService()

@router.get("/payouts")
async def list_payouts(
    vending_application_id: str = Header(...),
    start: str = Query(default=None),
    end: str = Query(default=None),
    ndata: str = Query(default=None),
    payout_id: str = Query(default=None),
):
    server_ts = int(time.time() * 1000)

    if not vending_application_id:
        raise HTTPException(status_code=400, detail="Application ID not Found")
    
    url = "https://pay.iotera.io/web/payout/transaction/all"
    body = {}

    if ndata:
        url= "https://pay.iotera.io/web/payout/transaction/latest"
        body = {"ndata": ndata}
    elif start and end:
        try:
            body = {
                "start": int(start),
                "end": int(end)
            }
            url = "https://pay.iotera.io/web/payout/transaction/period"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Time Format")
    elif payout_id:
        url = "https://pay.iotera.io/web/payout/transaction/get"
        body = {"payout": payout_id}

    result = payout_service.list(vending_application_id, url, body)

    if result["body"].get("result") != 1:
        raise HTTPException(status_code=400, detail=result["body"])
    
    return result["body"]