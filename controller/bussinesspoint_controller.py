from fastapi import APIRouter, Body, Header, HTTPException, Depends
from services.bussinesspoint_services import BusinessPointService
import time

router = APIRouter()
service = BusinessPointService()

@router.get("/devices")
async def list_devices(vending_application_id: str = Header(...)):
    server_ts = int(time.time() * 1000)

    if not vending_application_id:
        raise HTTPException(status_code=400, detail="Application id not found")

    res = service.list_devices(vending_application_id)

    if res.get("code") != 200:
        raise HTTPException(status_code=500, detail=str(res.get("body")))

    res["body"]["server_ts"] = server_ts
    res["body"]["message"] = "List device success"
    return res["body"]

@router.get("/get-masterdata")
def get_masterdata(vending_application_id: str = Header(...)):
    resp = service.get_master_data(vending_application_id)
    if resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get master data")
    return resp["body"]

@router.post("/set-masterdata")
def set_masterdata(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    resp = service.add_master(vending_application_id, payload)
    if resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to set master data")
    return resp["body"]

