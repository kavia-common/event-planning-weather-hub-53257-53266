"""Marshmallow schemas for validating and serializing Event Planner resources."""
from __future__ import annotations
from datetime import datetime
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class PaginationQuery(Schema):
    page = fields.Int(missing=1, description="Current page (1-based).")
    page_size = fields.Int(missing=20, validate=validate.Range(min=1, max=100), description="Items per page.")


class EventCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255), description="Event title.")
    description = fields.Str(allow_none=True, metadata={"description": "Event description."})
    location = fields.Str(allow_none=True, metadata={"description": "Event location."})
    date = fields.DateTime(required=True, format="iso", description="Event date-time in ISO8601 (UTC).")
    weather_preference = fields.Str(
        allow_none=True,
        validate=validate.Length(max=64),
        metadata={"description": "Optional weather preference (e.g., sunny, no_rain)."},
    )

    @validates_schema
    def validate_date(self, data, **kwargs):
        # Ensure date is in the future (or now)
        if "date" in data:
            if data["date"] < datetime.utcnow():
                # soft validation: allow past for demo? We'll enforce >= now
                raise ValidationError("Event date must be in the future or now.", field_name="date")


class EventUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    date = fields.DateTime(format="iso")
    weather_preference = fields.Str(validate=validate.Length(max=64))


class EventSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    date = fields.DateTime(required=True)
    weather_preference = fields.Str(allow_none=True)
    created_at = fields.DateTime(required=True)
    updated_at = fields.DateTime(required=True)
