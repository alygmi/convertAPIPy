import requests
from config import INTERNAL_API_BASE_URL, build_headers


class TagsRepository:
    def list(self, app_id):
        url = f"{INTERNAL_API_BASE_URL}/tag/selection/list?group=location"
        return requests.get(url, headers=build_headers(app_id)).json()

    def create(self, app_id, body):
        url = f"{INTERNAL_API_BASE_URL}/tag/selection/create"
        return requests.post(url, json=body, headers=build_headers(app_id)).json()

    def apply(self, app_id, body):
        url = f"{INTERNAL_API_BASE_URL}/device/tags/merge"
        return requests.post(url, json=body, headers=build_headers(app_id)).json()

    def remove(self, app_id, body):
        url = f"{INTERNAL_API_BASE_URL}/device/tags/delete"
        return requests.post(url, json=body, headers=build_headers(app_id)).json()

    def delete(self, app_id, body):
        url = f"{INTERNAL_API_BASE_URL}/tag/selection/delete"
        return requests.post(url, json=body, headers=build_headers(app_id)).json()
