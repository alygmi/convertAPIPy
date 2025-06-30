from fastapi import APIRouter
from controller import account_controller, bussinesspoint_controller, payout_controller, alert_controller
from database import Base, engine


Base.metadata.create_all(bind=engine)
app = APIRouter()
app.include_router(account_controller.router)
app.include_router(bussinesspoint_controller.router)
app.include_router(payout_controller.router)
app.include_router(alert_controller.router)