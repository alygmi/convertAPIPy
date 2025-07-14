# app/services/task_service.py
from typing import Any, Dict, List
from urllib.parse import urlencode

from config.settings import settings
from utils.web_services import WebService, WSResult  # Pastikan import yang benar
from utils.helper import WSResultToMap  # Jika masih diperlukan


class TaskService:
    async def call_telegram(self, token_telegram: str, body: str) -> WSResult:
        url = f"https://api.telegram.org/bot{token_telegram}/sendMessage?{body}"
        return await WebService.JGET({
            "Url": url,
            "Headers": {}
        })

    async def create_task(self, application_id: str, body: Dict[str, Any]) -> WSResult:
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/task/create"
        headers = self._build_internal_api_headers(application_id)
        return await WebService.JPOST({
            "Url": url,
            "Body": body,
            "Timeout": 90,
            "Headers": headers
        })  # type: ignore

    async def close_task(self, application_id: str, body: Dict[str, Any]) -> WSResult:
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/task/close"
        headers = self._build_internal_api_headers(application_id)
        return await WebService.JPOST({
            "Url": url,
            "Body": body,
            "Timeout": 90,
            "Headers": headers
        })  # type: ignore

    async def get_task(self, application_id: str) -> WSResult:
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/task/list"
        headers = self._build_internal_api_headers(application_id)
        return await WebService.JGET({
            "Url": url,
            "Headers": headers
        })

    async def get_bp(self, url: str) -> WSResult:
        return await WebService.JGET({
            "Url": url,
        })

    async def get_pinned_message(self, token: str, channel: str) -> WSResult:
        url = f"https://api.telegram.org/bot{token}/getChat?chat_id=-100{channel}"
        return await WebService.JGET({
            "Url": url
        })

    async def get_sensors(self, application_id: str) -> WSResult:
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/device/sensor/list/data/latest"
        headers = self._build_internal_platform_api_headers(application_id)
        return await WebService.JGET({
            "Url": url,
            "Headers": headers
        })

    async def list_device(self, application_id: str) -> WSResult:
        url = f"{settings.INTERNAL_PLATFORM_API_BASE_URL}/device/list"
        query_params = {
            "tags": "stock:true",
            "with_online": True
        }
        headers = self._build_internal_platform_api_headers(application_id)
        return await WebService.JGET({
            "Url": url,
            "QueryParams": query_params,
            "Headers": headers
        })

    async def create_pinned(self, message: str, channel_id_telegram: str, token_telegram: str, message_id: int) -> WSResult:
        body = {
            "parse_mode": "html",
            "chat_id": f"-100{channel_id_telegram}",
            "text": message,
        }
        # url.Values di Go mirip urlencode di Python
        encoded_body = urlencode(body)
        url = f"https://api.telegram.org/bot{token_telegram}/sendMessage?{encoded_body}"
        return await WebService.JGET({
            "Url": url
        })

    async def edit_pinned(self, message: str, channel_id_telegram: str, token_telegram: str, message_id: int) -> WSResult:
        body = {
            "parse_mode": "html",
            "chat_id": f"-100{channel_id_telegram}",
            "message_id": message_id,
            "text": message,
        }
        # Telegram API expects message_id as an integer directly, not a string in URL query params if using POST with JSON.
        # But since original Go code used JGET with query params, we follow that.
        encoded_body = urlencode(body)
        url = f"https://api.telegram.org/bot{token_telegram}/editMessageText?{encoded_body}"
        return await WebService.JGET({
            "Url": url
        })

    def _build_internal_api_headers(self, application_id: str) -> Dict[str, str]:
        # Ini adalah asumsi bagaimana header dibuat berdasarkan kode Go Anda.
        # Sesuaikan dengan implementasi service.BuildInternalApiHeaders dan service.BuildInternalPlatformApiHeaders Anda di Go.
        return {
            "Content-Type": "application/json",
            "Iotera-Internal-Token": settings.INTERNAL_PLATFORM_API_TOKEN,
            "Iotera-Application-Id": application_id,
        }

    def _build_internal_platform_api_headers(self, application_id: str) -> Dict[str, str]:
        # Jika ada perbedaan headers antara InternalApi dan InternalPlatformApi, definisikan di sini.
        # Untuk saat ini, diasumsikan sama dengan _build_internal_api_headers
        return self._build_internal_api_headers(application_id)
