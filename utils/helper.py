# app/utils/helper.py
import time
import json
from typing import Dict, Any, List, Optional, TypeVar, Tuple
from base64 import b64decode
from urllib.parse import urlencode

from utils.web_services import WSResult
from config.settings import settings  # Import settings

T = TypeVar('T')

# Dummy data for Telegram tokens/channel IDs/message IDs
# In a real app, these would likely come from a database or a more robust config system
_telegram_config = {
    "app_id_123": {  # Contoh applicationId
        "token": "5486013761:AAHSt1OlBGnRHydwFlvewyfOGoYZyw0gBR4",  # Contoh token
        "channel_id": "1664430239",  # Contoh channel ID
        "message_id": "123456789"  # Contoh message ID
    },
    # Tambahkan config untuk applicationId lain di sini
}


def GetChannelId(application_id: str) -> str:
    # Anda bisa memuat ini dari database atau konfigurasi yang lebih kompleks
    # Untuk contoh ini, kita pakai dummy dictionary
    return _telegram_config.get(application_id, {}).get("channel_id", "")


def GetTelegramToken(application_id: str) -> str:
    # Anda bisa memuat ini dari database atau konfigurasi yang lebih kompleks
    # Untuk contoh ini, kita pakai dummy dictionary
    return _telegram_config.get(application_id, {}).get("token", "")


def GetMessageID(application_id: str) -> str:
    # Anda bisa memuat ini dari database atau konfigurasi yang lebih kompleks
    # Untuk contoh ini, kita pakai dummy dictionary
    return _telegram_config.get(application_id, {}).get("message_id", "")


def WSResultToMap(ws_result: WSResult) -> Dict[str, Any]:
    # Mengonversi WSResult ke format map yang diharapkan di controller
    # Dalam Go, wsresult.Body bisa langsung digunakan sebagai map.
    # Di Python, kita sudah mengembalikan dict dari JSON.
    return {
        "code": ws_result.code,
        "body": ws_result.body,
        "error": str(ws_result.error) if ws_result.error else None
    }


async def PayloadEncryptedMap(ctx: Any) -> Tuple[Dict[str, Any], Optional[Exception]]:
    # Payload terenkripsi tidak diimplementasikan secara penuh di sini
    # Anggap saja ini mengembalikan JSON biasa untuk demo
    try:
        # FastAPI handles JSON parsing automatically with request.json()
        payload = await ctx.json()
        return payload, None
    except Exception as e:
        return {}, e


async def PayloadMap(ctx: Any) -> Tuple[Dict[str, Any], Optional[Exception]]:
    try:
        payload = await ctx.json()
        return payload, None
    except Exception as e:
        return {}, e


# type: ignore
def RGet(data: Any, key: str, errors: List[Exception]) -> Tuple[T, List[Exception], bool]:
    # Implementasi sederhana RGet untuk Python.
    # Tidak sekompleks Go, karena Python tidak memiliki pengecekan tipe statis seperti Go.
    # Asumsi data adalah dictionary.
    if not isinstance(data, dict):
        errors.append(ValueError(f"Expected dict for RGet, got {type(data)}"))
        return None, errors, False  # type: ignore

    value = data.get(key)
    if value is None:
        errors.append(KeyError(f"Key '{key}' not found or has None value"))
        return None, errors, False  # type: ignore

    # Optional: type checking, but Python is dynamic
    # try:
    #     if type(value) != T: # Ini hanya bekerja untuk tipe konkret, bukan Union/Any
    #         errors.append(TypeError(f"Value for key '{key}' has unexpected type: {type(value)}"))
    #         return None, errors, False
    # except TypeError:
    #     pass # T can be Any

    return value, errors, True


def AddSuccessResponse(response: Dict[str, Any], server_ts: int, message: str) -> Dict[str, Any]:
    response["server_ts"] = server_ts
    response["message"] = message
    response["result"] = 0  # Asumsi result 0 adalah SUCCESS
    return response

# Dummy result codes


class Result:
    SUCCESS = 0
    HTTP_OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500

# Untuk controller.BrFailed dan controller.IseFailed
# Ini akan diintegrasikan langsung ke dalam controller, bukan helper.
# Di Python, kita akan menggunakan HTTPException dari FastAPI
