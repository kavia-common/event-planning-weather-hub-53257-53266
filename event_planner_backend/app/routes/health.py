from flask_smorest import Blueprint
from flask.views import MethodView

# Correct tag naming and description for OpenAPI
blp = Blueprint("Health", "health", url_prefix="/", description="Health check route for uptime monitoring")


@blp.route("/")
class HealthCheck(MethodView):
    """Health check endpoint that returns basic service status."""
    def get(self):
        return {"message": "Healthy"}
