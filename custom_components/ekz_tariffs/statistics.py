from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import TypedDict

from homeassistant.util import dt as dt_util

from .api import TariffSlot

BUCKET_MINUTES = 15


class DailyStats(TypedDict):
    avg: float | None
    min: float | None
    max: float | None
    median: float | None
    q25: float | None
    q75: float | None
    slots_count: int
    covered_minutes: int


def _day_range_local(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    start = dt_util.start_of_local_day(
        dt_util.as_local(dt.datetime.combine(day, dt.time.min))
    )
    end = start + dt.timedelta(days=1)
    return start, end


def daily_stats(slots: list[TariffSlot], day: dt.date) -> DailyStats:
    """Time-weighted average + min/max for a local day, based on overlap with that day."""
    start, end = _day_range_local(day)

    total_weighted = 0.0
    total_seconds = 0.0

    min_p: float | None = None
    max_p: float | None = None
    slots_count = 0

    for s in slots:
        a = max(s.start, start)
        b = min(s.end, end)

        if b <= a:
            continue

        seconds = (b - a).total_seconds()
        total_seconds += seconds
        total_weighted += s.price_chf_per_kwh * seconds

        p = float(s.price_chf_per_kwh)
        min_p = p if min_p is None else min(min_p, p)
        max_p = p if max_p is None else max(max_p, p)

        slots_count += 1

    avg = (total_weighted / total_seconds) if total_seconds > 0 else None
    covered_minutes = round(total_seconds / 60.0)

    vals = [s.price_chf_per_kwh for s in slots if s.price_chf_per_kwh is not None]
    vals.sort()

    return {
        "avg": avg,
        "min": min_p,
        "max": max_p,
        "median": _median(vals),
        "q25": _quantile(vals, q=0.25),
        "q75": _quantile(vals, q=0.75),
        "slots_count": slots_count,
        "covered_minutes": covered_minutes,
    }


@dataclass
class WindowResult:
    start: dt.datetime
    end: dt.datetime
    avg: float


def bucket_prices(
    slots: list[TariffSlot], day: dt.date
) -> tuple[list[float | None], dt.datetime]:
    day_start, day_end = _day_range_local(day)
    slots_sorted = sorted(slots, key=lambda s: s.start)

    prices: list[float | None] = []
    t = day_start

    i = 0
    n = len(slots_sorted)

    step = dt.timedelta(minutes=BUCKET_MINUTES)
    while t < day_end:
        while i < n and slots_sorted[i].end <= t:
            i += 1

        price: float | None = None
        if i < n:
            s = slots_sorted[i]
            if s.start <= t < s.end:
                price = float(s.price_chf_per_kwh)

        prices.append(price)
        t += step

    return prices, day_start


def _quantile(sorted_vals: list[float], q: float) -> float | None:
    """
    Linear-interpolated quantile on sorted values, q in [0,1].
    Returns None if empty.
    """
    if not sorted_vals:
        return None
    if q <= 0:
        return sorted_vals[0]
    if q >= 1:
        return sorted_vals[-1]

    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _median(sorted_vals: list[float]) -> float | None:
    return _quantile(sorted_vals, q=0.5)


def rolling_window_extreme(
    prices: list[float | None], day_start: dt.datetime, window_minutes: int, mode: str
) -> WindowResult | None:
    """
    Find lowest/highest continuous window based on bucket averages.
    Requires all buckets in the window are non-None.
    """
    if window_minutes % BUCKET_MINUTES != 0:
        raise ValueError("window_minutes must be a multiple of 15")

    k = window_minutes // BUCKET_MINUTES
    if k <= 0 or len(prices) < k:
        return None

    best_idx: int | None = None
    best_avg: float | None = None

    # sliding sum for speed, but must handle None
    window_sum = 0.0
    none_count = 0

    # init first window
    for j in range(k):
        v = prices[j]
        if v is None:
            none_count += 1
        else:
            window_sum += v

    def better(a: float, b: float) -> bool:
        return a < b if mode == "min" else a > b

    if none_count == 0:
        best_idx = 0
        best_avg = window_sum / k

    # slide
    for i in range(1, len(prices) - k + 1):
        out_v = prices[i - 1]
        in_v = prices[i + k - 1]

        if out_v is None:
            none_count -= 1
        else:
            window_sum -= out_v

        if in_v is None:
            none_count += 1
        else:
            window_sum += in_v

        if none_count == 0:
            avg = window_sum / k
            if best_avg is None or better(avg, best_avg):
                best_avg = avg
                best_idx = i

    if best_idx is None or best_avg is None:
        return None

    start = day_start + dt.timedelta(minutes=best_idx * BUCKET_MINUTES)
    end = start + dt.timedelta(minutes=window_minutes)
    return WindowResult(start=start, end=end, avg=best_avg)
