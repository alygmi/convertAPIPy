import requests
import os

class AlertService:
    def __init__(self):
        self.base_url = os.getenv("INTERNAL_PLATFORM_API_BASE_URL", "https://iotera.internal")

    def _headers(self, app_id):
        return {
            "Vending-Application-Id": app_id,
            "Content-Type": "application/json"
        }
    
    def list_device(self, app_id):
        url = f"{self.base_url}/device/list"
        return self._get(url, {}, app_id)
    
    def alert_get(self, app_id, device_id):
        url = f"{self.base_url}/state/list/device"
        params = {"device_id": device_id}
        return self._get(url, params, app_id)

    def alert_get_by_device(self, app_id, device_id):
        url = f"{self.base_url}/state/read/device"
        params = {"device_id": device_id}
        return self._get(url, params, app_id)

    def alert_historical_by_device(self, app_id, device_id, key, start, end):
        url = f"{self.base_url}/state/list/data/period"
        params = {
            "device_id": device_id,
            "key": key,
            "start": start,
            "end": end
        }
        return self._get(url, params, app_id)

    def _get(self, url, params, app_id):
        try:
            resp = requests.get(url, params=params, headers=self._headers(app_id), timeout=90)
            return {"status_code": resp.status_code, "body": resp.json()}
        except requests.RequestException as e:
            return {"status_code": 500, "body": {"result": -1, "message": str(e)}}