from fastapi import APIRouter, Header, Query, Body, HTTPException
from services.subs_services import SubsService

router = APIRouter()
service = SubsService()

@router.get("/get-device-non-subs")
def get_device_non_subs(vending_application_id: str = Header(...)):
    res = service.list_device_non_sub(vending_application_id)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.get("/get-device-per-tags")
def get_device_per_tags(
    key: str,
    vending_application_id: str = Header(...)
):
    res = service.get_device_per_tags(vending_application_id, key)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.get("/get-subs")
def get_subs(vending_application_id: str = Header(...)):
    res = service.get_subs(vending_application_id)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.post("/cancel-subs")
def cancel_subs(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    order_id = payload.get("order_id")
    res = service.cancel_subs(vending_application_id, {
        "application_id": vending_application_id,
        "transaction_id": order_id
    })
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.post("/create-payment-subs")
def create_payment_subs(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    data = {
        "application_id": vending_application_id,
        "amount": payload.get("price"),
        "method": "QRIS-MIDTRANS",
        "name": payload.get("name"),
        "phone": payload.get("phone")
    }
    res = service.create_subs(vending_application_id, data)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.post("/extend-subs")
def extend_subs(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    res = service.create_subs(vending_application_id, payload)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.post("/untag-subs")
def untag_subs(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    res = service.untag_subs(vending_application_id, payload)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]

@router.post("/update-subs")
def update_subs(
    vending_application_id: str = Header(...),
    payload: dict = Body(...)
):
    res = service.update_subs(vending_application_id, payload)
    if res["status_code"] != 200:
        raise HTTPException(status_code=500, detail=res["body"])
    return res["body"]