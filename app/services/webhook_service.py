"""Twilio reminder-response webhook orchestration.

Re-targets the original Azure-backed flow: on a "no" reply, cancel the
appointment via ``AppointmentService``. There is no durable session store, so
the reminder response is only logged, not persisted.
"""

from typing import Any

from app.core.logging import get_logger
from app.schemas.webhook import TwilioReminderResponse
from app.services.appointment_service import AppointmentService
from app.services.base import BaseService

logger = get_logger(__name__)


class WebhookService(BaseService):
    async def handle_reminder_response(self, req: TwilioReminderResponse) -> dict[str, Any]:
        logger.info(
            "Reminder response appointment=%s type=%s response=%s cancel_request=%s",
            req.appointment_id,
            req.reminder_type,
            req.user_response,
            req.request_for_cancellation,
        )

        action = "acknowledged"
        if req.user_response == "no" and not req.request_for_cancellation:
            await AppointmentService().cancel(req.appointment_id)
            action = "cancelled"

        return {
            "appointmentId": req.appointment_id,
            "reminderType": req.reminder_type,
            "userResponse": req.user_response,
            "action": action,
        }
