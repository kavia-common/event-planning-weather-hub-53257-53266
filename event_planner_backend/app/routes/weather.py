from __future__ import annotations
import json
import logging
import requests
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
    if not cfg.OPENWEATHER_API_KEY:
        # Log clearly for backend debugging while keeping message generic to clients
        logger.error("OPENWEATHER_API_KEY is not set. Configure environment variable.")
        abort(500, message="OpenWeather API key is not configured.")


def _collect_params():
    """Collect and validate incoming query parameters for weather endpoints."""
    params = {}
    if "q" in request.args:
        params["q"] = request.args.get("q")
    if "lat" in request.args and "lon" in request.args:
        params["lat"] = request.args.get("lat")
        params["lon"] = request.args.get("lon")
    params["units"] = request.args.get("units", "metric")
    if "lang" in request.args:
        params["lang"] = request.args.get("lang")
    return params


def _validate_location_params(params: dict, context: str):
    if not params.get("q") and not (params.get("lat") and params.get("lon")):
        abort(400, message=f"Provide either ?q=city or ?lat=&lon= for {context} lookup.")


def _proxy_openweather(url: str, params: dict, cfg: Config, context: str):
    """Proxy helper that calls OpenWeather and handles error mapping."""
    # Add API key
    upstream_params = {**params, "appid": cfg.OPENWEATHER_API_KEY}

    logger.info(
        "Proxying to OpenWeather | context=%s | url=%s | params=%s",
        context, url, json.dumps({k: v for k, v in upstream_params.items() if k != "appid"})
    )

    try:
        resp = requests.get(url, params=upstream_params, timeout=10)
        content_type = resp.headers.get("Content-Type", "")
        body = resp.json() if "application/json" in content_type else {"raw": resp.text}

        # Log upstream status for diagnostics
        logger.info(
            "OpenWeather response | context=%s | status=%s | keys=%s",
            context, resp.status_code, list(body.keys()) if isinstance(body, dict) else type(body).__name__
        )

        if 200 <= resp.status_code < 300:
            # Return standardized success wrapper to help frontend logic
            return success_response(body), 200

        # For known OpenWeather error format, forward meaningful message
        message = body.get("message") if isinstance(body, dict) else "Upstream error"
        details = {"upstream_status": resp.status_code, "upstream_body": body}
        return error_response(
            message=message or f"Failed to fetch {context} from weather service.",
            code="upstream_error",
            details=details
        ), 502

    except requests.Timeout:
        logger.exception("Timeout contacting OpenWeather for %s", context)
        abort(504, message=f"Timeout contacting weather service for {context}.")
    except requests.RequestException as exc:
        logger.exception("Network error contacting OpenWeather for %s", context)
        abort(502, message=f"Failed to contact weather service: {exc}")


@blp.route("/current")
class CurrentWeather(MethodView):
    """Proxy for current weather by city name or coordinates."""
    def get(self):
        """
        Fetch current weather data.

        Query params:
            - q: City name (e.g., London)
            - lat, lon: Coordinates
            - units: metric/imperial (default metric)
            - lang: language code
        """
        cfg = Config()
        _require_api_key(cfg)

        params = _collect_params()
        _validate_location_params(params, "weather")

        url = f"{cfg.OPENWEATHER_BASE_URL}/weather"
        return _proxy_openweather(url, params, cfg, context="current")


@blp.route("/forecast")
class ForecastWeather(MethodView):
    """Proxy for 5 day / 3 hour forecast."""
    def get(self):
        """
        Fetch forecast weather data.

        Query params:
            - q: City name (e.g., London)
            - lat, lon: Coordinates
            - units: metric/imperial (default metric)
            - lang: language code
        """
        cfg = Config()
        _require_api_key(cfg)

        params = _collect_params()
        _validate_location_params(params, "forecast")

        url = f"{cfg.OPENWEATHER_BASE_URL}/forecast"
        return _proxy_openweather(url, params, cfg, context="forecast")
