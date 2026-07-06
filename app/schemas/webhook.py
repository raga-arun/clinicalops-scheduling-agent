"""Webhook request schemas."""

from typing import Literal

from app.schemas.base import Model


class TwilioReminderResponse(Model):
    appointment_id: str
    reminder_type: str
    user_response: Literal["yes", "no"]
    request_for_cancellation: bool = False
    patient_id: str | None = None
    session_id: str | None = None
