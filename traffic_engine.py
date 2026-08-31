"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  FalconFX — TRAFFIC ENGINE (Booster-side client)  v1.0                      ║
║  Signal generator, not a decision engine.                                   ║
║                                                                              ║
║  Calls the standalone Traffic Signal Engine (TSE) over HTTP and turns its   ║
║  response into two things the EXISTING Booster chain already knows how to   ║
║  consume:                                                                    ║
║                                                                              ║
║    Effect 1 — MOBILITY (speed_factor)                                      ║
║      TSE's speed_ratio feeds TrafficFriction.effective_speed(), same slot   ║
║      weather's speed_factor already occupies. A jammed road slows the      ║
║      rider down; it does NOT make a destination more wanted.                ║
║                                                                              ║
║    Effect 2 — DISPLACEMENT DEMAND (via TrafficDisplacementLayer in         ║
║      booster.py, mirroring MonsoonLayer). When a corridor's queue_pressure  ║
║      crosses a threshold, cells near that corridor's monitor points get a  ║
║      demand boost — stranded car/trotro passengers switching to bikes at   ║
║      the edges of a jam. This engine only supplies the trigger data;       ║
║      the boost mechanism itself lives in booster.py next to Monsoon.       ║
║                                                                              ║
║  Corridor geometry is duplicated here (not fetched from TSE) because       ║
║  Booster and TSE are separate deployable services — Booster needs its own  ║
║  copy to do the nearest-corridor lookup without an extra network hop per   ║
║  rider. If TSE_BASE_URL isn't set, every signal returns neutral instantly. ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import math
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

# Mirrors app/config.py CORRIDORS in the TSE repo exactly. Kept in sync by
# hand — if a corridor is added/changed in TSE, update it here too.
CORRIDORS: dict = {
    "N1":       {"points": ((5.5350, -0.4160), (5.5680, -0.2350), (5.6030, -0.2050)), "radius_km": 3.0},
    "Spintex":  {"points": ((5.6050, -0.1650), (5.5890, -0.1460), (5.5680, -0.1270)), "radius_km": 2.5},
    "Legon":    {"points": ((5.6400, -0.2050), (5.6500, -0.1870), (5.6810, -0.1900)), "radius_km": 2.5},
    "Madina":   {"points": ((5.6810, -0.1900), (5.6920, -0.1660), (5.7050, -0.1530)), "radius_km": 2.5},
    "Airport":  {"points": ((5.6050, -0.1710), (5.6000, -0.1880), (5.5910, -0.2020)), "radius_km": 2.5},
    "Circle":   {"points": ((5.5500, -0.2050), (5.5600, -0.2050), (5.5750, -0.1980)), "radius_km": 2.5},
    "Lapaz":    {"points": ((5.6220, -0.2510), (5.6350, -0.2460), (5.6480, -0.2370)), "radius_km": 2.5},
    "Achimota": {"points": ((5.6330, -0.2430), (5.6550, -0.2350), (5.6750, -0.2250)), "radius_km": 2.5},
}


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearest_corridor(lat: float, lng: float) -> Optional[str]:
    """Which corridor (if any) is close enough to this point to apply its
    signal. Returns None if the point isn't within ANY corridor's
    monitoring_radius_km — most of Booster's grid falls here, since TSE only
    covers 8 named arterials, not the whole city."""
    best_id, best_dist = None, float("inf")
    for cid, c in CORRIDORS.items():
        for plat, plng in c["points"]:
            d = _haversine_km(lat, lng, plat, plng)
            if d < best_dist:
                best_dist, best_id = d, cid
    if best_id is not None and best_dist <= CORRIDORS[best_id]["radius_km"]:
        return best_id
    return None


@dataclass
class TrafficSignal:
    corridor_id:          Optional[str] = None
    queue_pressure:        float = 0.0
    speed_ratio:            float = 1.0    # 1.0 = free-flow, feeds mobility directly
    flow_direction:          str = "stable"
    spillover_probability:  float = 0.0
    fetched_at:              float = 0.0
    is_stale:                 bool = True


def _neutral(corridor_id: Optional[str] = None) -> TrafficSignal:
    return TrafficSignal(corridor_id=corridor_id, is_stale=True)


class TrafficEngine:
    """Caches ONE TrafficSignal per corridor. Every rider's /booster/compute
    call reads from this cache — nobody triggers a live fetch directly."""

    def __init__(self):
        self._cache: dict = {}   # corridor_id -> TrafficSignal

    def get_signal_for_rider(self, lat: float, lng: float, config: dict) -> TrafficSignal:
        """Effect 1 input — the single corridor nearest this rider, or
        neutral if the rider isn't near any monitored corridor."""
        cid = nearest_corridor(lat, lng)
        if cid is None:
            return _neutral()
        return self._get(cid, config)

    def get_all_cached_signals(self, config: dict) -> dict:
        """Effect 2 input — TrafficDisplacementLayer needs to check EVERY
        corridor for congestion, not just the rider's nearest one, since a
        jam elsewhere can still be displacing demand toward cells the rider
        could be routed to. Only returns what's already cached (fresh or
        not) — does NOT trigger fetches for corridors nobody's near yet."""
        return dict(self._cache)

    def _get(self, corridor_id: str, config: dict) -> TrafficSignal:
        if not config.get("enabled", True):
            return _neutral(corridor_id)

        base_url = config.get("tse_base_url") or os.environ.get("TSE_BASE_URL")
        if not base_url:
            return _neutral(corridor_id)  # TSE not deployed/configured yet — silent no-op

        stale_after_s = config.get("stale_after_minutes", 5) * 60
        cached = self._cache.get(corridor_id)
        if cached and cached.fetched_at > 0 and (time.time() - cached.fetched_at) < stale_after_s:
            return cached

        try:
            signal = self._fetch(base_url, corridor_id, config)
        except Exception:
            # Same rule as weather: a failed traffic fetch must NEVER break
            # Booster. Fall back to neutral, mark stale.
            signal = _neutral(corridor_id)

        self._cache[corridor_id] = signal
        return signal

    def _fetch(self, base_url: str, corridor_id: str, config: dict) -> TrafficSignal:
        timeout = config.get("api_timeout_seconds", 5)
        url = f"{base_url.rstrip('/')}/api/v1/signals/{corridor_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "FalconFX-Booster/4.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return TrafficSignal(
            corridor_id=corridor_id,
            queue_pressure=float(data.get("queue_pressure", 0.0)),
            speed_ratio=float(data.get("speed_ratio", 1.0)),
            flow_direction=str(data.get("flow_direction", "stable")),
            spillover_probability=float(data.get("spillover_probability", 0.0)),
            fetched_at=time.time(),
            is_stale=False,
        )


# Module-level singleton — api.py imports and reuses this instance so the
# per-corridor cache is actually shared across every request.
traffic_engine = TrafficEngine()
