import requests

class PayoutRepository:
    def list_payout(self, app_id: str, url: str, body: dict):
        headers = {
            "X-API-Key": "mocked-api-key",  # ganti sesuai kebutuhan
            "Content-Type": "application/json",
            "Vending-Application-Id": app_id
        }
        try:
            response = requests.post(url, json=body, headers=headers, timeout=90)
            return {
                "body": response.json(),
                "status_code": response.status_code
            }
        except requests.exceptions.RequestException as e:
            return {
                "body": {"result": -1, "message": str(e)},
                "status_code": 500
            }