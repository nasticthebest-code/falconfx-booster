"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  FalconFX — WEATHER ENGINE  v1.0                                            ║
║  Signal generator, not a decision engine.                                   ║
║                                                                              ║
║  Produces a small, typed WeatherSignal from live Open-Meteo data (no API    ║
║  key required) and feeds it into the EXISTING Booster calculation chain:    ║
║                                                                              ║
║    demand_mult  → multiplies into DemandSimulator's demand_score            ║
║    speed_factor → multiplies into TrafficFriction's effective_speed         ║
║                                                                              ║
║  Fetches are cached and refreshed on a timer (stale_after_minutes), so      ║
║  /booster/compute NEVER makes a live weather API call — every rider reads   ║
║  the same cached signal. If the fetch fails or the cache goes stale, the    ║
║  signal collapses to neutral (1.0 / 1.0) rather than guessing — weather     ║
║  turns itself off instead of running on bad data.                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass

# Single city-wide reference point for v1 — rain doesn't vary block-to-block
# the way traffic does, so one reading is a reasonable simplification.
# Worth revisiting only if FalconFX expands beyond Accra.
ACCRA_LAT = 5.60
ACCRA_LNG = -0.18

_OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={ACCRA_LAT}&longitude={ACCRA_LNG}"
    "&current=precipitation,rain,weather_code"
)


@dataclass
class WeatherSignal:
    rain_mm:      float = 0.0
    condition:    str   = "clear"
    demand_mult:  float = 1.0   # multiplies into demand chain
    speed_factor: float = 1.0   # multiplies into mobility/TTA chain
    fetched_at:   float = 0.0
    is_stale:     bool  = True  # True until a real fetch succeeds


def _interpolate(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """Linear interpolation, clamped at the ends — no step-function jumps
    at band boundaries (same reasoning as _acceleration_band in booster.py)."""
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def _condition_label(rain_mm: float) -> str:
    if rain_mm <= 0.0:
        return "clear"
    if rain_mm < 2.5:
        return "light_rain"
    if rain_mm < 7.6:
        return "moderate_rain"
    if rain_mm < 15.0:
        return "heavy_rain"
    return "severe_storm"


class WeatherEngine:
    """
    Holds ONE cached WeatherSignal for the whole process. Every rider's
    /booster/compute call reads the same cache — nobody triggers a live
    fetch. Only get_signal() itself refreshes, and only when stale.
    """

    def __init__(self):
        self._cached = WeatherSignal()

    def get_signal(self, weather_config: dict) -> WeatherSignal:
        if not weather_config.get("enabled", True):
            return WeatherSignal()  # neutral multipliers, is_stale=True

        stale_after_s = weather_config.get("stale_after_minutes", 20) * 60
        age = time.time() - self._cached.fetched_at

        if self._cached.fetched_at > 0 and age < stale_after_s:
            return self._cached  # fresh — no network call

        try:
            self._cached = self._fetch(weather_config)
        except Exception:
            # Weather must NEVER be able to break Booster. Any failure
            # (timeout, bad JSON, network down) → fall back to neutral
            # and mark stale so callers know not to trust it.
            self._cached = WeatherSignal(is_stale=True)

        return self._cached

    def _fetch(self, weather_config: dict) -> WeatherSignal:
        timeout = weather_config.get("api_timeout_seconds", 5)
        req = urllib.request.Request(
            _OPEN_METEO_URL, headers={"User-Agent": "FalconFX-Booster/4.1"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data.get("current", {})
        rain_mm = float(current.get("rain") or current.get("precipitation") or 0.0)

        demand_max = float(weather_config.get("demand_multiplier_max", 1.30))
        speed_min  = float(weather_config.get("speed_factor_min", 0.75))

        demand_mult  = min(_interpolate(rain_mm, 0.0, 10.0, 1.00, demand_max), demand_max)
        speed_factor = max(_interpolate(rain_mm, 0.0, 10.0, 1.00, speed_min), speed_min)

        return WeatherSignal(
            rain_mm=round(rain_mm, 2),
            condition=_condition_label(rain_mm),
            demand_mult=round(demand_mult, 4),
            speed_factor=round(speed_factor, 4),
            fetched_at=time.time(),
            is_stale=False,
        )


# Module-level singleton — api.py imports and reuses this one instance
# so the cache is actually shared across every request.
weather_engine = WeatherEngine()
