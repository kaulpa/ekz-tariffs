from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from aiohttp import ClientSession
from homeassistant.util import dt as dt_util

from .const import API_BASE, API_TARIFFS_PATH, INTEGRATED_PREFIX


@dataclass(frozen=True)
class TariffSlot:
    start: datetime
    end: datetime
    price_chf_per_kwh: float


class EkzTariffsApi:
    def __init__(self, session: ClientSession):
        self._session = session

    async def fetch_tariffs(
        self,
        tariff_name: str,
        start: datetime,
        end: datetime,
    ) -> list[TariffSlot]:
        """Fetch tariff slots from EKZ API for time range"""
        start = dt_util.as_local(start)
        end = dt_util.as_local(end)

        params = {
            "tariff_name": f"{INTEGRATED_PREFIX}{tariff_name}",
            "start_timestamp": start.isoformat(timespec="seconds"),
            "end_timestamp": end.isoformat(timespec="seconds"),
        }

        url = f"{API_BASE}{API_TARIFFS_PATH}"

        async with self._session.get(url, params=params, timeout=30) as resp:
            resp.raise_for_status()
            data: dict[str, Any] = await resp.json()

        slots: list[TariffSlot] = []
        for item in data.get("prices", []):
            start_ts = dt_util.parse_datetime(item["start_timestamp"])
            end_ts = dt_util.parse_datetime(item["end_timestamp"])
            if start_ts is None or end_ts is None:
                continue
            price_val = None
            for comp in item.get("integrated", []):
                if comp.get("unit") == "CHF_kWh":
                    price_val = comp.get("value")
                    break

            if price_val is None:
                continue

            slots.append(TariffSlot(
                start=dt_util.as_local(start_ts),
                end=dt_util.as_local(end_ts),
                price_chf_per_kwh=float(price_val),
            ))

        slots.sort(key=lambda s: s.start)
        return slots