import os
  print('OPENWEATHER_API_KEY from env:', os.environ.get('OPENWEATHER_API_KEY'))

from __future__ import annotations
import json
import logging
import requests
from typing import Any, Dict, List, Tuple
from flask import request
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from ..config import Config
from ..utils import success_response, error_response

# Configure module-level logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

blp = Blueprint(
    "Weather",
    "weather",
    url_prefix="/api/weather",
    description="Secure proxy endpoints to fetch weather data from OpenWeather",
)


def _require_api_key(cfg: Config):
    """
    Ensure OPENWEATHER_API_KEY is set; otherwise respond with a clear error.

    PUBLIC_INTERFACE
    """
    if not cfg.OPENWEATHER_API_KEY:
        # Log the backend-side cause while keeping client message generic.
        logger.error("OPENWEATHER_API_KEY is not set. Configure environment variable.")
        abort(500, message="OpenWeather API key is not configured.")


def _collect_params() -> Dict[str, str]:
    """Collect and validate incoming query parameters for weather endpoints."""
    params: Dict[str, str] = {}
    if "q" in request.args:
        params["q"] = request.args.get("q") or ""
    if "lat" in request.args and "lon" in request.args:
        params["lat"] = request.args.get("lat") or ""
        params["lon"] = request.args.get("lon") or ""
    params["units"] = request.args.get("units", "metric")
    if "lang" in request.args:
        params["lang"] = request.args.get("lang") or ""
    return params


def _validate_location_params(params: dict, context: str):
    """Validate that either city name or coordinates were provided."""
    if not params.get("q") and not (params.get("lat") and params.get("lon")):
        abort(400, message=f"Provide either ?q=city or ?lat=&lon= for {context} lookup.")


def _map_upstream_status_to_http(resp_status: int, body: Dict[str, Any]) -> int:
    """
    Map OpenWeather upstream statuses to appropriate HTTP codes for clients.

    - 401 -> 401 Unauthorized
    - 403 -> 403 Forbidden
    - 429 or body.cod == "429" -> 429 Too Many Requests
    - else -> 502 Bad Gateway
    """
    cod = str(body.get("cod", "")).strip() if isinstance(body, dict) else ""
    if resp_status == 401:
        return 401
    if resp_status == 403:
        return 403
    if resp_status == 429 or cod == "429":
        return 429
    return 502


def _normalize_forecast(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize OpenWeather 5-day/3-hour forecast into a predictable structure.

    Returns:
    {
      "city": { name, country, coord },
      "forecast": [
         { "dt": 1737312000, "dt_txt": "...", "temp": 12.3, "feels_like": 11.0,
           "humidity": 70, "weather": { "id": 500, "main": "Rain", "description": "light rain", "icon": "10d" },
           "wind_speed": 3.5, "wind_deg": 220, "pop": 0.15 }
      ]
    }
    """
    city = (body or {}).get("city") or {}
    lst: List[Dict[str, Any]] = (body or {}).get("list") or []
    normalized: List[Dict[str, Any]] = []
    for item in lst:
        weather0 = (item.get("weather") or [{}])[0] if isinstance(item.get("weather"), list) else {}
        main = item.get("main") or {}
        wind = item.get("wind") or {}
        normalized.append(
            {
                "dt": item.get("dt"),
                "dt_txt": item.get("dt_txt"),
                "temp": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "temp_min": main.get("temp_min"),
                "temp_max": main.get("temp_max"),
                "pressure": main.get("pressure"),
                "humidity": main.get("humidity"),
                "weather": {
                    "id": weather0.get("id"),
                    "main": weather0.get("main"),
                    "description": weather0.get("description"),
                    "icon": weather0.get("icon"),
                },
                "wind_speed": wind.get("speed"),
                "wind_deg": wind.get("deg"),
                "clouds": (item.get("clouds") or {}).get("all"),
                "pop": item.get("pop"),  # probability of precipitation
                "rain_3h": (item.get("rain") or {}).get("3h"),
                "snow_3h": (item.get("snow") or {}).get("3h"),
            }
        )
    return {
        "city": {
            "name": city.get("name"),
            "country": city.get("country"),
            "coord": (city.get("coord") or {}),
            "timezone": city.get("timezone"),
            "sunrise": city.get("sunrise"),
            "sunset": city.get("sunset"),
        },
        "forecast": normalized,
    }


def _proxy_openweather(url: str, params: dict, cfg: Config, context: str) -> Tuple[Dict[str, Any], int]:
    """
    Proxy helper that calls OpenWeather and handles error mapping.

    Returns a tuple of (payload, http_status). On success, payload = success_response(data, meta).
    On error, payload = error_response(...).

    PUBLIC_INTERFACE
    """
    # Add API key
    upstream_params = {**params, "appid": cfg.OPENWEATHER_API_KEY}

    safe_params = {k: v for k, v in upstream_params.items() if k != "appid"}
    logger.info(
        "Proxying to OpenWeather | context=%s | url=%s | params=%s",
        context, url, json.dumps(safe_params)
    )

    try:
        resp = requests.get(url, params=upstream_params, timeout=10)
        content_type = resp.headers.get("Content-Type", "")
        is_json = "application/json" in content_type
        body = resp.json() if is_json else {"raw": resp.text}

        # Log upstream status and a small snippet for diagnostics
        preview = body if not isinstance(body, dict) else {k: body.get(k) for k in list(body.keys())[:5]}
        logger.info(
            "OpenWeather response | context=%s | status=%s | preview=%s",
            context, resp.status_code, json.dumps(preview) if isinstance(preview, dict) else str(preview)[:200]
        )

        if 200 <= resp.status_code < 300:
            # Normalize forecast response to ensure frontend gets predictable arrays
            data = body
            meta = {"source": "openweathermap", "upstream_status": resp.status_code}

            if context == "forecast" and isinstance(body, dict):
                data = _normalize_forecast(body)
                # Log size for debugging "no data" cases
                logger.info(
                    "Normalized forecast entries: %s", len(data.get("forecast", []) if isinstance(data, dict) else [])
                )

            payload = success_response(data, meta=meta)
            # Also log final backend payload size/info
            logger.info(
                "Backend success | context=%s | keys=%s",
                context, list(payload.keys())
            )
            return payload, 200

        # Map and forward meaningful errors
        message = (body.get("message") if isinstance(body, dict) else "Upstream error") or \
                  f"Failed to fetch {context} from weather service."
        http_status = _map_upstream_status_to_http(resp.status_code, body if isinstance(body, dict) else {})
        details = {"upstream_status": resp.status_code, "upstream_body": body, "context": context}
        payload = error_response(
            message=message,
            code="upstream_error",
            details=details
        )
        logger.warning(
            "Backend error | context=%s | http_status=%s | message=%s",
            context, http_status, message
        )
        return payload, http_status

    except requests.Timeout:
        logger.exception("Timeout contacting OpenWeather for %s", context)
        abort(504, message=f"Timeout contacting weather service for {context}.")
    except requests.RequestException as exc:
        logger.exception("Network error contacting OpenWeather for %s", context)
        abort(502, message=f"Failed to contact weather service: {exc}")


@blp.route("/current")
class CurrentWeather(MethodView):
    """
    Proxy for current weather by city name or coordinates.

    PUBLIC_INTERFACE
    """
    def get(self):
        """
        Fetch current weather data.

        Query params:
            - q: City name (e.g., London)
            - lat, lon: Coordinates
            - units: metric/imperial (default metric)
            - lang: language code

        Returns:
            JSON envelope:
              { "success": true, "data": <openweather current>, "meta": { "source": "openweathermap", "upstream_status": 200 } }
        """
        cfg = Config()
        _require_api_key(cfg)

        params = _collect_params()
        _validate_location_params(params, "weather")

        url = f"{cfg.OPENWEATHER_BASE_URL}/weather"
        return _proxy_openweather(url, params, cfg, context="current")


@blp.route("/forecast")
class ForecastWeather(MethodView):
    """
    Proxy for 5 day / 3 hour forecast.

    PUBLIC_INTERFACE
    """
    def get(self):
        """
        Fetch forecast weather data.

        Query params:
            - q: City name (e.g., London)
            - lat, lon: Coordinates
            - units: metric/imperial (default metric)
            - lang: language code

        Returns:
            JSON envelope:
              { "success": true,
                "data": { "city": {...}, "forecast": [ <normalized entries> ] },
                "meta": { "source": "openweathermap", "upstream_status": 200 } }
        """
        cfg = Config()
        _require_api_key(cfg)

        params = _collect_params()
        _validate_location_params(params, "forecast")

        url = f"{cfg.OPENWEATHER_BASE_URL}/forecast"
        return _proxy_openweather(url, params, cfg, context="forecast")
