from datetime import datetime
import json
import time
from typing import Dict
from fastapi import APIRouter, Depends, Header, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from services.planogram_services import CoffeeService, PlanogramService
from utils.helper import PayloadMap, WSResultToMap
from utils.parser import get, rget
from utils.planogram import decode_base64_payload, build_config_list, get_payload_encrypted_map
from utils.response import assess_error, ok_json, bad_request_json, br_failed
from utils.validation import is_number

router = APIRouter()
service = PlanogramService()
coffee = CoffeeService()


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


@router.post("/planogram/playstationset")
async def playstation_set(
    request: Request,
    vending_application_id: str = Header(..., alias="Vending-Application-Id")
):
    server_ts = int(time.time() * 1000)

    try:
        payload = await request.json()

        result, status_code = await service.process_playstation_set(
            vending_application_id,
            payload,
            server_ts
        )

        response_data = {
            "status": "success" if status_code == 200 else "error",
            "ts": server_ts,
            **result
        }

        return JSONResponse(
            content=response_data,
            status_code=status_code
        )

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "ts": server_ts,
                "result": -2,
                "message": "Invalid JSON payload"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "ts": server_ts,
                "result": -999,
                "message": str(e)
            }
        )


@router.post("/api/water-dispenser/set")
async def water_dispenser_set(
    request: Request,
    vending_application_id: str = Header(..., alias="Vending-Application-Id")
):
    server_ts = int(datetime.now().timestamp() * 1000)

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "server_ts": server_ts,
                "result": -2,
                "message": "Invalid payload"
            }
        )

    errors = []

    # Get all parameters using rget
    device_id, errors = rget(payload, "device_id", errors)
    wait_result = payload.get("wait_result", True)

    water_duration, errors = rget(payload, "durationWater", errors)
    water_price, errors = rget(payload, "priceWater", errors)
    cup_duration, errors = rget(payload, "durationCup", errors)
    cup_price, errors = rget(payload, "priceCup", errors)
    cup_stock, errors = rget(payload, "stockCup", errors)

    if errors:
        return JSONResponse(
            status_code=400,
            content={
                "server_ts": server_ts,
                "result": -3,
                "message": "Invalid payload: " + ", ".join(errors)
            }
        )

    config_list = []

    if water_duration is not None:
        config_list.append({
            "sensor": "water",
            "param": "duration",
            "value": int(water_duration)
        })

    if water_price is not None:
        config_list.append({
            "sensor": "water",
            "param": "price",
            "value": int(water_price)
        })

    if cup_duration is not None:
        config_list.append({
            "sensor": "water_cup",
            "param": "duration",
            "value": int(cup_duration)
        })

    if cup_price is not None:
        config_list.append({
            "sensor": "water_cup",
            "param": "price",
            "value": int(cup_price)
        })

    if cup_stock is not None:
        config_list.append({
            "sensor": "water_cup",
            "configtype": "cdata",
            "param": "stock",
            "value": int(cup_stock)
        })

    result = await service.process_water_dispenser(
        application_id=vending_application_id,
        config_data={
            "device_id": device_id,
            "payload": config_list,
            "wait_result": wait_result
        }
    )

    if result.get("result") == 0:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": result
            }
        )
    else:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "data": result
            }
        )

    return ok_json(result) if result.get("result") == 0 else bad_request_json(result)


@router.post("/planogram/arcadeset")
async def arcade_set(request: Request):
    server_ts = int(datetime.now().timestamp() * 1000)

    # Headers
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    # Payload body
    try:
        payload, err = await PayloadMap(request)
        if err is not None:
            return br_failed(server_ts, -2, "Invalid payload")
    except Exception:
        return br_failed(server_ts, -2, "Invalid payload")

    errors = []

    device_id, errors = rget(payload, "device_id", errors)
    wait_result = get(payload, "wait_result", True)
    pulse, errors = rget(payload, "pulse", errors)
    price_data, errors = rget(payload, "price", errors)

    try:
        assess_error(errors)
    except Exception:
        return br_failed(server_ts, -3, "Invalid payload")

    if not is_number(pulse):
        return br_failed(server_ts, -3, "Invalid payload")

    config_list = [
        {
            "sensor": "arcade",
            "param": "pulse_factor",
            "value": pulse
        },
        {
            "sensor": "arcade",
            "param": "price",
            "value": price_data
        }
    ]

    try:
        wsresult = await service.process_arcade_set(application_id, {
            "device_id": device_id,
            "payload": config_list,
            "wait_result": wait_result
        })

        # Handle response dari internal API
        result_code = int(wsresult.get("result", -1))
        command_id = wsresult.get("command_id", "")

        # DEFINE RESULT CODES
        SUCCESS = 0
        DEVICE_OFFLINE = 10  # Device mati/offline

        response = {
            "result": result_code,
            "command_id": command_id,
            "device_id": device_id
        }

        if result_code == SUCCESS:
            response["message"] = "Command executed successfully"
            return ok_json(response)

        elif result_code == DEVICE_OFFLINE:
            # BUKAN ERROR! Command berhasil dikirim, tapi device offline
            response["message"] = "Command queued successfully but device is currently offline"
            # Masih return 200 OK karena bukan error sistem
            return ok_json(response)

        else:
            # Other error codes (real errors)
            response["message"] = f"Operation failed with code {result_code}"
            return bad_request_json(response)

    except Exception as e:
        return br_failed(server_ts, -5, f"Internal server error: {str(e)}")


@router.post("/planogram/stock/history")
async def stock_history(
    request: Request,
    vending_application_id: str = Header(..., alias="Vending-Application-Id")
):
    server_ts = int(time.time() * 1000)

    if not vending_application_id:
        return br_failed(server_ts, -1, "Application Id not found")

    # parse payload
    try:
        payload = await request.json()

    except Exception:
        return br_failed(server_ts, -1, "Invalid Payload")

    # service
    ws_result = await service.stock_history_service(
        payload=payload,
        application_id=vending_application_id,
        server_ts=server_ts
    )

    # print("ws Result:", ws_result)

    # ws_result handler
    if ws_result.code != 200:
        return bad_request_json(ws_result.body)

    return ok_json({"code": 1})


@router.post("/planogram/coffee-franke-set")
async def coffee_franke_set(
    request: Request,
    application_id: str = Header(None, alias="Vending-Application-Id"),
):
    server_ts = int(datetime.now().timestamp() * 1000)

    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    payload, err = await get_payload_encrypted_map(request)
    if err:
        return br_failed(server_ts, -2, "Invalid payload")

    response = await coffee.coffee_franke_set(application_id, payload, server_ts)
    if response.get("error"):
        return br_failed(server_ts, response["code"], response["message"])

    result_code = response["result"]
    if result_code != 0:  # SUCCESS
        return bad_request_json(response)

    return ok_json(response)


@router.get("/planogram/coffee-milano")
async def coffee_milano_get(
    request: Request,
    id: str = Query(..., description="Device ID yang akan diambil datanya")
):
    # ambil header
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        raise HTTPException(status_code=400, detail="Application id not found")

    # proses ke service
    result = await service.get_planogram(application_id, id)

    # handle error dari service
    if "error" in result:
        return bad_request_json(result["body"])

    # sukses
    return ok_json(result)
