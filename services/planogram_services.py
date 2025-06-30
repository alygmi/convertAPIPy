from repository.planogram_repository import PlanogramRepository

class PlanogramService:
    def __init__(self):
        self.repo = PlanogramRepository()

    def batch_config(self, app_id: str, body: dict):
        return self.repo.batch_config(app_id, body)

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
