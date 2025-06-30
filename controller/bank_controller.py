# app/controllers/bank_controller.py
from fastapi import APIRouter, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from services.bank_services import list_banks
import time

router = APIRouter()

@router.get("/banks")
def get_banks(
    request: Request,
    application_id: str = Header(alias="Vending-Application-Id")
):
    server_ts = int(time.time() * 1000)

    if not application_id:
        raise HTTPException(status_code=400, detail="Application id not found")

    res = list_banks(application_id)

    if res.status_code != 200:
        body = res.json()
        body["applicationId"] = application_id
        return JSONResponse(
            status_code=res.status_code,
            content={
                "timestamp": server_ts,
                "code": res.status_code,
                "message": body
            }
        )

    return JSONResponse(content={
        "timestamp": server_ts,
        "code": 200,
        "message": "List bank success",
        "data": res.json()
    })
