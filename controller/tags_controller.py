from fastapi import APIRouter, Request, HTTPException
from services.tags_service import TagsService

router = APIRouter()
tags_service = TagsService()


@router.get("/tags")
async def get_tags(request: Request):
    application_id = request.headers.get("Vending-Application-Id")
    if not application_id:
        raise HTTPException(status_code=400, detail="Application id not found")
    return tags_service.list(application_id)


@router.post("/tags")
async def create_tags(request: Request):
    application_id = request.headers.get("Vending-Application-Id")
    body = await request.json()
    return tags_service.create(application_id, body)


@router.post("/tags/apply")
async def apply_tags(request: Request):
    application_id = request.headers.get("Vending-Application-Id")
    body = await request.json()
    return tags_service.apply(application_id, body)


@router.post("/tags/remove")
async def remove_tags(request: Request):
    application_id = request.headers.get("Vending-Application-Id")
    body = await request.json()
    return tags_service.remove(application_id, body)


@router.post("/tags/delete")
async def delete_tags(request: Request):
    application_id = request.headers.get("Vending-Application-Id")
    body = await request.json()
    return tags_service.delete(application_id, body)
