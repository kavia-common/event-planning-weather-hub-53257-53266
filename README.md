# event-planning-weather-hub-53257-53266

Backend (Flask) for Event Planning with Weather Proxy

- Features:
  - CRUD API for events persisted to a database (SQLite by default; Postgres/MySQL supported via env).
  - Secure proxy endpoints to fetch current weather and 5-day forecast from OpenWeather without exposing API key to clients.
  - OpenAPI docs available at /docs on the backend service.

Quick Start:
1) Create .env from example and set values:
   cp event_planner_backend/.env.example event_planner_backend/.env
   # edit OPENWEATHER_API_KEY and DATABASE_URL as needed

2) Install dependencies (handled by CI using requirements.txt).

3) Run backend:
   cd event_planner_backend
   python run.py

Endpoints:
- Health: GET /
- Events:
  - GET /api/events?page=1&page_size=20
  - POST /api/events
  - GET /api/events/<id>
  - PATCH /api/events/<id>
  - DELETE /api/events/<id>
- Weather Proxy:
  - GET /api/weather/current?q=London&units=metric
  - GET /api/weather/current?lat=51.5072&lon=-0.1276&units=metric
  - GET /api/weather/forecast?q=London&units=metric