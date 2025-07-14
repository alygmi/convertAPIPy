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
    def _merge_query_params(self, url: str, extra_params: Dict[str, Any]) -> str:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

        parsed_url = urlparse(url)
        original_params = dict(parse_qsl(parsed_url.query))
        original_params.update(extra_params or {})
        new_query = urlencode(original_params, doseq=True)
        return urlunparse(parsed_url._replace(query=new_query))

    async def JGET(self, params: Dict[str, Any]) -> WSResult:
        raw_url = params.get("Url") or ""
        query_params = params.get("QueryParams") or {}
        headers = params.get("Headers", {})
        timeout = params.get("Timeout", 30)

        try:
            url = self._merge_query_params(raw_url, query_params)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
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

    async def JPOST(self, params: Dict[str, Any]) -> WSResult:
        url = params.get("Url") or ""
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
