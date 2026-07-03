"""Shared response envelopes."""

from app.schemas.base import Model


class ErrorDetail(Model):
    code: str
    message: str


class ErrorResponse(Model):
    error: ErrorDetail


class HealthResponse(Model):
    status: str = "ok"
    service: str
    version: str
