"""Aggregate v1 router."""

from fastapi import APIRouter

from app.api.v1.routes import (
    address,
    appointment,
    chat,
    doctor_clinic,
    health,
    insurance,
    patient,
    slots,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctor_clinic.router, tags=["doctor-clinic"])
api_router.include_router(address.router, tags=["address"])
api_router.include_router(slots.router, tags=["slots"])
api_router.include_router(patient.router, tags=["patient"])
api_router.include_router(appointment.router, tags=["appointment"])
api_router.include_router(insurance.router, tags=["insurance"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
