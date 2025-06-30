from fastapi import APIRouter, Header, Body, HTTPException
from services.planogram_services import PlanogramService

router = APIRouter()
service = PlanogramService()

@router.post("/planogram/combo-porto-set")
def combo_porto_set(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    result = service.batch_config(vending_application_id, payload)

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to set combo porto")

    return result["body"]

@router.post("/planogram/mc-pro-set")
def mc_pro_set(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    result = service.batch_config(vending_application_id, payload)

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to set mc pro")

    return result["body"]

@router.post("/planogram/set")
def planogram_set(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    result = service.config(vending_application_id, payload)

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to config planogram")

    return result["body"]

@router.get("/planogram/get")
def planogram_get(
    device_id: str,
    vending_application_id: str = Header(...)
):
    result = service.get_sensors(device_id, vending_application_id)

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get planogram")

    return result["body"]

@router.get("/planogram/get-ice")
def planogram_get_ice(
    device_id: str,
    vending_application_id: str = Header(...)
):
    result = service.get_ice(device_id, vending_application_id )

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get ice")

    return result["body"]
