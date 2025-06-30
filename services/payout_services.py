from repository.payout_repository import PayoutRepository

class PayoutService:
    def __init__(self):
        self.repo = PayoutRepository()

    def list(self, app_id:str, url:str, body:dict):
        return self.repo.list_payout(app_id, url, body)