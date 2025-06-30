from fastapi import APIRouter, Header, Query, Body, HTTPException
from services.planogram_services import PlanogramService  # karena sudah include send & get
import time

router = APIRouter()
service = PlanogramService()

@router.get("/user-rfid-get")
def user_rfid_get(
    device_id: str,
    vending_application_id: str = Header(...)
):
    ts = int(time.time() * 1000)

    sensors_resp = service.get_latest_rfid(vending_application_id, device_id)
    if sensors_resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get latest RFID")

    value = sensors_resp["body"].get("sensors", [{}])[0].get("latest_data", {}).get("value", {})

    state_resp = service.get_state_rfid(vending_application_id, device_id)
    if state_resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get RFID state")

    value_state = state_resp["body"].get("sensors", [{}])[0].get("latest_data", {}).get("value", {})

    table_data = []
    for rfid in value:
        table_data.append({
            "RFID": {"value": rfid, "success": True, "status": ""},
            "QUOTA": {"value": value[rfid], "success": True, "status": ""},
            "STATE": {"value": value_state.get(rfid, 0), "success": True, "status": ""},
        })

    return {
        "response": {
            "code": 200,
            "body": {
                "device_id": device_id,
                "table_data": table_data,
                "table_keys": ["RFID", "QUOTA", "STATE"],
                "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status_desc": "list_users_success",
                "status": "success",
                "status_code": 0,
            }
        }
    }

@router.post("/user-rfid-set")
def user_rfid_set(
    vending_application_id: str = Header(...),
    body: dict = Body(...)
):
    device_id = body.get("id")
    configs = body.get("configs", [])

    # Konversi sesuai ParseRfidSensors (di Go helper)
    try:
        value = []
        for cfg in configs:
            rfid = cfg.get("RFID", {}).get("value")
            quota = cfg.get("QUOTA", {}).get("value")
            if rfid is not None and quota is not None:
                value.append({"id": rfid, "quota": quota})
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid sensor config")

    resp = service.config(vending_application_id, {
        "device_id": device_id,
        "sensor": "user",
        "configtype": "config",
        "param": "rule",
        "value": value
    })

    if resp["body"].get("result") != 1:
        raise HTTPException(status_code=500, detail="Failed to update RFID")

    return {
        "time": time.strftime("%y-%m-%d %H:%M:%S", time.localtime()),
        "status_desc": "update_planogram_success",
        "status": "success",
        "status_code": 0
    }
