# app/utils/helper.py
import time
import json
from typing import Dict, Any, List, Optional, TypeVar, Tuple, Union
from base64 import b64decode
from urllib.parse import urlencode

from utils.web_services import WSResult
from config.settings import settings
from utils.wsclient import WebSocketResult  # Import settings

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


def WSResultToMap(ws_result: Union["WebSocketResult", Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(ws_result, dict):
        return {
            "result": ws_result.get("result") or ws_result.get("code"),
            "body": ws_result.get("body") or ws_result.get("Body") or ws_result.get("data"),
            "error": ws_result.get("error") or ws_result.get("message"),
        }

    # kalau object WebSocketResult
    return {
        "result": getattr(ws_result, "result", None),
        "body": getattr(ws_result, "body", None),
        "error": str(getattr(ws_result, "error", None)) if getattr(ws_result, "error", None) else None,
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


def parse_coffee_sensors(configs: list):
    # convert configs -> sensors sesuai logic dari Go
    sensors = []
    for cfg in configs:
        sensors.append(cfg)  # placeholder, isi sesuai kebutuhan
    return sensors
# Dummy result codes


def parse_coffee_le_vending_configs(configs: List[Any]) -> Tuple[Dict[str, Any], Optional[Exception]]:
    if len(configs) < 2:
        return {}, ValueError("error -1: configs too short")

    header_array = configs[0]
    if not isinstance(header_array, list):
        return {}, ValueError("error -2: header is not a list")

    # Validasi header
    expected_headers = [
        "selection", "sku", "price", "order", "active",
        "hot", "ice", "ingredient", "name", "image"
    ]
    for idx, expected in enumerate(expected_headers):
        try:
            val = str(header_array[idx]).strip()
        except Exception:
            return {}, ValueError(f"error -3: header index {idx} missing")
        if val != expected:
            return {}, ValueError(f"error -3: header {expected} not found")

    result: Dict[str, Any] = {}

    # Loop isi configs
    for row in configs[1:]:  # skip header
        if not isinstance(row, list) or len(row) < 10:
            continue

        selection_data = str(row[0]).strip()
        if not selection_data or selection_data == "selection":
            continue

        sku_data = str(row[1]).strip()
        if not sku_data:
            continue

        name_data = str(row[8]).strip()
        if not name_data:
            continue

        # price
        price_data: Union[int, float]
        try:
            price_data = int(row[2]) if isinstance(row[2], str) else row[2]
            if not isinstance(price_data, (int, float)):
                continue
        except Exception:
            continue

        # order
        order_data: Union[int, float]
        try:
            order_data = int(row[3]) if isinstance(row[3], str) else row[3]
            if not isinstance(order_data, (int, float)):
                continue
        except Exception:
            continue

        # active & hot
        try:
            active_data = bool(row[4])
            hot_data = bool(row[5])
        except Exception:
            continue

        # ingredient
        ingredient_data = row[7] if isinstance(row[7], dict) else None
        if not ingredient_data:
            continue

        # ice (boleh kosong, fallback default)
        ice_data = row[6] if isinstance(row[6], dict) else {
            "no": 0, "less": 100, "medium": 140, "many": 170}

        # sugar → hardcoded default
        sugar_data = {"no": 0, "less": 10, "medium": 20, "many": 30}

        # image
        image_data = str(row[9]).strip()

        # Build data
        data_result = {
            "config": {
                "id": "text",
                "name": "text",
                "price": "number",
                "active": "bool",
                "image": "text",
                "ingredient": "uobject",
                "order": "number",
                "hot": "bool",
                "ice": "uobject",
                "sugar": "uobject",
            },
            "config_init": {
                "id": sku_data,
                "name": name_data,
                "price": price_data,
                "active": active_data,
                "image": image_data,
                "ingredient": ingredient_data,
                "order": order_data,
                "hot": hot_data,
                "ice": ice_data,
                "sugar": sugar_data,
            },
        }
        result[selection_data] = data_result

    return result, None


def maps_equal(map1: dict, map2: dict) -> bool:
    """Bandingkan dua dict secara key dan value persis seperti versi Go"""
    if len(map1) != len(map2):
        return False
    for key, val1 in map1.items():
        if key not in map2:
            return False
        val2 = map2[key]
        if val1 != val2:
            return False
    return True


def contains_map(slice_: list[dict], value: dict) -> bool:
    for item in slice_:
        if maps_equal(item, value):
            return True
    return False


class Result:
    SUCCESS = 0
    HTTP_OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500

# Untuk controller.BrFailed dan controller.IseFailed
# Ini akan diintegrasikan langsung ke dalam controller, bukan helper.
# Di Python, kita akan menggunakan HTTPException dari FastAPI
