from fastapi import Request
import json
from starlette.middleware.base import BaseHTTPMiddleware


class PrintBodyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        try:
            body_str = body.decode("utf-8")
            try:
                json_body = json.loads(body_str)
                print(
                    "Request Body:", json.dumps(json_body, indent=2, ensure_ascii=False)
                )
            except json.JSONDecodeError:
                print("Request Body is not valid JSON:", body_str)
        finally:
            response = await call_next(request)
            return response
