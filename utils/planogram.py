import json
import base64
from typing import Dict, List, Any, Tuple

from fastapi import Request


def decode_base64_payload(encoded_data: str) -> Dict[str, Any]:
    """Decode base64 payload and parse JSON"""
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:  # type: ignore
        raise ValueError(f"Invalid payload: {str(e)}")


async def get_payload_encrypted_map(request: Request):
    try:
        body = await request.body()
        payload = json.loads(body.decode())
        return payload, None
    except Exception:
        return None, "invalid"


def build_config_list(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build configList from payload in the required format"""
    config_list = []

    field_mappings = {
        "ids": "id",
        "names": "name",
        "values": "value",
        "types": "type",
        "prices": "price",
        "stocks": "stock",
        "selections": "selection",
        "actives": "active"
    }

    for field, param in field_mappings.items():
        if field in payload:
            for sensor, val in payload[field].items():
                config_list.append({
                    "sensor": sensor,
                    "param": param,
                    "value": val
                })

    return config_list


def build_config_list_playstation(decoded_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build config list khusus PlayStation Set sesuai dengan implementasi Go
    """
    config_list = []

    # Field mappings sesuai dengan handler Go
    field_validations = {
        "ids": ("id", lambda x: isinstance(x, str)),
        "names": ("name", lambda x: isinstance(x, str)),
        "remoteBrands": ("remote_brand", lambda x: isinstance(x, str)),
        "remoteIds": ("remote_id", lambda x: isinstance(x, str)),
        "prices": ("price", lambda x: isinstance(x, dict)),
        "remoteCommands": ("remote_command", lambda x: isinstance(x, dict))
    }

    for field, (param, validator) in field_validations.items():
        if field in decoded_payload:
            field_data = decoded_payload[field]
            if not isinstance(field_data, dict):
                continue

            for sensor, value in field_data.items():
                if not validator(value):
                    raise ValueError(
                        f"Invalid type for {field}[{sensor}]. Expected {validator.__name__}")

                config_list.append({
                    "sensor": str(sensor),
                    "param": param,
                    "value": value
                })

    return config_list
