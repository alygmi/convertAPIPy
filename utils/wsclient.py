from typing import Any, Dict


class WebSocketResult:
    def __init__(self, result: int, body: dict = None, error: str = None, message: str = None):
        self.result = result
        self.body = body or {}
        self.error = error
        self.message = message

    def to_dict(self):
        return {
            "result": self.result,
            "body": self.body,
            "error": self.error,
            "message": self.message,
        }


class WebSocketClient:
    async def send(self, action: str, application_id: str, data: dict):
        # Dummy websocket call
        print(
            f"[WS SEND] action={action}, app_id={application_id}, data={data}"
        )

        # Contoh response dummy
        return WebSocketResult(
            result=0,
            body={"echo": data},
            error=None,
            message="OK"
        )
