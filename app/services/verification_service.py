"""Phone-verification (OTP) orchestration over the external verification service.

Thin pass-through: the external provider owns Twilio Verify, OTP state, and any
issued token. Responses are returned verbatim (raw ``status``/``message``/
``verification`` shape) so the legacy chatbot UI is unchanged.
"""

from typing import Any

from app.core.logging import get_logger
from app.schemas.verification import PhoneUpdate, PhoneVerificationConfirm, PhoneVerificationStart
from app.services.base import BaseService

logger = get_logger(__name__)


class VerificationService(BaseService):
    async def start(self, req: PhoneVerificationStart) -> dict[str, Any]:
        logger.info("Phone verification start session=%s channel=%s", req.session_id, req.channel)
        return await self._clients.external.verification.start(
            session_id=req.session_id,
            channel=req.channel,
            force_resend=req.force_resend,
        )

    async def confirm(self, req: PhoneVerificationConfirm) -> dict[str, Any]:
        logger.info("Phone verification confirm session=%s", req.session_id)
        return await self._clients.external.verification.confirm(
            session_id=req.session_id, code=req.code
        )

    async def update(self, req: PhoneUpdate) -> dict[str, Any]:
        logger.info("Phone number update session=%s", req.session_id)
        return await self._clients.external.verification.update(
            session_id=req.session_id, new_phone_number=req.new_phone_number
        )
