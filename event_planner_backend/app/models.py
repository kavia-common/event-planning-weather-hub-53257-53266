"""Database models for the Event Planner backend."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from .db import Base


class Event(Base):
    """Represents an event planned by the user."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    date = Column(DateTime, nullable=False)  # Event start date and time (UTC)
    weather_preference = Column(String(64), nullable=True)  # e.g., "sunny", "no_rain"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title!r} date={self.date.isoformat()}>"
