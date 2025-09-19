"""Utility helpers for responses and error handling."""
from __future__ import annotations
from typing import Any, Dict, Optional


def success_response(data: Any, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a standardized success response."""
    resp = {"success": True, "data": data}
    if meta:
        resp["meta"] = meta
    return resp


def error_response(message: str, code: str = "error", details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build a standardized error response."""
    resp = {"success": False, "error": {"code": code, "message": message}}
    if details:
        resp["error"]["details"] = details
    return resp
