import datetime as dt
from dataclasses import dataclass

from .api import TariffSlot


@dataclass
class FusedEvent:
    start: dt.datetime
    end: dt.datetime
    price: float


def fuse_slots(slots: list[TariffSlot]) -> list[FusedEvent]:
    fused: list[FusedEvent] = []
    if not slots:
        return fused

    def norm(x: float) -> float:
        return round(x, 6)

    cur = FusedEvent(
        start=slots[0].start, end=slots[0].end, price=norm(slots[0].price_chf_per_kwh)
    )
    for s in slots[1:]:
        p = norm(s.price_chf_per_kwh)
        if p == cur.price and s.start == cur.end:
            cur.end = s.end
        else:
            fused.append(cur)
            cur = FusedEvent(start=s.start, end=s.end, price=p)
    fused.append(cur)
    return fused
