import requests
import os
from utils.headers import get_application_id


class DeviceService:
    def __init__(self):
        self.base_url = os.getenv(
            "INTERNAL_PLATFORM_API_BASE_URL", "https://iotera.internal")
        self.superadmin_url = os.getenv(
            "SUPER_ADMIN_PLATFORM_API_URL", "https://superadmin.iotera")

    def _build_headers(self):
        return {
            "vending-application-id": get_application_id(),
            "Content-Type": "application/json"
        }

    def list(self):
        url = f"{self.base_url}/device/list"
        params = {
            "tags": "active:true",
            "with_online": True,
            "as_object": True
        }
        return self._get(url, params)

    def list_payment(self):
        url = f"{self.base_url}/device/list"
        params = {
            "tags": "payment_link:true",
            "with_online": True,
            "as_object": True
        }
        return self._get(url, params)

    def get_master(self):
        url = f"{self.base_url}/masterdata/list/group?group=rfid"
        return self._get(url, {})

    def update(self, body: dict):
        url = f"{self.base_url}/device/update"
        return self._post(url, body)

    def add_master(self, body: dict):
        url = f"{self.base_url}/masterdata/insert"
        return self._post(url, body)

    def update_master(self, body: dict):
        url = f"{self.base_url}/masterdata/update"
        return self._post(url, body)

    def delete_master(self, body: dict):
        url = f"{self.base_url}/masterdata/delete"
        return self._post(url, body)

    def device_latest_data(self, body: dict):
        url = f"{self.superadmin_url}/device/sensor/list/data/latest"
        return self._post(url, body, use_superadmin=True)

    def push_payment_data(self, body: dict):
        url = "https://asia-southeast2-iotera-vending.cloudfunctions.net/pushFrPaymentServerNew2nd"
        headers = {
            "Authorization": "apikey ajkhjkhqkjhwjkehkqwe:khkkjqhjkwhjkq",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                url, json=body, headers=headers, timeout=90)
            return {"status_code": response.status_code, "body": response.json()}
        except requests.exceptions.RequestException as e:
            return {"status_code": 500, "result": -1, "message": str(e)}

    def _get(self, url, params):
        headers = self._build_headers()
        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=90)
            return {"status_code": response.status_code, "body": response.json()}
        except requests.exceptions.RequestException as e:
            return {"status_code": 500, "body": {"result": -1, "message": str(e)}}

    def _post(self, url, body, use_superadmin=False):
        headers = self._build_headers()
        try:
            response = requests.post(
                url, json=body, headers=headers, timeout=90)
            return {"status_code": response.status_code, "body": response.json()}
        except requests.exceptions.RequestException as e:
            return {"status_code": 500, "body": {"result": -1, "message": str(e)}}
