"""Slot availability orchestration over the internal Common slots API."""

import calendar
from datetime import date as date_cls
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger
from app.services.base import BaseService

logger = get_logger(__name__)

LOOKAHEAD_DAYS = 60


def _weekday(day: str) -> str | None:
    try:
        return datetime.strptime(day, "%Y-%m-%d").strftime("%A")
    except ValueError:
        return None


def _month_bounds(start_date: str) -> tuple[str, str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    last_day = calendar.monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day)
    return start.isoformat(), end.isoformat()


class SlotsService(BaseService):
    async def live_slots(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        date: str,
        slot_type: str = "NP",
        slots_count: int = 20,
    ) -> list[dict[str, Any]]:
        logger.info(
            "Live slots for doctor=%s clinic=%s date=%s type=%s",
            doctor_id,
            clinic_id,
            date,
            slot_type,
        )
        slots = await self._clients.internal.scheduling.live_slots(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            date=date,
            slot_type=slot_type,
            slots_count=slots_count,
        )
        return [s for s in slots if str(s.get("status", "")).lower() == "free"]

    async def month_slots(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        start_date: str,
        slot_type: str = "NP",
    ) -> dict[str, Any]:
        start, end = _month_bounds(start_date)
        logger.info(
            "Month slots for doctor=%s clinic=%s %s..%s type=%s",
            doctor_id,
            clinic_id,
            start,
            end,
            slot_type,
        )
        counts = await self._clients.internal.scheduling.slot_counts(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            start_date=start,
            end_date=end,
            slot_type=slot_type,
        )
        data: list[dict[str, Any]] = []
        total = 0
        for item in counts:
            day = item.get("date")
            count = item.get("count", 0) or 0
            total += count
            data.append({"date": day, "slot_count": count, "weekday": _weekday(day) if day else None})
        return {"month": start[:7], "data": data, "total_slots": total}

    async def nearest_dates_slots(
        self,
        *,
        doctor_id: str,
        clinic_id: str,
        slot_type: str = "NP",
        count: int = 3,
    ) -> list[dict[str, Any]]:
        today = date_cls.today()
        end = today + timedelta(days=LOOKAHEAD_DAYS)
        logger.info(
            "Nearest %s dates for doctor=%s clinic=%s type=%s",
            count,
            doctor_id,
            clinic_id,
            slot_type,
        )
        counts = await self._clients.internal.scheduling.slot_counts(
            doctor_id=doctor_id,
            clinic_id=clinic_id,
            start_date=today.isoformat(),
            end_date=end.isoformat(),
            slot_type=slot_type,
        )
        available = sorted(
            (c for c in counts if (c.get("count", 0) or 0) > 0),
            key=lambda c: c.get("date", ""),
        )[:count]

        results: list[dict[str, Any]] = []
        for item in available:
            day = item.get("date")
            slots = await self._clients.internal.scheduling.live_slots(
                doctor_id=doctor_id,
                clinic_id=clinic_id,
                date=day,
                slot_type=slot_type,
            )
            results.append(
                {
                    "date": day,
                    "weekday": _weekday(day) if day else None,
                    "slot_count": item.get("count", 0) or 0,
                    "slots": [s for s in slots if str(s.get("status", "")).lower() == "free"],
                }
            )
        return results
