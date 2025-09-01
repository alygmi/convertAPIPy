from datetime import datetime, timezone
import json
import time
import pytz
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from services.planogram_services import CoffeeService, PlanogramService
from utils import helper
from utils.helper import PayloadEncryptedMap, PayloadMap, RGet, WSResultToMap, parse_coffee_le_vending_configs, parse_coffee_le_vending_sensors
from utils.parser import get, rget, safe_rget
from utils.planogram import decode_base64_payload, build_config_list, get_payload_encrypted_map
from utils.response import assess_error, ok_json, bad_request_json, br_failed
from utils.validation import is_number
from utils.object import IsBool, IsDict, IsList, IsNumber, IsString

router = APIRouter()
service = PlanogramService()
coffee = CoffeeService()

# set planogram


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


@router.post("/planogram/coffee-franke/set")
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


@router.post("/coffeealegria/set")
async def coffee_alegria_set(
    request: Request,
    vending_application_id: Optional[str] = Header(
        None, alias="Vending-Application-Id")
):
    server_ts = int(time.time() * 1000)

    # Headers check
    if not vending_application_id:
        return br_failed(server_ts, -1, "Application id not found")

    # Payload body
    payload, err = await PayloadEncryptedMap(request)
    if err:
        return br_failed(server_ts, -2, "Invalid payload")

    errors: List[Exception] = []

    device_id, errors, = rget(payload, "device_id", errors)
    timeout, errors, = rget(payload, "timeout", errors)
    wait_result = get(payload, "wait_result", True)

    ids, errors = rget(payload, "ids", errors)
    names, errors = rget(payload, "names", errors)
    prices, errors = rget(payload, "prices", errors)
    actives, errors = rget(payload, "actives", errors)
    bypass, errors = rget(payload, "bypass", errors)

    config_list: List[Dict[str, Any]] = []

    # payment timeout
    config_list.append({
        "sensor": "payment",
        "param": "timeout",
        "value": timeout
    })

    # ids
    for column, val in (ids or {}).items():
        if not IsString(val):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "id",
            "value": val
        })

    # names
    for column, val in (names or {}).items():
        if not IsString(val):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "name",
            "value": val
        })

    # prices
    for column, val in (prices or {}).items():
        if not IsNumber(val):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "price",
            "value": val
        })

    # actives
    for column, val in (actives or {}).items():
        if not IsBool(val):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "active",
            "value": val
        })

    # bypass
    for column, val in (bypass or {}).items():
        if not IsBool(val):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "bypass",
            "value": val
        })

    # group per sensor
    config_map: Dict[str, List[Dict[str, Any]]] = {}
    for config in config_list:
        sensor = config["sensor"]
        if sensor not in config_map:
            config_map[sensor] = []
        config_map[sensor].append({
            "sensor": config["sensor"],
            "param": config["param"],
            "value": config["value"]
        })

    print("ConfigMap per sensor:", config_map)

    latest_response: Dict[str, Any] = {}

    for sensor, configs in config_map.items():
        payload_sensor = []
        for cfg in configs:
            payload_sensor.append({
                "sensor": cfg["sensor"],
                "param": cfg["param"],
                "value": cfg["value"]
            })

        print(sensor)
        print(payload_sensor)

        wsresult = await service.batch_config(
            app_id=vending_application_id,
            device_id=str(device_id),
            config_list=configs,
            wait_result=bool(wait_result)
        )

        body = wsresult["Body"]
        result_code = int(body["result"])
        response = WSResultToMap(wsresult)
        latest_response = response
        SUCCESS = 0

        if result_code != SUCCESS:
            print(f"Failed to send config for sensor {sensor}")
            return bad_request_json(response)

        print(f"Successfully sent config for sensor {sensor}")

    return ok_json(latest_response)


@router.post("/coffee-milano/set")
async def coffee_milano_set(
    request: Request,
    vending_application_id: str = Header(None, alias="Vending-Application-Id"),
):
    # Server time
    server_ts = int(time.time() * 1000)

    # Headers
    if not vending_application_id:
        return br_failed(server_ts, -1, "Application id not found")

    # Payload body
    payload, err = await PayloadEncryptedMap(request)
    if err:
        return br_failed(server_ts, -2, "Invalid payload")

    errors = []

    # Extract fields
    device_id, errors = rget(payload, "device_id", errors)
    wait_result = get(payload, "wait_result", True)

    ids, errors = rget(payload, "ids", errors)
    names, errors = rget(payload, "names", errors)
    prices, errors = rget(payload, "prices", errors)

    config_list = []

    # IDs
    for column, val in (ids or {}).items():
        if not isinstance(val, str):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "id",
            "value": val,
        })

    # Names
    for column, val in (names or {}).items():
        if not isinstance(val, str):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "name",
            "value": val,
        })

    # Prices
    for column, val in (prices or {}).items():
        if not isinstance(val, (int, float)):
            return br_failed(server_ts, -3, "Invalid payload")
        config_list.append({
            "sensor": column,
            "param": "price",
            "value": val,
        })

    # Call service
    wsresult = await service.batch_config(
        app_id=vending_application_id,
        device_id=str(device_id),
        config_list=config_list,
        wait_result=bool(wait_result)
    )

    body = wsresult.get("body", {})
    result_code = int(body.get("result", -999))
    response = WSResultToMap(wsresult)
    SUCCESS = 0

    if result_code == SUCCESS:
        return ok_json(response)

    return bad_request_json(response)


@router.post("/planogram/coffee-levanding/set")
async def coffee_levanding_set(self, request: Request):
    server_ts = int(datetime.now().timestamp() * 1000)
    now = datetime.fromtimestamp(server_ts / 1000)

    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    payload, err = await PayloadEncryptedMap(request)
    if err:
        return br_failed(server_ts, -2, "Invalid payload")

    errors = []
    device_id, errors = rget(payload, "id", errors)
    wait_result = get(payload, "wait_result", True)
    configs, errors = rget(payload, "configs", errors)

    err = assess_error(errors)
    if err:
        return br_failed(server_ts, -3, "Invalid payload")

    if configs is None:
        configs = []

    sensors, err = parse_coffee_le_vending_configs(configs)
    if err:
        return br_failed(server_ts, -4, "Error parsing")

    wsresult = await self.sendservice.Sensors(application_id, {
        "device_id": device_id,
        "sensors": sensors,
        "wait_result": wait_result,
        "keep": ["payment", "sampling", "stock", "user", "canceltrx", "confirmation", "ir_sensor"],
    })

    body_ws = wsresult.Body
    result_code = int(body_ws.get("result", -99))

    if result_code != helper.Result.SUCCESS:
        return bad_request_json(WSResultToMap(wsresult))

    tz = pytz.timezone("Asia/Jakarta")
    return ok_json({
        "time": now.astimezone(tz).strftime("%y-%m-%d %H:%M:%S"),
        "status_desc": "update_planogram_success",
        "status": "success",
        "status_code": 0,
    })


# get planogram
@router.get("/planogram/sensors/get")
async def sensors_get(self, request: Request, device_id: str = Query(...)):
    server_ts = int(datetime.now().timestamp() * 1000)
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    wsresult = await self.getservice.GetSensors(application_id, device_id)
    body_ws = wsresult.Body
    result_code = int(body_ws.get("result", -99))
    if result_code != helper.Result.SUCCESS:
        return bad_request_json(WSResultToMap(wsresult))
    return ok_json(wsresult.Body)


@router.get("/planogram/coffee-levanding/get")
async def CoffeeLevendingGet(self, request: Request, device_id: str = Query(...)):
    server_ts = int(datetime.now().timestamp() * 1000)
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    errors = []
    wsresult = await self.getservice.GetSensors(application_id, device_id)
    body_ws = wsresult.Body
    result_code = int(body_ws.get("result", -99))
    if result_code != helper.Result.SUCCESS:
        return bad_request_json(helper.WSResultToMap(wsresult))

    sensors, errors = rget(body_ws, "sensors", errors)
    id_map, price_map, order_map, active_map, ingredient_map, recipe_map, stock_map, ice_map = {
    }, {}, {}, {}, {}, {}, {}, {}
    sorted_list = []

    for d in (sensors or []):
        if not isinstance(d, dict):
            continue
        key, errors = rget(d, "key", errors)
        sensor, errors = rget(d, "sensor", errors)
        latest_data, errors = rget(d, "latest_data", errors)
        if isinstance(key, str) and ":config:id" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            id_map[sensor] = value
            sorted_list.append(sensor)
        elif isinstance(key, str) and ":config:price" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            price_map[sensor] = value
        elif isinstance(key, str) and ":config:order" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            order_map[sensor] = value
        elif isinstance(key, str) and ":config:active" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            active_map[sensor] = value
        elif isinstance(key, str) and ":config:ingredient" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            ingredient_map[sensor] = value
        elif isinstance(key, str) and ":cdata:recipe" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            recipe_map[sensor] = value
        elif isinstance(key, str) and ":cdata:stock" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            stock_map[sensor] = value

    # Get ice sensors
    result_ice = await self.getservice.GetIce(application_id, device_id)
    if result_ice.Code != helper.Result.HTTP_OK:
        return bad_request_json(helper.WSResultToMap(result_ice))

    sensors_data, errors = rget(
        result_ice.Body, "sensors", errors)
    sensors_ice, errors = safe_rget(sensors_data, "detail", errors)
    for sensor, key in (sensors_ice or {}).items():
        if ":ice" in sensor:
            sensor_id = sensor.split(":")[0]
            ice_map[sensor_id] = key

    keys = ["SELECTION", "SKU", "HARGA",
            "ORDER", "ACTIVE", "INGREDIENT", "ICE"]
    table_data = []
    for key in sorted_list:
        id_, errors = rget(id_map, key, errors)
        price, errors = rget(price_map, key, errors)
        order, errors = rget(order_map, key, errors)
        active, errors = rget(active_map, key, errors)
        ingredient, errors = rget(ingredient_map, key, errors)
        ice, errors = rget(ice_map, key, errors)
        recipe, errors = rget(recipe_map, key, errors)
        stock, errors = rget(stock_map, key, errors)

        table_data.append({
            "SELECTION": {"value": key, "success": True, "status": ""},
            "SKU": {"value": id_, "success": True, "status": ""},
            "HARGA": {"value": price or 0, "success": True, "status": ""},
            "ORDER": {"value": order or 0, "success": True, "status": ""},
            "ACTIVE": {"value": active or False, "success": True, "status": ""},
            "INGREDIENT": {"value": ingredient or {}, "success": True, "status": ""},
            "ICE": {"value": ice or {}, "success": True, "status": ""},
            "STOCK": {"value": stock or {}, "success": True, "status": ""},
            "RECIPE": {"value": recipe or {}, "success": True, "status": ""},
        })

    formatted_time = datetime.now(timezone.utc).isoformat()
    response = {
        "device_id": device_id,
        "table_data": table_data,
        "table_keys": keys,
        "time": formatted_time,
        "status_desc": "list_planogram_success",
        "status": "success",
        "status_code": 0,
        "stock_map": stock_map,
        "recipe_map": recipe_map,
    }
    return ok_json(response)


@router.get("/planogram/coffee-franke/get")
async def CoffeeFrankeGet(self, request: Request, device_id: str = Query(...)):
    server_ts = int(datetime.now().timestamp() * 1000)
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        return br_failed(server_ts, -1, "Application id not found")

    errors = []
    wsresult = await self.getservice.GetSensors(application_id, device_id)
    body_ws = wsresult.Body
    result_code = int(body_ws.get("result", -99))
    if result_code != helper.Result.SUCCESS:
        return bad_request_json(WSResultToMap(wsresult))

    sensors, errors = rget(body_ws, "sensors", errors)
    id_map, name_map, price_map = {}, {}, {}
    sorted_list = []

    for d in (sensors or []):
        if not isinstance(d, dict):
            continue
        key, errors = rget(d, "key", errors)
        sensor, errors = rget(d, "sensor", errors)
        latest_data, errors = rget(d, "latest_data", errors)
        if isinstance(key, str) and ":config:id" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            id_map[sensor] = value
            sorted_list.append(sensor)
        elif isinstance(key, str) and ":config:price" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            price_map[sensor] = value
        elif isinstance(key, str) and ":config:name" in key:
            value, errors = safe_rget(latest_data, "value", errors)
            name_map[sensor] = value

    keys = ["SELECTION", "SKU", "NAME", "HARGA"]
    table_data = []
    for key in sorted_list:
        id_, errors = rget(id_map, key, errors)
        name, errors = rget(name_map, key, errors)
        price, errors = rget(price_map, key, errors)

        table_data.append({
            "SELECTION": {"value": key, "success": True, "status": ""},
            "SKU": {"value": id_, "success": True, "status": ""},
            "NAME": {"value": name or "", "success": True, "status": ""},
            "HARGA": {"value": price or 0, "success": True, "status": ""},
        })

    formatted_time = datetime.now(timezone.utc).isoformat()
    response = {
        "device_id": device_id,
        "table_data": table_data,
        "table_keys": keys,
        "time": formatted_time,
        "status_desc": "list_planogram_success",
        "status": "success",
        "status_code": 0,
    }
    return ok_json(response)


@router.get("/planogram/coffee-milano/get")
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

# todo


@router.get("/stock")
async def stock_get(request: Request):
    server_ts = int(datetime.now().timestamp() * 1000)

    # Header
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        raise HTTPException(status_code=400, detail="Application id not found")

    # Call service GetStock
    wsresult = await service.get_stock(application_id)
    body_ws = wsresult["Body"]
    result_code = int(body_ws.get("result", -1))

    if result_code != helper.Result.SUCCESS:
        return bad_request_json(WSResultToMap(wsresult))

    # Filter sensors
    sensors, errors, _ = rget(body_ws, "sensors")
    list_sensor = []
    for d in sensors or []:
        if not isinstance(d, dict):
            continue
        latest_configtype, _, _ = rget(d, "configtype")
        latest_param, _, _ = rget(d, "param")

        if latest_configtype == "data" and latest_param == "stock":
            sensor, _, _ = rget(d, "sensor")
            device_id, _, _ = rget(d, "device_id")
            data_valid = {
                "sensor": sensor,
                "device_id": device_id,
            }
            list_sensor.append(data_valid)

    # Call service GetStockLatest
    wsresult_latest = await service.get_stock_latest(application_id)
    if wsresult_latest["Code"] != helper.Result.HTTP_OK:
        return bad_request_json(WSResultToMap(wsresult_latest))

    ws_latest_body = wsresult_latest["Body"]
    latest_data, _, _ = rget(ws_latest_body, "sensors")
    data_stock = []
    for d in latest_data or []:
        if not isinstance(d, dict):
            continue
        sensor, _, _ = rget(d, "sensor")
        device_id, _, _ = rget(d, "device_id")

        data_check = {
            "sensor": sensor,
            "device_id": device_id,
        }
        if service.contains_map(list_sensor, data_check):
            data_stock.append(d)

    return ok_json(data_stock)
