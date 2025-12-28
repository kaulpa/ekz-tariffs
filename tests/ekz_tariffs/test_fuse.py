from __future__ import annotations

import datetime as dt

from homeassistant.util import dt as dt_util

from custom_components.ekz_tariffs.api import TariffSlot
from custom_components.ekz_tariffs.calendar import fuse_slots


def test_fuse_adjacent_equal_prices():
    tz = dt_util.DEFAULT_TIME_ZONE
    t0 = dt.datetime(2025, 12, 28, 0, 0, tzinfo=tz)

    slots = [
        TariffSlot(t0, t0 + dt.timedelta(minutes=15), 0.10),
        TariffSlot(t0 + dt.timedelta(minutes=15), t0 + dt.timedelta(minutes=30), 0.10),
        TariffSlot(t0 + dt.timedelta(minutes=30), t0 + dt.timedelta(minutes=45), 0.12),
        TariffSlot(t0 + dt.timedelta(minutes=45), t0 + dt.timedelta(minutes=60), 0.12),
        TariffSlot(t0 + dt.timedelta(minutes=60), t0 + dt.timedelta(minutes=75), 0.10),
    ]

    fused = fuse_slots(slots)
    assert len(fused) == 3
    assert fused[0].start == t0
    assert fused[0].end == t0 + dt.timedelta(minutes=30)
    assert fused[0].price == 0.10

    assert fused[1].start == t0 + dt.timedelta(minutes=30)
    assert fused[1].end == t0 + dt.timedelta(minutes=60)
    assert fused[1].price == 0.12
