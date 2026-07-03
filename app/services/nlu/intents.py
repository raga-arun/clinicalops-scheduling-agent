"""Supported scheduling intents."""

from enum import Enum


class Intent(str, Enum):
    FIND_SLOTS = "find_slots"
    BOOK_APPOINTMENT = "book_appointment"
    CANCEL_APPOINTMENT = "cancel_appointment"
    RESCHEDULE_APPOINTMENT = "reschedule_appointment"
    UNKNOWN = "unknown"
