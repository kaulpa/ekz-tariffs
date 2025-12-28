from homeassistant.const import Platform

DOMAIN = "ekz_tariffs"
PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR]

CONF_TARIFF_NAME = "tariff_name"
DEFAULT_TARIFF_NAME = "400D"

API_BASE = "https://api.tariffs.ekz.ch/v1"
API_TARIFFS_PATH = "/tariffs"

INTEGRATED_PREFIX = "integrated_"

FETCH_HOUR = 18
FETCH_MINUTE = 30

EVENT_TYPE = f"{DOMAIN}_event"
EVENT_TARIFF_START = "tariff_start"

SERVICE_REFRESH = "refresh"


