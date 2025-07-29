import time
from typing import Dict
from fastapi import APIRouter, Header, Body, HTTPException, Request
from services.planogram_services import PlanogramService
from utils.planogram import decode_base64_payload, build_config_list
from utils.response import ok_json, bad_request_json, br_failed

router = APIRouter()
service = PlanogramService()


@router.post("/planogram/combo-porto-set")
async def combo_porto_set(
    vending_application_id: str = Header(..., alias="vending-application-id"),
    payload: Dict[str, str] = Body(...)
):
    try:
        # Extract and decode base64 data
        encoded_data = payload.get("data")
        if not encoded_data:
            raise HTTPException(
                status_code=400, detail="Missing data field in payload")

        try:
            decoded_payload = decode_base64_payload(encoded_data)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Validate required fields
        device_id = decoded_payload.get("device_id")
        if not device_id:
            raise HTTPException(
                status_code=400, detail="device_id is required")

        wait_result = decoded_payload.get("wait_result", True)

        # Build configList
        config_list = build_config_list(decoded_payload)
        if not config_list:
            raise HTTPException(
                status_code=400,
                detail="No valid configuration data provided"
            )

        # Call service
        result = await service.batch_config(
            vending_application_id,
            device_id,
            config_list,  # type: ignore
            wait_result
        )

        # Handle response
        if not result.get("success"):
            raise HTTPException(
                status_code=result.get("status_code", 500),
                detail=result.get("detail", "Failed to set combo porto")
            )

        return {
            "result": 0,  # 0 for success
            "data": result.get("body", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        # Return result 10 for device offline/error
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/planogram/mc-pro-set")
async def mc_pro_set(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    device_id = ""
    wait_result = True
    config_list = {}
    result = await service.batch_config(
        vending_application_id,
        device_id,
        config_list,  # type: ignore
        wait_result
    )

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
        raise HTTPException(
            status_code=500, detail="Failed to config planogram")

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
    result = service.get_ice(device_id, vending_application_id)

    if result["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get ice")

    return result["body"]


@router.post("/planogram/retailset")
async def retail_set(
    request: Request,
    vending_application_id: str = Header(None, alias="Vending-Application-Id")
):
    server_ts = int(time.time() * 1000)

    if not vending_application_id:
        return br_failed(server_ts, -1, "Application id not found")

    try:
        payload = await request.json()
    except Exception:
        return br_failed(server_ts, -2, "Invalid payload")

    result = await service.handle_retail_set(payload, vending_application_id, server_ts)

    if result.get("success"):
        return ok_json(result["data"])
    else:
        return bad_request_json(result["data"])
