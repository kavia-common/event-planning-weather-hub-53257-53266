from __future__ import annotations
from datetime import datetime
from flask_smorest import Blueprint, abort
from flask.views import MethodView
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from ..db import SessionLocal
from ..models import Event
from ..schemas import EventCreateSchema, EventSchema, PaginationQuery, EventUpdateSchema

blp = Blueprint(
    "Events",
    "events",
    url_prefix="/api/events",
    description="CRUD operations for event resources",
)


@blp.route("/")
class EventsList(MethodView):
    """List or create events."""
    @blp.arguments(PaginationQuery, location="query")
    @blp.response(200, EventSchema(many=True))
    def get(self, args):
        """List events with pagination.

        Returns a paginated list of events ordered by date ascending.
        """
        page = int(args.get("page", 1))
        page_size = int(args.get("page_size", 20))
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        offset = (page - 1) * page_size
        session = SessionLocal()

        try:
            total = session.query(Event).count()
            events = session.execute(
                select(Event).order_by(Event.date.asc()).offset(offset).limit(page_size)
            ).scalars().all()
            blp.record_response_metadata({"X-Total-Count": total})  # for awareness; not auto-added
            return events
        finally:
            session.close()

    @blp.arguments(EventCreateSchema)
    @blp.response(201, EventSchema)
    def post(self, payload):
        """Create a new event.

        Validates the payload and stores the event record.
        """
        session = SessionLocal()
        try:
            event = Event(
                title=payload["title"],
                description=payload.get("description"),
                location=payload.get("location"),
                date=payload["date"],
                weather_preference=payload.get("weather_preference"),
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        except SQLAlchemyError as exc:
            session.rollback()
            abort(400, message=f"Failed to create event: {str(exc)}")
        finally:
            session.close()


@blp.route("/<int:event_id>")
class EventDetail(MethodView):
    """Retrieve, update, or delete a single event by ID."""
    @blp.response(200, EventSchema)
    def get(self, event_id: int):
        """Retrieve an event by ID."""
        session = SessionLocal()
        try:
            event = session.get(Event, event_id)
            if not event:
                abort(404, message="Event not found")
            return event
        finally:
            session.close()

    @blp.arguments(EventUpdateSchema)
    @blp.response(200, EventSchema)
    def patch(self, payload, event_id: int):
        """Update fields on an existing event."""
        session = SessionLocal()
        try:
            event = session.get(Event, event_id)
            if not event:
                abort(404, message="Event not found")

            for key, value in payload.items():
                if key == "date" and isinstance(value, datetime):
                    setattr(event, key, value)
                elif key in ("title", "description", "location", "weather_preference"):
                    setattr(event, key, value)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
        except SQLAlchemyError as exc:
            session.rollback()
            abort(400, message=f"Failed to update event: {str(exc)}")
        finally:
            session.close()

    @blp.response(204)
    def delete(self, event_id: int):
        """Delete an event by ID."""
        session = SessionLocal()
        try:
            event = session.get(Event, event_id)
            if not event:
                abort(404, message="Event not found")
            session.delete(event)
            session.commit()
            return ""
        except SQLAlchemyError as exc:
            session.rollback()
            abort(400, message=f"Failed to delete event: {str(exc)}")
        finally:
            session.close()
