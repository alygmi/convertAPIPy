# app/controllers/account_controller.py
from fastapi import APIRouter, Body, Depends, Header, Request, Query
from fastapi.responses import JSONResponse
from schemas.account_schemas import AccountCreate
from services import account_services
from sqlalchemy.orm import Session
from database import get_db
import time

router = APIRouter()


@router.get("/account")
async def get_account(request: Request, account_id: str = Query(default=None)):
    server_ts = int(time.time() * 1000)
    application_id = request.headers.get("Vending-Application-Id")

    if not application_id:
        return JSONResponse(status_code=400, content={
            "timestamp": server_ts,
            "code": -1,
            "message": "Application id not found"
        })

    if account_id:
        body = {"account_id": account_id}
        res = account_services.account_get(application_id, body)
    else:
        res = account_services.account_list(application_id)

    if res.status_code != 200:
        return JSONResponse(status_code=500, content={
            "timestamp": server_ts,
            "code": res.status_code,
            "message": res.text
        })

    return JSONResponse(content={
        "timestamp": server_ts,
        "code": 200,
        "message": "List Account success",
        "data": res.json()
    })


@router.post("/account/create")
async def create_account(
    payload: AccountCreate = Body(...), 
    application_id: str = Header(alias="Vending-Application-Id"),
    db: Session = Depends(get_db)
):
    server_ts = int(time.time() * 1000)

    if not application_id:
        return JSONResponse(status_code=400, content={
            "timestamp": server_ts,
            "code": -1,
            "message": "Application Id Not Found"
        })

    try:
        account = account_services.account_create(db, application_id, payload)

        return JSONResponse(status_code=201, content={
            "timestamp": server_ts,
            "code": 201,
            "message": "Account created successfully",
            "data": {
                "id": account.id,
                "account_name": account.account_name,
                "account_no": account.account_no,
                "account_email": account.account_email,
                "account_bank_id": account.account_bank_id,
            }
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={
            "timestamp": server_ts,
            "code": -999,
            "message": f"Account creation failed: {str(e)}"
        })
