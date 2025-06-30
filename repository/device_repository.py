class DeviceRepository:
    def list_device(self, app_id:str):
        return {
            "code": 200,
            "body": {
                "devices": [
                    {"id": "device1", "name": "Mesin A"},
                    {"id": "device2", "name": "Mesin B"}
                ]
            }
        }