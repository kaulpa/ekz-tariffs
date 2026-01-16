from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

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

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            # Create selector options with descriptions
            options = [
                {"value": tariff, "label": tariff}
                for tariff in TARIFF_CHOICES
            ]
            
            schema = vol.Schema(
                {
                    vol.Required(CONF_TARIFF_NAME, default=DEFAULT_TARIFF_NAME): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                        )
                    ),
                }
            )
            
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
                description_placeholders={
                    "tariff_description": TARIFF_DESCRIPTIONS.get(
                        DEFAULT_TARIFF_NAME, ""
                    )
                },
            )

        await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_TARIFF_NAME]}")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"EKZ {user_input[CONF_TARIFF_NAME]}",
            data=user_input,
        )
