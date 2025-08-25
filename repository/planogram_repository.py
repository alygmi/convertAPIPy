import json
import time
from typing import Any, Dict
from config.settings import settings
from utils.planogram import build_config_list
from utils.wsclient import WebSocketClient
from utils.web_services import WSResult, WebService

import requests
import os
import httpx

ws = WebSocketClient()

headers = {
    'Iotera-Internal-Api-Token': '1711f6e884b5d0c90cdf239553ba58b96b2315fb7132851b77cb3d426f826f04',
    'Iotera-Application-Id': "1000000021"
}


class PlanogramRepository:
    def __init__(self):
        self.base_url = settings.INTERNAL_PLATFORM_API_BASE_URL
        self.token = settings.INTERNAL_PLATFORM_API_TOKEN

    def _headers(self, app_id):
        return {
            "Content-Type": f"application/json",
            "Iotera-Internal-Api-Token": self.token,
            "Iotera-Application-Id": app_id,
        }

    def _post(self, url, body, app_id):
        try:
            r = requests.post(
                url, json=body, headers=self._headers(app_id), timeout=180)
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "body": {"result": -1, "message": str(e)}}

    def _get(self, url, params, app_id):
        try:
            r = requests.get(url, params=params,
                             headers=self._headers(app_id), timeout=90)
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "body": {"result": -1, "message": str(e)}}

    def command(self, app_id, body):
        return self._post(f"{self.base_url}/send/command", body, app_id)

    def config(self, app_id, body):
        return self._post(f"{self.base_url}/send/config", body, app_id)

    def batch_command(self, app_id, body):
        return self._post(f"{self.base_url}/send/command/batch", body, app_id)

    async def batch_config(self, app_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/send/config/batch"
        headers = self._headers(app_id)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                return {
                    "status": "success",
                    "status_code": response.status_code,
                    "body": response.json(),
                    "success": True
                }

        except httpx.HTTPStatusError as exc:
            return {
                "status": "error",
                "status_code": exc.response.status_code,
                "detail": str(exc),
                "success": False
            }
        except httpx.RequestError as exc:
            return {
                "status": "error",
                "status_code": 503,
                "detail": f"Network error: {str(exc)}",
                "success": False
            }
        except Exception as exc:
            return {
                "status": "error",
                "status_code": 500,
                "detail": f"Unexpected error: {str(exc)}",
                "success": False
            }

        print(url)
        print(headers)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=body, headers=headers)
                print("Request URL:", url)
                print("Payload:", payload)
                print("Response status:", response.status_code)
                print("Response body:", response.text)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {
                "status": "error",
                "status_code": exc.response.status_code,
                "detail": str(exc)
            }
        except Exception as exc:
            return {
                "status": "error",
                "detail": str(exc)
            }

    async def batch_config_playstation(self, application_id: str, decoded_payload: dict) -> dict:
        url = f"{self.base_url}/send/config/batch"
        headers = {
            "Vending-Application-Id": application_id,
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=decoded_payload, headers=headers)
                response.raise_for_status()
                return {
                    "status": "success",
                    "body": response.json()
                }
        except httpx.HTTPStatusError as e:
            try:
                error_body = e.response.json()
            except:
                error_body = {"result": 10, "message": str(e)}

            return {
                "status": "error",
                "status_code": e.response.status_code,
                "body": error_body,
                "error": str(e)
            }

    @staticmethod
    async def batch_config_water_dispenser(application_id: str, config_data: dict) -> dict:
        """Async version of repository method"""
        # Implementasi async untuk berkomunikasi dengan database/device
        # Contoh simulasi:
        return {
            "result": 0,
            "message": "Configuration applied successfully",
            "data": config_data
        }

        if not config_data.get("device_id"):
            return {
                "result": -2,
                "message": "Device id not found",
                "data": None
            }

        # Panggil repository dengan await
        return await self.repo.batch_config(application_id, config_data)

    async def batch_config_repo(self, application_id: str, payload: dict):
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/send/config/batch"
        headers = {
            "Iotera-Application-Id": application_id,
            "Iotera-Internal-Api-Token": settings.INTERNAL_PLATFORM_API_TOKEN,
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=180.0)

            # Untuk semua response (200, 400, dll), return JSON-nya
            # Biarkan business logic yang handle result codes
            return resp.json()

    async def send_insert(self, application_id: str, body: dict) -> WSResult:
        """
        body di sini masih payload mentah dari client (punya latest_planogram, planogram, dll).
        Repository yang menyesuaikan format supaya API internal bisa baca.
        """

        # ambil device_id dari payload
        device_id = body.get("id", "")
        email = body.get("email", "")
        latest_planogram = body.get("latest_planogram", {})
        new_planogram = body.get("planogram", {})

        # timestamp server
        server_ts = int(time.time() * 1000)

        item_list = []

        # compare old vs new stock
        for key, old_product in latest_planogram.items():
            # skip key yang mengandung "P"
            print("DEBUG key:", key, "old_product:", old_product)

            if "P" in key:
                continue

            new_product = new_planogram.get(key)
            print("DEBUG new_product:", new_product)

            if not isinstance(new_product, dict):
                continue

            old_stock = int(old_product.get("stock", 0))
            new_stock = int(new_product.get("stock", 0))
            print("DEBUG stocks:", old_stock, new_stock)

            if old_stock != new_stock:
                value = {
                    "start": old_stock,
                    "end": new_stock,
                    "difference": new_stock - old_stock,
                    "source": "planogram",
                    "type": "update_stock_planogram",
                    "extras": {
                        "ts": server_ts,
                        "user": email,
                    },
                }
                item = {
                    "sensor": key,
                    "configtype": "data",
                    "param": "stock_history",
                    "value": value,
                }
                item_list.append(item)

                print("item:", item)
        # body final sesuai format API internal
        final_body = {
            "device_id": device_id,
            "payload": item_list,
        }

        headers = {
            "Iotera-Application-Id": application_id,
            "Iotera-Internal-Api-Token": settings.IOTERA_INTERNAL_API_TOKEN,
            "Content-Type": "application/json",
        }

        if settings.INTERNAL_PLATFORM_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_PLATFORM_API_TOKEN}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                print("=== DEBUG REQUEST ===")
                print("URL:", settings.INTERNAL_PLATFORM_API_BASE_URL)
                print("Headers:", headers)
                print("Body:", final_body)

                resp = await client.post(settings.INTERNAL_PLATFORM_API_BASE_URL, json=final_body, headers=headers)

                try:
                    resp_body = resp.json()
                except Exception:
                    resp_body = {"raw": resp.text}

                print("=== DEBUG RESPONSE ===")
                print("HTTP Status:", resp.status_code)
                print("Response Body:", resp_body)

                status_val = resp_body.get("status")

                if status_val in (0, 10):
                    return WSResult(code=resp.status_code, body=resp_body)
                else:
                    return WSResult(code=resp.status_code, body=resp_body)

            except Exception as e:
                return WSResult(code=500, body={"error": str(e)})

    async def send_sensors(self, application_id: str, data: dict):
        return await ws.send("Sensors", application_id, data)

    def insert(self, app_id, body):
        return self._post(f"{self.base_url}/data/insert", body, app_id)

    def sensors(self, app_id, body):
        return self._post(f"{self.base_url}/send/sensors", body, app_id)

    def get_sensors(self, app_id, device_id):
        return self._get(f"{self.base_url}/device/sensor/list/data/latest", {"device_id": device_id}, app_id)

    def get_ice(self, app_id, device_id):
        return self._get(f"{self.base_url}/device/sensors/read/flatten", {"id": device_id}, app_id)

    def get_stock(self, app_id):
        return self._get(f"{self.base_url}/device/sensor/list/data/latest", {
            "configtype": "data",
            "param": "stock",
            "datatype": "number"
        }, app_id)

    def get_stock_latest(self, app_id):
        return self._get(f"{self.base_url}/device/sensor/list/data/latest", {}, app_id)

    def get_latest_rfid(self, app_id, device_id):
        return self._get(f"{self.base_url}/device/sensor/list/data/latest", {
            "device_id": device_id,
            "sensor": "user",
            "configtype": "config",
            "param": "rule"
        }, app_id)

    def get_state_rfid(self, app_id, device_id):
        return self._get(f"{self.base_url}/device/sensor/list/data/latest", {
            "device_id": device_id,
            "sensor": "user",
            "configtype": "data",
            "param": "state"
        }, app_id)
