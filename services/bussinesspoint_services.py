from repository.device_repository import DeviceRepository
from services.device_services import DeviceService

class BusinessPointService:
    def __init__(self):
        self.device_service = DeviceService()

    def list_devices(self, application_id):
        return self.device_service.list(application_id)

    def list_device_payment(self, application_id):
        return self.device_service.list_payment(application_id)

    def update_device(self, application_id, body: dict):
        return self.device_service.update(application_id, body)

    def get_master_data(self, application_id):
        return self.device_service.get_master(application_id)

    def get_latest_sensor(self, application_id, payload: dict):
        return self.device_service.device_latest_data(application_id, payload)

    def push_payment_data(self, payload: dict):
        return self.device_service.push_payment_data(payload)
    
    def add_master(self, application_id, payload: dict):
        return self.device_service.add_master(application_id, payload)
