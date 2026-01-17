
from __future__ import annotations

import contextlib
import datetime as dt
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .api import TariffSlot
from .const import DOMAIN
from .sensor_daily_average import EkzAverageTodaySensor, EkzAverageTomorrowSensor
from .sensor_window_extreme import EkzWindowExtremeSensor
from .utils import FusedEvent, fuse_slots


def _find_current_slot(slots: list[FusedEvent], now: dt.datetime) -> FusedEvent | None:
    for s in slots:
        if s.start <= now < s.end:
            return s
    return None


def _find_next_boundary(
    slots: list[FusedEvent], now: dt.datetime
) -> dt.datetime | None:
    """
    Next moment when the price can change:
    - if currently in a slot: its end
    - else: the next slot start after now
    """
    cur = _find_current_slot(slots, now)
    if cur:
        return cur.end
    for s in slots:
        if s.start > now:
            return s.start
    return None


def santize_tariff_name(tariff_name: str) -> str:
    return tariff_name.replace(" ", "_").lower()


class EkzCurrentPriceSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "CHF/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:cash-100"

    def __init__(
        self, hass: HomeAssistant, entry_id: str, tariff_name: str, coordinator
    ) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._tariff_name = tariff_name
        self._coordinator = coordinator

        self._attr_unique_id = f"{entry_id}_current_price"
        self._attr_name = f"Current price: {tariff_name}"

        self._unsub_boundary: Any | None = None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self._coordinator.async_add_listener(self._handle_coordinator_update)
        )
        self._handle_coordinator_update()

    def _clear_boundary_timer(self) -> None:
        if self._unsub_boundary:
            with contextlib.suppress(Exception):
                self._unsub_boundary()
            self._unsub_boundary = None

    def _schedule_next_boundary_update(self) -> None:
        self._clear_boundary_timer()
        slots: list[TariffSlot] = self._coordinator.data or []
        now = dt_util.now()
        fused_slots = fuse_slots(slots)
        next_boundary = _find_next_boundary(fused_slots, now)
        if not next_boundary or next_boundary <= now:
            return

        async def _on_boundary(_now: dt.datetime) -> None:
            # Recompute native_value/attributes and then schedule the *next* boundary.
            self.async_write_ha_state()
            self._schedule_next_boundary_update()

        self._unsub_boundary = async_track_point_in_time(
            self.hass, _on_boundary, next_boundary
        )

    def _handle_coordinator_update(self) -> None:
        # Tariff schedule changed (daily refresh) -> reschedule boundary updates
        self._schedule_next_boundary_update()
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        slots: list[TariffSlot] = self._coordinator.data or []
        now = dt_util.now()
        fused_slots = fuse_slots(slots)
        cur = _find_current_slot(fused_slots, now)
        if not cur:
            return None
        # avoid float noise; keep sensor stable
        return round(cur.price, 6)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slots: list[TariffSlot] = self._coordinator.data or []
        now = dt_util.now()
        fused_slots = fuse_slots(slots)
        cur = _find_current_slot(fused_slots, now)
        next_boundary = _find_next_boundary(fused_slots, now)

        attrs: dict[str, Any] = {
            "tariff_name": self._tariff_name,
            "schedule_date": dt_util.as_local(now).date().isoformat(),
            "next_change": next_boundary.isoformat() if next_boundary else None,
        }
        if cur:
            attrs.update(
                {
                    "slot_start": cur.start.isoformat(),
                    "slot_end": cur.end.isoformat(),
                }
            )
        return attrs


class EkzNextChangeSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self, hass: HomeAssistant, entry_id: str, tariff_name: str, coordinator
    ) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._tariff_name = tariff_name
        self._coordinator = coordinator
        self._attr_name = f"Next change: {tariff_name}"
        self._attr_unique_id = f"{entry_id}_next_change"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))
        self._handle_update()

    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> dt.datetime | None:
        slots: list[TariffSlot] = self._coordinator.data or []
        fused_slots = fuse_slots(slots)
        return _find_next_boundary(fused_slots, dt_util.now())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slots: list[TariffSlot] = self._coordinator.data or []
        now = dt_util.now()
        fused_slots = fuse_slots(slots)
        cur = _find_current_slot(fused_slots, now)
        return {
            "tariff_name": self._tariff_name,
            "slot_start": cur.start.isoformat() if cur else None,
            "slot_end": cur.end.isoformat() if cur else None,
        }



def _slot_to_dict(slot: TariffSlot) -> dict[str, Any]:
    return {
        "start": slot.start.isoformat(),
        "end": slot.end.isoformat(),
        "value": round(slot.price, 6),
    }


def _filter_by_local_date(slots: list[TariffSlot], day: dt.date) -> list[TariffSlot]:
    """Filter 15-min slots by local calendar day."""
    out: list[TariffSlot] = []
    for s in slots or []:
        s_local_start = dt_util.as_local(s.start)
        if s_local_start.date() == day:
            out.append(s)
    out.sort(key=lambda x: x.start)
    return out


class EkzForecastSensor(SensorEntity):
    """Exposes today's and tomorrow's 15-min tariff slots as attributes for plotting."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:timeline-clock"

    def __init__(self, hass: HomeAssistant, entry_id: str, tariff_name: str, coordinator) -> None:
        self.hass = hass
        self._entry_id = entry_id
        self._tariff_name = tariff_name
        self._coordinator = coordinator
        self._attr_name = f"Tariff schedule: {tariff_name}"
        self._attr_unique_id = f"{entry_id}_schedule"

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.async_add_listener(self._handle_update))
        self._handle_update()

    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        # As state we expose the local date of the schedule (today)
        return dt_util.as_local(dt_util.now()).date().isoformat()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        slots: list[TariffSlot] = self._coordinator.data or []
        today = dt_util.as_local(dt_util.now()).date()
        tomorrow = today + dt.timedelta(days=1)
        today_slots = _filter_by_local_date(slots, today)
        tomorrow_slots = _filter_by_local_date(slots, tomorrow)
        return {
            "tariff_name": self._tariff_name,
            "price_unit": "CHF/kWh",
            "today": [_slot_to_dict(s) for s in today_slots],
            "tomorrow": [_slot_to_dict(s) for s in tomorrow_slots],  # may be empty until ~18:00
        }


def _mk_windows(hass, entry_id, tariff_name, coordinator, day_offset: int, suffix: str):
    label = "today" if day_offset == 0 else "tomorrow"
    return [
        EkzWindowExtremeSensor(
            hass,
            entry_id,
            tariff_name,
            coordinator,
            day_offset,
            window_minutes=240,
            mode="min",
            name=f"Lowest 4h window {label}: {tariff_name}",
            unique_suffix=f"lowest_4h_{suffix}",
        ),
        EkzWindowExtremeSensor(
            hass,
            entry_id,
            tariff_name,
            coordinator,
            day_offset,
            window_minutes=120,
            mode="min",
            name=f"Lowest 2h window {label}: {tariff_name}",
            unique_suffix=f"lowest_2h_{suffix}",
        ),
        EkzWindowExtremeSensor(
            hass,
            entry_id,
            tariff_name,
            coordinator,
            day_offset,
            window_minutes=240,
            mode="max",
            name=f"Highest 4h window {label}: {tariff_name}",
            unique_suffix=f"highest_4h_{suffix}",
        ),
        EkzWindowExtremeSensor(
            hass,
            entry_id,
            tariff_name,
            coordinator,
            day_offset,
            window_minutes=120,
            mode="max",
            name=f"Highest 2h window {label}: {tariff_name}",
            unique_suffix=f"highest_2h_{suffix}",
        ),
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    entities = [
        EkzCurrentPriceSensor(
            hass, entry.entry_id, data["tariff_name"], data["coordinator"]
        ),
        EkzNextChangeSensor(
            hass, entry.entry_id, data["tariff_name"], data["coordinator"]
        ),
        # New: forecast/schedule entity with today/tomorrow slot arrays
        EkzForecastSensor(
            hass, entry.entry_id, data["tariff_name"], data["coordinator"]
        ),
        EkzAverageTodaySensor(
            hass, entry.entry_id, data["tariff_name"], data["coordinator"]
        ),
        EkzAverageTomorrowSensor(
            hass, entry.entry_id, data["tariff_name"], data["coordinator"]
        ),
    ]
    entities += _mk_windows(
        hass,
        entry.entry_id,
        data["tariff_name"],
        data["coordinator"],
        day_offset=0,
        suffix="today",
    )
    entities += _mk_windows(
        hass,
        entry.entry_id,
        data["tariff_name"],
        data["coordinator"],
        day_offset=1,
        suffix="tomorrow",
    )
    async_add_entities(entities, update_before_add=False)
