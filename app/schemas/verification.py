"""Phone-verification (OTP) request schemas.

Field names match the legacy chatbot UI payloads (snake_case); the shared
``Model`` also accepts camelCase via its alias generator.
"""

from app.schemas.base import Model


class PhoneVerificationStart(Model):
    session_id: str
    channel: str = "sms"
    force_resend: bool = False


class PhoneVerificationConfirm(Model):
    session_id: str
    code: str


class PhoneUpdate(Model):
    session_id: str
    new_phone_number: str
