from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from .config import Config
from .db import init_db
from .routes.health import blp as health_blp
from .routes.events import blp as events_blp
from .routes.weather import blp as weather_blp


app = Flask(__name__)
app.url_map.strict_slashes = False

# Load config
cfg = Config()
app.config["API_TITLE"] = cfg.API_TITLE
app.config["API_VERSION"] = cfg.API_VERSION
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/docs"
app.config["OPENAPI_SWAGGER_UI_PATH"] = ""
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
app.config["SECRET_KEY"] = cfg.SECRET_KEY

# CORS
CORS(app, resources={r"/*": {"origins": cfg.CORS_ALLOW_ORIGINS}})

# Initialize DB (create tables if not exist)
init_db(cfg)

# Initialize API and register blueprints
api = Api(app)
api.register_blueprint(health_blp)
api.register_blueprint(events_blp)
api.register_blueprint(weather_blp)
