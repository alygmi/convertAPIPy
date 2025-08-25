from typing import Any, Dict, List, Tuple

import httpx
from repository.planogram_repository import PlanogramRepository
from utils.helper import WSResultToMap, parse_coffee_sensors
from utils.parser import rget, get
from utils.planogram import build_config_list, build_config_list_playstation
from utils.response import assess_error
from utils.validation import is_string, is_number, is_bool
import base64
import json

from utils.wsclient import WebSocketClient, WebSocketResult

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

    async def process_playstation_set(self, application_id: str, payload: dict, server_ts: int) -> Tuple[dict, int]:
        try:
            # Decode base64 payload
            decoded_payload = json.loads(
                base64.b64decode(payload["data"]).decode("utf-8"))

            # Validasi payload sesuai implementasi Go
            required_fields = ["device_id", "ids", "names", "prices"]
            for field in required_fields:
                if field not in decoded_payload:
                    return {"result": -3, "error": f"Missing required field: {field}"}, 400

            # Build config list dengan validasi ketat
            config_list = []
            for field, config in [
                ("ids", "id"),
                ("names", "name"),
                ("prices", "price"),
                ("remoteCommands", "remote_command"),
                ("remoteBrands", "remote_brand"),
                ("remoteIds", "remote_id")
            ]:
                if field in decoded_payload:
                    if not isinstance(decoded_payload[field], dict):
                        return {"result": -4, "error": f"Field {field} must be a dictionary"}, 400

                    for sensor, value in decoded_payload[field].items():
                        # Validasi khusus untuk prices dan remoteCommands
                        if field == "prices" and not isinstance(value, dict):
                            return {"result": -5, "error": "Price items must be dictionaries"}, 400
                        if field == "remoteCommands" and not isinstance(value, dict):
                            return {"result": -6, "error": "Remote commands must be dictionaries"}, 400

                        config_list.append({
                            "sensor": str(sensor),
                            "param": config,
                            "value": value
                        })

            # Kirim ke repository
            api_payload = {
                "device_id": decoded_payload["device_id"],
                "payload": config_list,
                "wait_result": decoded_payload.get("wait_result", True)
            }

            ws_result = await self.repo.batch_config_playstation(
                application_id=application_id,
                decoded_payload=api_payload
            )

            # Handle response code 10 khusus
            if ws_result.get("body", {}).get("result") == 10:
                return {
                    "result": 10,
                    "command_id": ws_result["body"].get("command_id"),
                    "device_id": decoded_payload["device_id"],
                    "error": "Invalid configuration (code 10)"
                }, 400

            if ws_result.get("status") != "success":
                return ws_result, 400

            return ws_result.get("body", {}), 200

        except Exception as e:
            return {"result": -999, "error": str(e)}, 500

    async def process_water_dispenser(self, application_id: str, config_data: dict) -> dict:
        """Async version of service method"""
        if not application_id:
            return {
                "result": -1,
                "message": "Application id not found",
                "data": None
            }

        if not config_data.get("device_id"):
            return {
                "result": -2,
                "message": "Device id not found",
                "data": None
            }

        # Panggil repository dengan await
        return await self.repo.batch_config_water_dispenser(application_id, config_data)

    async def process_arcade_set(self, application_id: str, payload: dict):
        """
        Service untuk memanggil repository batch_config_repo.
        """
        try:
            return await repository.batch_config_repo(application_id, payload)
        except Exception as e:
            raise Exception(f"Service error: {str(e)}")

    async def stock_history_service(self, payload: dict, application_id: str, server_ts: int):
        errors = []

        old_planogram = payload.get("latest planogram", {})
        new_planogram = payload.get("newest_planogram", {})
        email = payload.get("email", "")
        device_id = payload.get("device_id", "")

        item_list = []

        for key, old_product in old_planogram.items():
            if "p" in key:
                continue

            if not isinstance(old_product, dict):
                continue

            new_product = new_planogram.get(key)
            if not isinstance(new_product, dict):
                continue

            old_stock = int(old_product.get("stock", 0))
            new_stock = int(new_product.get("stock", 0))

            if old_stock != new_stock:
                value = {
                    "start": old_stock,
                    "end": new_stock,
                    "difference": new_stock - old_stock,
                    "source": "planogram",
                    "type": "update_stock_planogram",
                    "extras": {
                        "ts": server_ts,
                        "user": email
                    }
                }
                item = {
                    "sensor": key,
                    "configtype": "data",
                    "param": "stock_history",
                    "value": value
                }
                item_list.append(item)

        body = {
            "device_id": device_id,
            "payload": item_list
        }

        # send to repository
        ws_result = await repository.send_insert(application_id, body)
        return ws_result


class CoffeeService:
    def __init__(self):
        self.ws_client = WebSocketClient()

    async def coffee_franke_set(self, application_id: str, payload: dict, server_ts: int):
        """
        Kirim planogram ke mesin Coffee Franke via websocket.
        Response dibungkus ke dict supaya aman dipakai .get()
        """
        # --- panggil websocket, ganti sesuai fungsi yg memang kamu pakai ---
        raw_response = await send_ws(
            application_id=application_id,
            action="coffee.franke.set",
            data=payload,
            server_ts=server_ts
        )

        # pastikan response selalu dict
        response = WSResultToMap(raw_response)

        # cek kalau ada error message
        if response.get("error"):
            raise Exception(f"Coffee Franke error: {response['error']}")

        # ambil result code (bisa 'result' atau 'code')
        result_code = response.get("result") or response.get("code")

        if result_code is None:
            raise Exception(
                f"Coffee Franke set gagal, response tidak valid: {response}")

        # 0 = sukses, 10 = mesin offline (anggap wajar, tidak error)
        if result_code not in (0, 10):
            raise Exception(
                f"Coffee Franke set failed, code: {result_code}, response: {response}")

        return response
