import os
import requests
from utils.headers import build_payment_api_headers
from config.settings import settings


class TagsRepository:
    def list(self, application_id):
        url = settings.INTERNAL_PLATFORM_API_BASE_URL + \
            "/tag/selection/list?group=location"
        headers = build_payment_api_headers(application_id)
        response = requests.get(url, headers=headers)
        return response.json()

    def create(self, application_id, body):
        url = settings.INTERNAL_PLATFORM_API_BASE_URL + \
            "/tag/selection/create"
        headers = build_payment_api_headers(application_id)
        response = requests.post(url, json=body, headers=headers)
        return response.json()

    def apply(self, application_id, body):
        url = settings.INTERNAL_PLATFORM_API_BASE_URL + \
            "/device/tags/merge"
        headers = build_payment_api_headers(application_id)
        response = requests.post(url, json=body, headers=headers)
        return response.json()

    def remove(self, application_id, body):
        url = settings.INTERNAL_PLATFORM_API_BASE_URL + \
            "/device/tags/delete"
        headers = build_payment_api_headers(application_id)
        response = requests.post(url, json=body, headers=headers)
        return response.json()

    def delete(self, application_id, body):
        url = settings.INTERNAL_PLATFORM_API_BASE_URL + \
            "/tag/selection/delete"
        headers = build_payment_api_headers(application_id)
        response = requests.post(url, json=body, headers=headers)
        return response.json()
