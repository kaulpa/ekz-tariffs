from __future__ import annotations

import datetime as dt
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change

from custom_components.ekz_tariffs.storage import make_store, slots_from_json

from .api import EkzTariffsApi
from .const import (CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME, DOMAIN, FETCH_HOUR,
                    FETCH_MINUTE, PLATFORMS, SERVICE_REFRESH)
from .coordinator import EkzTariffsCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    tariff_name = entry.data.get(CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME)
    
    session = async_get_clientsession(hass)
    api = EkzTariffsApi(session)

    store = make_store(hass, entry.entry_id)
    coordinator = EkzTariffsCoordinator(hass, api, tariff_name, store)

    saved = await store.async_load()
    if saved and "slots" in saved:
        coordinator.async_set_updated_data(slots_from_json(saved["slots"]))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "tariff_name": tariff_name,
    }

    await coordinator.async_config_entry_first_refresh()

    async def _scheduled_refresh(_now: dt.datetime) -> None:
        _LOGGER.debug("Scheduled refresh triggered")
        await coordinator.async_request_refresh()

    unsub = async_track_time_change(
        hass,
        _scheduled_refresh,
        hour=FETCH_HOUR,
        minute=FETCH_MINUTE,
        second=0,
    )
    entry.async_on_unload(unsub)

    async def _handle_refresh(call: ServiceCall) -> None:
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        _handle_refresh,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok