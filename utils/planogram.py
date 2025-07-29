import json
import base64
from typing import Dict, List, Any


def decode_base64_payload(encoded_data: str) -> Dict[str, Any]:
    """Decode base64 payload and parse JSON"""
    try:
        decoded_bytes = base64.b64decode(encoded_data)
        decoded_str = decoded_bytes.decode('utf-8')
        return json.loads(decoded_str)
    except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:  # type: ignore
        raise ValueError(f"Invalid payload: {str(e)}")


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
