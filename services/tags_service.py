from repository.tags_repository import TagsRepository


class TagsService:
    def __init__(self):
        self.repo = TagsRepository()

    def list(self, app_id: str):
        return self.repo.list(app_id)

    def create(self, app_id: str, body: dict):
        return self.repo.create(app_id, body)

    def apply(self, app_id: str, body: dict):
        return self.repo.apply(app_id, body)

    def remove(self, app_id: str, body: dict):
        return self.repo.remove(app_id, body)

    def delete(self, app_id: str, body: dict):
        return self.repo.delete(app_id, body)
