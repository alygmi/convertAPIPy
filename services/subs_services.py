import os
import requests

class SubsService:
    def __init__(self):
        self.base_url = os.getenv("INTERNAL_PLATFORM_API_BASE_URL", "https://iotera.internal")
        self.payment_base_url = os.getenv("PAYMENT_API_BASE_URL", "https://pay.iotera.io")

    def _headers(self, app_id, use_payment=False):
        return {
            "Vending-Application-Id": app_id,
            "Content-Type": "application/json",
            "X-API-Key": "mocked-key" if use_payment else None
        }

    def _get(self, url, app_id, params=None, use_payment=False):
        headers = self._headers(app_id, use_payment)
        headers = {k: v for k, v in headers.items() if v is not None}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=90)
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "body": {"message": str(e)}}

    def _post(self, url, app_id, body, use_payment=False):
        headers = self._headers(app_id, use_payment)
        headers = {k: v for k, v in headers.items() if v is not None}
        try:
            r = requests.post(url, json=body, headers=headers, timeout=90)
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "body": {"message": str(e)}}

    def list_device_non_sub(self, app_id):
        url = f"{self.base_url}/subscription/details/device/list/nonsubs"
        return self._get(url, app_id)

    def get_device_per_tags(self, app_id, key):
        url = f"{self.base_url}/subscription/details/device/list/subs"
        return self._get(url, app_id, {"key": key})

    def get_subs(self, app_id):
        url = f"{self.base_url}/subscription/details/list"
        return self._get(url, app_id)

    def cancel_subs(self, app_id, body):
        url = f"{self.payment_base_url}/application/transaction/cancel"
        return self._post(url, app_id, body, use_payment=True)

    def create_subs(self, app_id, body):
        url = f"{self.payment_base_url}/application/transaction/subscription"
        return self._post(url, app_id, body, use_payment=True)

    def extend_subs(self, app_id, body):
        url = f"{self.base_url}/subscription/details/extend"
        return self._post(url, app_id, body)

    def active_subs(self, app_id, body):
        url = f"{self.payment_base_url}/subscription/details/extend"
        return self._post(url, app_id, body, use_payment=True)

    def register_subs(self, app_id, body):
        url = f"{self.base_url}/subscription/details/register"
        return self._post(url, app_id, body)

    def untag_subs(self, app_id, body):
        url = f"{self.base_url}/subscription/details/untag"
        return self._post(url, app_id, body)

    def update_subs(self, app_id, body):
        url = f"{self.base_url}/updateSubs"
        return self._post(url, app_id, body)

    def push_firebase(self, url, body):
        try:
            r = requests.post(url, json=body, timeout=90)
            return {"status_code": r.status_code, "body": r.json()}
        except Exception as e:
            return {"status_code": 500, "body": {"message": str(e)}}
