"""Phone-verification (OTP) endpoints for the legacy chatbot UI.

These use a plain ``APIRouter`` (not ``create_router``) so responses are NOT
wrapped in the ClinicalOps success envelope: the frontend reads the provider's
raw ``status``/``message``/``verification`` shape at the root. Do not switch
this to ``create_router`` without a matching frontend change.
"""

from typing import Any

from fastapi import APIRouter

from app.schemas.verification import PhoneUpdate, PhoneVerificationConfirm, PhoneVerificationStart
from app.services.verification_service import VerificationService

router = APIRouter()


@router.post("/verification/phone/start")
async def start_phone_verification(payload: PhoneVerificationStart) -> dict[str, Any]:
    return await VerificationService().start(payload)


@router.post("/verification/phone/confirm")
async def confirm_phone_verification(payload: PhoneVerificationConfirm) -> dict[str, Any]:
    return await VerificationService().confirm(payload)


@router.post("/verification/phone/update")
async def update_phone_number(payload: PhoneUpdate) -> dict[str, Any]:
    return await VerificationService().update(payload)
