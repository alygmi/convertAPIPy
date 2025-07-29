from typing import Any, Dict, List
from repository.planogram_repository import PlanogramRepository
from utils.parser import rget, get
from utils.validation import is_string, is_number, is_bool
import base64
import json

repository = PlanogramRepository()


class PlanogramService:
    def __init__(self):
        self.repo = PlanogramRepository()

    async def batch_config(
        self,
        app_id: str,
        device_id: str,
        config_list: List[Dict[str, Any]],
        wait_result: bool = True
    ) -> Dict[str, Any]:
        try:
            if not config_list:
                return {
                    "status_code": 400,
                    "detail": "Empty config list",
                    "success": False
                }

            payload = {
                "device_id": device_id,
                "payload": config_list,
                "wait_result": wait_result
            }

            result = await self.repo.batch_config(app_id, payload)

            if result.get("status") == "error":
                return {
                    "status_code": result.get("status_code", 500),
                    "detail": result.get("detail", "Repository error"),
                    "success": False
                }

            return {
                "status_code": 200,
                "body": result,
                "success": True
            }

        except Exception as e:
            return {
                "status_code": 500,
                "detail": f"Service error: {str(e)}",
                "success": False
            }

    def config(self, app_id: str, body: dict):
        return self.repo.config(app_id, body)

    def command(self, app_id: str, body: dict):
        return self.repo.command(app_id, body)

    def insert_data(self, app_id: str, body: dict):
        return self.repo.insert(app_id, body)

    def send_sensors(self, app_id: str, body: dict):
        return self.repo.sensors(app_id, body)

    def get_sensors(self, app_id: str, device_id: str):
        return self.repo.get_sensors(app_id, device_id)

    def get_ice(self, app_id: str, device_id: str):
        return self.repo.get_ice(app_id, device_id)

    def get_stock(self, app_id: str):
        return self.repo.get_stock(app_id)

    def get_stock_latest(self, app_id: str):
        return self.repo.get_stock_latest(app_id)

    def get_latest_rfid(self, app_id: str, device_id: str):
        return self.repo.get_latest_rfid(app_id, device_id)

    def get_state_rfid(self, app_id: str, device_id: str):
        return self.repo.get_state_rfid(app_id, device_id)

    async def handle_retail_set(self, payload: dict, application_id: str, server_ts: int):
        errors = []
        device_id, errors = rget(payload, "device_id", errors)
        wait_result = get(payload, "wait_result", True)

        config_sources = {
            "id": ("ids", is_string),
            "name": ("names", is_string),
            "stock": ("stocks", is_number, "cdata"),
            "price": ("prices", is_number),
            "active": ("actives", is_bool),
            "column": ("selections", is_string),
            "image": ("images", is_string),
            "order": ("orders", is_number),
            "active": ("actives_product", is_bool),
            "group": ("groups", is_string),
            "description": ("descriptions", is_string)
        }

        config_list = []

        for param, (key, validator, *rest) in config_sources.items():
            dataset = payload.get(key, {})
            for sensor, val in dataset.items():
                if not validator(val):
                    return {"success": False, "data": {
                        "device_id": device_id,
                        "payload": config_list,
                        "wait_result": wait_result
                    }}
                config_entry = {
                    "sensor": sensor,
                    "param": param,
                    "value": val
                }
                if rest:
                    config_entry["configtype"] = rest[0]
                config_list.append(config_entry)

        ws_result = await repository.batch_config(application_id, {
            "device_id": device_id,
            "payload": config_list,
            "wait_result": wait_result
        })

        body = ws_result.get("body", {})
        result_code = int(body.get("result", -999))

        if result_code == 0:
            return {"success": True, "data": {
                "device_id": device_id,
                "payload": config_list,
                "wait_result": wait_result
            }}

        return {"success": False, "data": {
            "device_id": device_id,
            "payload": config_list,
            "wait_result": wait_result
        }}
