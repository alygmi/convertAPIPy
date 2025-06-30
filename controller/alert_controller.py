from fastapi import APIRouter, Header, Query, HTTPException
from services.alert_services import AlertService
import time

router = APIRouter()
service = AlertService()

@router.get("/alerts")
def get_alerts(vending_application_id: str = Header(...)):
    devices_resp = service.list_device(vending_application_id)
    if devices_resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Device list failed")

    result = []
    for device in devices_resp["body"].get("devices", []):
        device_id = device.get("id")
        device_name = device.get("name")

        alert_resp = service.alert_get(vending_application_id, device_id)
        if alert_resp["status_code"] != 200:
            continue

        for alert in alert_resp["body"].get("states", []):
            alert["device_id"] = device_id
            alert["device_name"] = device_name
            if alert.get("value") != "false":
                result.append(alert)

    return result

@router.get("/alerts/device")
def get_alert_by_device(
    vending_application_id: str = Header(...),
    device_id: str = Query(...)
):
    resp = service.alert_get_by_device(vending_application_id, device_id)
    if resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get alert")

    return resp["body"].get("states", [])

@router.get("/alerts/device/history")
def get_alert_historical_by_device(
    vending_application_id: str = Header(...),
    device_id: str = Query(...),
    key: str = Query(...),
    start: int = Query(...),
    end: int = Query(...)
):
    resp = service.alert_historical_by_device(vending_application_id, device_id, key, start, end)
    if resp["status_code"] != 200:
        raise HTTPException(status_code=500, detail="Failed to get historical alert")

    return resp["body"].get("state_data", [])
