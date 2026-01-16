from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME, DOMAIN

TARIFF_CHOICES = ["400D", "400F", "400ST", "400WP", "400L", "400LS", "16L", "16LS"]

TARIFF_DESCRIPTIONS = {
    "400D": "EKZ Energie Dynamisch + EKZ Netz 400D + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "400F": "EKZ Energie Erneuerbar + EKZ Netz 400F + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "400ST": "EKZ Energie Erneuerbar + EKZ Netz 400ST + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "400WP": "EKZ Energie Erneuerbar + EKZ Netz 400WP + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "400L": "EKZ Energie Business Erneuerbar + EKZ Netz 400L + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "400LS": "EKZ Energie Business Erneuerbar + EKZ Netz 400LS + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "16L": "EKZ Energie Business Erneuerbar + EKZ Netz 16L + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
    "16LS": "EKZ Energie Business Erneuerbar + EKZ Netz 16LS + SDL, Stromreserve, Solidarisierte Kosten, Bundesabgaben",
}


class EkzTariffsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # If submitted, go to confirmation step to show full description
        if user_input is not None:
            self.context[CONF_TARIFF_NAME] = user_input[CONF_TARIFF_NAME]
            return await self.async_step_confirm()

        # Initial display
        selected_tariff = self.context.get(CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME)
        description = TARIFF_DESCRIPTIONS.get(selected_tariff, "")

        schema = vol.Schema(
            {
                vol.Required(CONF_TARIFF_NAME, default=selected_tariff): vol.In(
                    TARIFF_CHOICES
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={
                "tariff_description": description,
            },
        )

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Confirmation step showing full tariff details."""
        tariff_name = self.context.get(CONF_TARIFF_NAME, DEFAULT_TARIFF_NAME)
        description = TARIFF_DESCRIPTIONS.get(tariff_name, "")

        if user_input is not None:
            # User confirmed, create the entry
            await self.async_set_unique_id(f"{DOMAIN}_{tariff_name}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"EKZ {tariff_name}",
                data={CONF_TARIFF_NAME: tariff_name},
            )

        # Show confirmation with full description
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),  # No input needed, just confirmation
            description_placeholders={
                "tariff_name": tariff_name,
                "tariff_description": description,
            },
        )
