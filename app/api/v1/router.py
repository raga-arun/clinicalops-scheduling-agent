"""Aggregate v1 router."""

from fastapi import APIRouter

from app.api.v1.routes import address, chat, doctor_clinic, health, scheduling

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(doctor_clinic.router, tags=["doctor-clinic"])
api_router.include_router(address.router, tags=["address"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(scheduling.router, prefix="/scheduling", tags=["scheduling"])
