from __future__ import annotations
import requests
from flask import request
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from ..config import Config

blp = Blueprint(
    "Weather",
    "weather",
    url_prefix="/api/weather",
    description="Secure proxy endpoints to fetch weather data from OpenWeather",
)


def _require_api_key(cfg: Config):
    if not cfg.OPENWEATHER_API_KEY:
        abort(500, message="OpenWeather API key is not configured.")


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

        params = {}
        if "q" in request.args:
            params["q"] = request.args.get("q")
        if "lat" in request.args and "lon" in request.args:
            params["lat"] = request.args.get("lat")
            params["lon"] = request.args.get("lon")
        params["units"] = request.args.get("units", "metric")
        if "lang" in request.args:
            params["lang"] = request.args.get("lang")

        if not params.get("q") and not (params.get("lat") and params.get("lon")):
            abort(400, message="Provide either ?q=city or ?lat=&lon= for weather lookup.")

        url = f"{cfg.OPENWEATHER_BASE_URL}/weather"
        try:
            resp = requests.get(url, params={**params, "appid": cfg.OPENWEATHER_API_KEY}, timeout=10)
            return resp.json(), resp.status_code
        except requests.RequestException as exc:
            abort(502, message=f"Failed to contact weather service: {exc}")


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

        params = {}
        if "q" in request.args:
            params["q"] = request.args.get("q")
        if "lat" in request.args and "lon" in request.args:
            params["lat"] = request.args.get("lat")
            params["lon"] = request.args.get("lon")
        params["units"] = request.args.get("units", "metric")
        if "lang" in request.args:
            params["lang"] = request.args.get("lang")

        if not params.get("q") and not (params.get("lat") and params.get("lon")):
            abort(400, message="Provide either ?q=city or ?lat=&lon= for forecast lookup.")

        url = f"{cfg.OPENWEATHER_BASE_URL}/forecast"
        try:
            resp = requests.get(url, params={**params, "appid": cfg.OPENWEATHER_API_KEY}, timeout=10)
            return resp.json(), resp.status_code
        except requests.RequestException as exc:
            abort(502, message=f"Failed to contact weather service: {exc}")
