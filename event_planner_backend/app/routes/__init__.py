"""Routes package initializer to expose blueprints for the application.

This allows imports like:
    from .routes.health import blp as health_blp
    from .routes.events import blp as events_blp
    from .routes.weather import blp as weather_blp
"""
# No runtime logic required here; files in this package define and register blueprints.
