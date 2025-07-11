# app/utils/webservice.py
import httpx
import json
from typing import Dict, Any, Optional


class WSResult:
    def __init__(self, code: int, body: Any = None, error: Optional[Exception] = None):
        self.code = code
        self.body = body
        self.error = error


class WebService:
    @staticmethod
    async def JGET(params: Dict[str, Any]) -> WSResult:
        url = params.get("Url")
        query_params = params.get("QueryParams")
        headers = params.get("Headers", {})
        timeout = params.get("Timeout", 30)  # Default timeout 30 seconds

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=query_params, headers=headers)
                response.raise_for_status()  # Raises an exception for 4xx/5xx responses
                try:
                    return WSResult(code=response.status_code, body=response.json())
                except json.JSONDecodeError:
                    return WSResult(code=response.status_code, body=response.text)
        except httpx.HTTPStatusError as e:
            return WSResult(code=e.response.status_code, body=e.response.json() if e.response.text else {}, error=e)
        except httpx.RequestError as e:
            return WSResult(code=500, body={"message": f"Network or request error: {e}"}, error=e)
        except Exception as e:
            return WSResult(code=500, body={"message": f"An unexpected error occurred: {e}"}, error=e)

    @staticmethod
    async def JPOST(params: Dict[str, Any]) -> WSResult:
        url = params.get("Url")
        body = params.get("Body")
        headers = params.get("Headers", {})
        # Default timeout 90 seconds (sesuai Go)
        timeout = params.get("Timeout", 90)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=body, headers=headers)
                response.raise_for_status()
                try:
                    return WSResult(code=response.status_code, body=response.json())
                except json.JSONDecodeError:
                    return WSResult(code=response.status_code, body=response.text)
        except httpx.HTTPStatusError as e:
            return WSResult(code=e.response.status_code, body=e.response.json() if e.response.text else {}, error=e)
        except httpx.RequestError as e:
            return WSResult(code=500, body={"message": f"Network or request error: {e}"}, error=e)
        except Exception as e:
            return WSResult(code=500, body={"message": f"An unexpected error occurred: {e}"}, error=e)
