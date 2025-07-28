from repository.planogram_repository import PlanogramRepository
import base64
import json

repository = PlanogramRepository()


class PlanogramService:
    def __init__(self):
        self.repo = PlanogramRepository()

    def batch_config(self, vending_application_id: str, payload: dict):
        encoded_data = payload.get("data")

        if not encoded_data:
            return {
                "status_code": 400,
                "body": {"message": "device_id atau config kosong"}
            }

        try:
            decode_bytes = base64.b64decode(encoded_data)
            decode_str = decode_bytes.decode('utf-8')
            decode_payload = json.loads(decode_str)
        except Exception as e:
            return {
                "status_code": 400,
                "body": {"message": f"Gagal decode Base64: {str(e)}"}
            }

        device_id = decode_payload.get("device_id")
        if not device_id:
            return {
                "status_code": 400,
                "body": {"message": "device_id tidak ditemukan di payload"}
            }

        # lanjut repository
        result = repository.batch_config(
            vending_application_id, decode_payload)
        return {
            "status_code": 200,
            "body": result
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
