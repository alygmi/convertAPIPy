from typing import Any, Dict
from config.settings import settings
from utils.planogram import build_config_list

import requests
import os
import httpx


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
