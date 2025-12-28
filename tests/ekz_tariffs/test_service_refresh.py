from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from custom_components.ekz_tariffs.const import DOMAIN


@pytest.mark.asyncio
async def test_refresh_service_calls_coordinator(
    hass,
    mock_config_entry,
):
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.ekz_tariffs.api.EkzTariffsApi.fetch_tariffs",
        return_value=[],
    ):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]["coordinator"]

    # Spy on async_request_refresh
    with patch.object(coordinator, "async_request_refresh", new=AsyncMock()) as spy:
        await hass.services.async_call(DOMAIN, "refresh", {}, blocking=True)
        assert spy.await_count == 1
