"""Small signed demo-token authentication helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from typing import Literal

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


_bearer = HTTPBearer(auto_error=False)
_secret = os.getenv("AUTH_SECRET", "career-quest-demo-secret").encode()


@dataclass(frozen=True)
class Principal:
    role: Literal["employee", "hr"]
    employee_id: str | None


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_token(role: Literal["employee", "hr"], employee_id: str | None = None) -> str:
    payload = _encode(json.dumps({"role": role, "employee_id": employee_id}, separators=(",", ":")).encode())
    signature = _encode(hmac.new(_secret, payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def _invalid_token() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing bearer token")


def decode_token(token: str) -> Principal:
    try:
        payload, supplied_signature = token.split(".", 1)
        expected_signature = _encode(hmac.new(_secret, payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise ValueError("signature mismatch")
        data = json.loads(_decode(payload))
        if data.get("role") not in {"employee", "hr"}:
            raise ValueError("unknown role")
        employee_id = data.get("employee_id")
        if employee_id is not None and not isinstance(employee_id, str):
            raise ValueError("invalid employee id")
        return Principal(role=data["role"], employee_id=employee_id)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        raise _invalid_token() from None


def current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _invalid_token()
    return decode_token(credentials.credentials)


def require_self_or_hr(
    employee_id: str = Path(...), principal: Principal = Depends(current_principal)
) -> Principal:
    if principal.role == "hr" or principal.employee_id == employee_id:
        return principal
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You may only access your own profile")


def require_hr(principal: Principal = Depends(current_principal)) -> Principal:
    if principal.role == "hr":
        return principal
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="HR access required")
