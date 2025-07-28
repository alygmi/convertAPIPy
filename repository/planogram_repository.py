import requests
import os
import httpx


class PlanogramRepository:
    def __init__(self):
        self.base_url = os.getenv(
            "INTERNAL_PLATFORM_API_BASE_URL", "https://iotera.internal")

    def _headers(self, app_id):
        return {
            "Vending-Application-Id": app_id,
            "Content-Type": "application/json"
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

    def batch_config(self, app_id, body):
        url = f"{self.base_url}/send/config/batch"
        headers = {"vending-application-id": app_id}
        print(f"[DEBUG] Sending to: {url}")
        print(f"[DEBUG] Headers: {headers}")
        print(f"[DEBUG] Body: {body}")

        try:
            response = httpx.post(url, json=body, headers=headers, timeout=30)
            response.raise_for_status()
            return {"status_code": response.status_code, "body": response.json()}
        except httpx.HTTPStatusError as exc:
            print(
                f"[ERROR] HTTP Error: {exc.response.status_code} - {exc.response.text}")
            return {"status_code": exc.response.status_code, "body": {"error": exc.response.text}}
        except Exception as exc:
            print(f"[ERROR] Unexpected error: {str(exc)}")
            return {"status_code": 500, "body": {"error": "Unexpected error"}}

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
