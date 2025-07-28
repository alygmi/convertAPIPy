from fastapi import APIRouter
from controller import account_controller, bussinesspoint_controller, payout_controller, alert_controller, planogram_controller, bank_controller, rfid_controller, subs_controller, tags_controller, task_controller
from database import Base, engine


Base.metadata.create_all(bind=engine)
app = APIRouter()
app.include_router(account_controller.router)
app.include_router(bussinesspoint_controller.router)
app.include_router(payout_controller.router)
app.include_router(alert_controller.router)
app.include_router(planogram_controller.router)
app.include_router(bank_controller.router)
app.include_router(rfid_controller.router)
app.include_router(subs_controller.router)
app.include_router(task_controller.router)
app.include_router(tags_controller.router)
