"""Webhook endpoints: Twilio appointment-reminder replies."""

from typing import Any

from app.api.route import create_router
from app.schemas.webhook import TwilioReminderResponse
from app.services.webhook_service import WebhookService

router = create_router()


@router.post("/webhooks/twilio-reminder-response", response_model=dict[str, Any])
async def twilio_reminder_response(payload: TwilioReminderResponse) -> dict[str, Any]:
    return await WebhookService().handle_reminder_response(payload)
