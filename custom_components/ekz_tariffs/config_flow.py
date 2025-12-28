from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME, DOMAIN

TARIFF_CHOICES = ["400D", "400F", "400ST", "400WP", "400L", "400LS", "16L", "16LS"]


class EkzTariffsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            schema = vol.Schema(
                {
                    vol.Required(CONF_TARIFF_NAME, default=DEFAULT_TARIFF_NAME): vol.In(
                        TARIFF_CHOICES
                    ),
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_TARIFF_NAME]}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"EKZ {user_input[CONF_TARIFF_NAME]}",
            data=user_input,
        )
