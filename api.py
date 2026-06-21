"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  FalconFX BOOSTER  —  FastAPI  v4.1  (External Positioning Overlay Layer)  ║
║                                                                              ║
║  POST /booster/compute        →  BoosterOutput JSON (15-min front-runner)   ║
║  POST /booster/telemetry      →  rider match feedback loop                  ║
║  GET  /booster/telemetry/stats→  per-zone weight table + match scores       ║
║  GET  /booster/health         →  engine status                               ║
║  GET  /booster/shadow         →  active shadow matrix windows                ║
║  GET  /dashboard              →  admin command centre (HTML)                 ║
║  GET  /booster/config         →  current runtime config                      ║
║  POST /booster/config         →  update guards / routing params at runtime   ║
║  POST /booster/ingest         →  parse + append raw POI text to places.json  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import datetime
import json
import math
import os
import re
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from booster import BoosterEngine, RiderTelemetry, GRID_RESOLUTION, PREDICTIVE_OFFSET_MINS


# ══════════════════════════════════════════════════════════════════════════════
# RUNTIME CONFIGURATION STORE
# ══════════════════════════════════════════════════════════════════════════════

_runtime_config: dict = {
    "guards": {
        "ghost_penalty":    True,
        "cash_cow_guard":   True,
        "megachurch_waves": True,
        "corp_arbitrage":   True,
    },
    "params": {
        "velocity_stable_threshold": 8.0,
        "ghost_score_threshold":     85.0,
        "min_profit_threshold":      4.00,
        "fuel_cost_per_km":          1.80,
        "search_radius_km":          5.0,
        "ghost_multiplier":          0.25,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# EXTERNAL MATCH TELEMETRY STORE
#
# Structure:
#   _telemetry[(grid_lat_r3, grid_lng_r3)][hour_slot] = {
#       "weight": float,   # cumulative multiplier (starts 1.0)
#       "pings":  int,     # success_ping count
#       "idles":  int,     # dry_idle count
#       "timeouts": int,   # timeout count
#       "last_updated": str,
#   }
#
# Weight rules:
#   success_ping  → ×1.05  (zone confirmed active, boost 5%)
#   dry_idle      → ×0.90  (zone dry, penalise 10%)
#   timeout       → ×0.97  (ambiguous signal, minor 3% haircut)
#   Weight is clamped to [0.30, 2.50]
# ══════════════════════════════════════════════════════════════════════════════

_telemetry_store: dict = defaultdict(
    lambda: defaultdict(lambda: {
        "weight": 1.0, "pings": 0, "idles": 0, "timeouts": 0, "last_updated": None
    })
)

_WEIGHT_RULES = {
    "success_ping": 1.05,
    "dry_idle":     0.90,
    "timeout":      0.97,
}
_WEIGHT_MIN, _WEIGHT_MAX = 0.30, 2.50


def _match_probability_label(weight: float, pings: int, idles: int) -> str:
    """
    External Match Probability Score for a zone/hour slot.
      HIGH     — weight ≥ 1.12 AND pings ≥ 2     (consistently delivering)
      VOLATILE — weight ≤ 0.82 OR (idles ≥ 3 and pings == 0)  (dry or noisy)
      MEDIUM   — everything else
    """
    if weight >= 1.12 and pings >= 2:
        return "HIGH"
    if weight <= 0.82 or (idles >= 3 and pings == 0):
        return "VOLATILE"
    return "MEDIUM"


def _build_cell_weight_overrides(hour: int) -> dict:
    """Build grid-key → weight dict for the current hour from telemetry store."""
    overrides = {}
    for cell_key, hour_slots in _telemetry_store.items():
        slot = hour_slots.get(hour)
        if slot and slot["weight"] != 1.0:
            overrides[cell_key] = slot["weight"]
    return overrides or None


# ══════════════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class RiderInput(BaseModel):
    lat:                 float
    lng:                 float
    speed_kmh:           float
    heading_deg:         float
    has_active_delivery: bool  = False
    dropoff_lat:         Optional[float] = None
    dropoff_lng:         Optional[float] = None
    fuel_level_pct:      float = Field(100.0, ge=0, le=100)


class HotspotSignal(BaseModel):
    lat:       float
    lng:       float
    intensity: float = Field(..., ge=0, le=100)


class ComputeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "rider": {
                "lat": 5.605, "lng": -0.173,
                "speed_kmh": 28, "heading_deg": 135,
                "has_active_delivery": False,
                "fuel_level_pct": 78,
            },
            "search_radius_km": 5.0,
            "simulate_hotspots": [],
            "rain_active_zones": [],
        }
    })
    rider:              RiderInput
    hour:               Optional[int]           = Field(None, ge=0, lt=24)
    minute:             Optional[int]           = Field(None, ge=0, lt=60)
    search_radius_km:   float                   = Field(5.0, ge=0.5, le=20.0)
    simulate_hotspots:  list[HotspotSignal]     = Field(default_factory=list)
    rain_active_zones:  list[str]               = Field(default_factory=list)


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "rider_id": "rider_gh_001",
            "grid_cell": {"lat": 5.605, "lng": -0.173},
            "timestamp": "2026-06-11T10:30:00Z",
            "status": "success_ping",
        }
    })
    rider_id:  str
    grid_cell: dict              # {"lat": float, "lng": float}
    timestamp: str
    status:    str               # "success_ping" | "dry_idle" | "timeout"


class RuntimeGuards(BaseModel):
    ghost_penalty:    Optional[bool] = None
    cash_cow_guard:   Optional[bool] = None
    megachurch_waves: Optional[bool] = None
    corp_arbitrage:   Optional[bool] = None


class RuntimeParams(BaseModel):
    velocity_stable_threshold: Optional[float] = None
    ghost_score_threshold:     Optional[float] = None
    min_profit_threshold:      Optional[float] = None
    fuel_cost_per_km:          Optional[float] = None
    search_radius_km:          Optional[float] = None
    ghost_multiplier:          Optional[float] = None


class ConfigUpdateRequest(BaseModel):
    guards: Optional[RuntimeGuards] = None
    params: Optional[RuntimeParams] = None


class IngestRequest(BaseModel):
    raw_text:         str
    default_category: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# LIFESPAN
# ══════════════════════════════════════════════════════════════════════════════

PLACES_PATH = os.environ.get("PLACES_PATH", "places.json")
_engine: Optional[BoosterEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine
    print("[FalconFX API v4.1] Loading engine (External Positioning Overlay)...")
    _engine = BoosterEngine(PLACES_PATH)
    print(f"[FalconFX API v4.1] Ready. Predictive offset: +{PREDICTIVE_OFFSET_MINS}min.")
    yield
    _engine = None
    print("[FalconFX API v4.1] Shutdown.")


# ══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="FalconFX Booster API",
    description=(
        "External Positioning Overlay Layer for riders multi-apping on Uber/Yango/Bolt. "
        "Positions riders 15 minutes BEFORE third-party surge visibility using predictive "
        "demand scoring, telemetry feedback loops, and 27,066-POI Accra grid."
    ),
    version="4.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    html_path = _static_dir / "dashboard.html"
    if not html_path.exists():
        raise HTTPException(404, detail="Dashboard not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/booster/health")
def health():
    if _engine is None:
        raise HTTPException(503, detail="Engine not initialised")
    tel_zones   = len(_telemetry_store)
    tel_events  = sum(
        s["pings"] + s["idles"] + s["timeouts"]
        for slots in _telemetry_store.values()
        for s in slots.values()
    )
    return {
        "status":               "ok",
        "version":              "4.1.0",
        "grid_cells":           len(_engine.grid.cells),
        "places_loaded":        sum(len(c.places) for c in _engine.grid.cells.values()),
        "shadow_matrix_zones":  len(_engine.demand.shadow_matrix),
        "road_quality_zones":   len(_engine.friction.road_quality_zones),
        "b2b_wholesale_zones":  len(_engine.demand.b2b_zones),
        "terminal_schedules":   5,
        "predictive_offset_mins": PREDICTIVE_OFFSET_MINS,
        "telemetry_zones_tracked": tel_zones,
        "telemetry_events_total":  tel_events,
        "front_running_mode":   True,
        "algorithm":            "ghost_penalty+accel_scoring+4layer_friction+15min_offset+telemetry_loop",
        "timestamp":            datetime.datetime.utcnow().isoformat() + "Z",
    }


# ══════════════════════════════════════════════════════════════════════════════
# SHADOW MATRIX
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/booster/shadow")
def shadow_active(hour: Optional[int] = None, minute: Optional[int] = None):
    if _engine is None:
        raise HTTPException(503, detail="Engine not initialised")
    now = datetime.datetime.utcnow()
    h = hour   if hour   is not None else now.hour
    m = minute if minute is not None else now.minute
    active = _engine.demand.active_shadow_windows(h, m)
    return {"hour": h, "minute": m, "active_windows": active, "count": len(active)}


# ══════════════════════════════════════════════════════════════════════════════
# COMPUTE  (main endpoint — External Positioning Overlay)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/booster/compute")
def compute(req: ComputeRequest):
    """
    Main positioning endpoint. Demand signals are scored 15 minutes into the
    future (PREDICTIVE_OFFSET_MINS) so riders are parked BEFORE third-party
    apps trigger global visibility. Telemetry weight overrides from rider
    feedback are applied to reinforce confirmed zones and suppress dry ones.
    """
    if _engine is None:
        raise HTTPException(503, detail="Engine not initialised")

    now     = datetime.datetime.utcnow()
    hour    = req.hour   if req.hour   is not None else now.hour
    minute  = req.minute if req.minute is not None else now.minute
    weekday = now.weekday()

    rider = RiderTelemetry(
        lat=req.rider.lat,
        lng=req.rider.lng,
        speed_kmh=req.rider.speed_kmh,
        heading_deg=req.rider.heading_deg,
        has_active_delivery=req.rider.has_active_delivery,
        dropoff_lat=req.rider.dropoff_lat,
        dropoff_lng=req.rider.dropoff_lng,
        fuel_level_pct=req.rider.fuel_level_pct,
    )

    spikes = [(s.lat, s.lng, s.intensity) for s in req.simulate_hotspots]
    radius = _runtime_config["params"]["search_radius_km"]
    if req.search_radius_km != 5.0:
        radius = req.search_radius_km

    # Pull telemetry weight overrides for current hour slot
    cell_overrides = _build_cell_weight_overrides(hour)

    result = _engine.compute(
        rider=rider,
        hour=hour,
        minute=minute,
        search_radius_km=radius,
        simulate_hotspots=spikes or None,
        rain_active_zones=req.rain_active_zones,
        weekday=weekday,
        cell_weight_overrides=cell_overrides,
    )

    output = asdict(result)

    # Apply guard suppressions at API level (non-destructive overlay)
    guards = _runtime_config["guards"]
    if not guards["ghost_penalty"] and output.get("grid_stats"):
        output["grid_stats"]["ghost_cells_suppressed"] = 0
        output["grid_stats"]["ghost_penalty_applied"]  = False
    if not guards["cash_cow_guard"] and output.get("grid_stats"):
        output["grid_stats"]["cash_cow_guard_active"] = False
        output["grid_stats"]["cash_cow_cells"]        = 0
    if not guards["megachurch_waves"] and output.get("grid_stats"):
        output["grid_stats"]["megachurch_waves_firing"]  = 0
        output["grid_stats"]["megachurch_events_active"] = []
    if not guards["corp_arbitrage"]:
        output["corporate_arbitrage"] = None

    # Attach match probability for the rider's current cell
    cell_key = (
        round(req.rider.lat, GRID_RESOLUTION),
        round(req.rider.lng, GRID_RESOLUTION),
    )
    slot = _telemetry_store[cell_key][hour]
    output["match_probability"] = {
        "score": _match_probability_label(slot["weight"], slot["pings"], slot["idles"]),
        "weight": round(slot["weight"], 4),
        "pings":  slot["pings"],
        "idles":  slot["idles"],
    }

    return output


# ══════════════════════════════════════════════════════════════════════════════
# EXTERNAL MATCH TELEMETRY  (rider feedback loop)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/booster/telemetry")
def receive_telemetry(event: TelemetryEvent):
    """
    Accepts rider match feedback from third-party network activity.

    status = "success_ping"  → rider got a match at the recommended cell → +5% weight
    status = "dry_idle"      → rider sat idle, no match → −10% weight
    status = "timeout"       → platform timeout, no visibility → −3% weight

    Weight adjustments compound per hour slot and persist until server restart.
    They are applied to demand scoring on subsequent /booster/compute calls.
    """
    status = event.status
    if status not in _WEIGHT_RULES:
        raise HTTPException(400, detail=f"Unknown status '{status}'. Use: success_ping, dry_idle, timeout")

    # Snap to grid resolution to match engine cell keys
    try:
        lat = float(event.grid_cell["lat"])
        lng = float(event.grid_cell["lng"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(400, detail="grid_cell must contain 'lat' and 'lng' floats")

    cell_key = (round(lat, GRID_RESOLUTION), round(lng, GRID_RESOLUTION))

    # Parse hour from timestamp (fallback to server UTC)
    try:
        ts = datetime.datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
        hour_slot = ts.hour
    except Exception:
        hour_slot = datetime.datetime.utcnow().hour

    slot = _telemetry_store[cell_key][hour_slot]
    multiplier = _WEIGHT_RULES[status]
    new_weight  = max(_WEIGHT_MIN, min(_WEIGHT_MAX, slot["weight"] * multiplier))

    # Increment counters
    if status == "success_ping":
        slot["pings"] += 1
    elif status == "dry_idle":
        slot["idles"] += 1
    else:
        slot["timeouts"] += 1

    slot["weight"]       = round(new_weight, 4)
    slot["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"

    match_score = _match_probability_label(slot["weight"], slot["pings"], slot["idles"])

    return {
        "status":        "accepted",
        "rider_id":      event.rider_id,
        "cell_key":      list(cell_key),
        "hour_slot":     hour_slot,
        "event":         status,
        "new_weight":    slot["weight"],
        "weight_delta":  round(new_weight - (slot["weight"] / multiplier), 4),
        "match_probability_score": match_score,
        "cumulative": {
            "pings":    slot["pings"],
            "idles":    slot["idles"],
            "timeouts": slot["timeouts"],
        },
        "timestamp": slot["last_updated"],
    }


@app.get("/booster/telemetry/stats")
def telemetry_stats(top_n: int = 20, hour: Optional[int] = None):
    """
    Returns the top-N grid cells ranked by telemetry activity,
    with their current External Match Probability Score.
    Used by the dashboard to display live zone intelligence.
    """
    now_h = hour if hour is not None else datetime.datetime.utcnow().hour

    rows = []
    for cell_key, hour_slots in _telemetry_store.items():
        # Aggregate all hour slots for ranking; show current-hour slot details
        total_pings   = sum(s["pings"]    for s in hour_slots.values())
        total_idles   = sum(s["idles"]    for s in hour_slots.values())
        total_timeouts= sum(s["timeouts"] for s in hour_slots.values())
        total_events  = total_pings + total_idles + total_timeouts

        current_slot  = hour_slots.get(now_h, {"weight": 1.0, "pings": 0, "idles": 0, "timeouts": 0})
        cur_weight    = current_slot["weight"]
        match_score   = _match_probability_label(
            cur_weight, current_slot["pings"], current_slot["idles"]
        )

        rows.append({
            "cell_lat":       cell_key[0],
            "cell_lng":       cell_key[1],
            "current_weight": round(cur_weight, 4),
            "match_probability_score": match_score,
            "current_hour_pings":   current_slot["pings"],
            "current_hour_idles":   current_slot["idles"],
            "total_pings":    total_pings,
            "total_idles":    total_idles,
            "total_timeouts": total_timeouts,
            "total_events":   total_events,
            "last_updated":   current_slot.get("last_updated"),
            "hour_slots_tracked": len(hour_slots),
        })

    # Sort by total event volume descending
    rows.sort(key=lambda r: r["total_events"], reverse=True)

    summary = {
        "high":     sum(1 for r in rows if r["match_probability_score"] == "HIGH"),
        "medium":   sum(1 for r in rows if r["match_probability_score"] == "MEDIUM"),
        "volatile": sum(1 for r in rows if r["match_probability_score"] == "VOLATILE"),
        "untested": 0,   # cells with no events (not in store)
    }

    return {
        "current_hour":    now_h,
        "zones_tracked":   len(rows),
        "summary":         summary,
        "predictive_offset_mins": PREDICTIVE_OFFSET_MINS,
        "top_zones":       rows[:top_n],
        "timestamp":       datetime.datetime.utcnow().isoformat() + "Z",
    }


class TelemetryResetRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {"lat": 5.605, "lng": -0.173, "hour": None}
    })
    lat:  float
    lng:  float
    hour: Optional[int] = None   # omit to reset ALL hour slots for this cell


@app.post("/booster/telemetry/reset")
def telemetry_reset(req: TelemetryResetRequest):
    """
    Manual safety valve — added alongside the telemetry feedback loop so a
    bad data point (mistyped earning, buggy client repeatedly firing the
    wrong status) can be corrected without restarting the whole server.

    Resets the named cell (and optionally a single hour slot within it)
    back to neutral: weight=1.0, all counters zeroed. Does NOT delete the
    cell entirely — it stays in _telemetry_store so it keeps appearing in
    /booster/telemetry/stats, just with a clean slate.
    """
    cell_key = (round(req.lat, GRID_RESOLUTION), round(req.lng, GRID_RESOLUTION))
    if cell_key not in _telemetry_store:
        raise HTTPException(404, detail=f"No telemetry recorded for cell {cell_key}")

    neutral = {"weight": 1.0, "pings": 0, "idles": 0, "timeouts": 0,
               "last_updated": datetime.datetime.utcnow().isoformat() + "Z"}

    if req.hour is not None:
        if not (0 <= req.hour <= 23):
            raise HTTPException(400, detail="hour must be 0-23")
        _telemetry_store[cell_key][req.hour] = dict(neutral)
        reset_scope = f"hour {req.hour} only"
    else:
        for h in list(_telemetry_store[cell_key].keys()):
            _telemetry_store[cell_key][h] = dict(neutral)
        reset_scope = "all hour slots"

    return {
        "status":      "reset",
        "cell_key":    list(cell_key),
        "scope":       reset_scope,
        "new_weight":  1.0,
        "timestamp":   neutral["last_updated"],
    }


@app.get("/booster/telemetry/audit")
def telemetry_audit():
    """
    Flags telemetry cells whose weight has drifted to an extreme — likely
    candidates for a bad-data investigation or a manual reset via
    /booster/telemetry/reset. A cell sitting at _WEIGHT_MIN or _WEIGHT_MAX
    has been pushed there by repeated identical events, which is either a
    genuinely consistent real-world pattern OR a sign something's firing
    incorrectly (e.g. dry_idle events on every tick due to a client bug).
    This endpoint doesn't decide which — it just surfaces the candidates
    for a human to look at.
    """
    flagged = []
    for cell_key, hour_slots in _telemetry_store.items():
        for hour, slot in hour_slots.items():
            w = slot["weight"]
            total_events = slot["pings"] + slot["idles"] + slot["timeouts"]
            if total_events < 3:
                continue  # too little data to call this suspicious either way
            at_floor = w <= _WEIGHT_MIN * 1.05
            at_ceiling = w >= _WEIGHT_MAX * 0.95
            if at_floor or at_ceiling:
                flagged.append({
                    "cell_lat": cell_key[0], "cell_lng": cell_key[1], "hour": hour,
                    "weight": round(w, 4),
                    "extreme": "floor" if at_floor else "ceiling",
                    "pings": slot["pings"], "idles": slot["idles"], "timeouts": slot["timeouts"],
                    "total_events": total_events,
                })
    flagged.sort(key=lambda r: r["total_events"], reverse=True)
    return {
        "flagged_count": len(flagged),
        "weight_bounds": {"min": _WEIGHT_MIN, "max": _WEIGHT_MAX},
        "flagged_cells": flagged,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


# ══════════════════════════════════════════════════════════════════════════════
# RUNTIME CONFIG
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/booster/config")
def get_config():
    return _runtime_config


@app.post("/booster/config")
def update_config(req: ConfigUpdateRequest):
    if req.guards:
        _runtime_config["guards"].update(req.guards.model_dump(exclude_none=True))
    if req.params:
        _runtime_config["params"].update(req.params.model_dump(exclude_none=True))
    return {
        "status":    "applied",
        "guards":    _runtime_config["guards"],
        "params":    _runtime_config["params"],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    }


# ══════════════════════════════════════════════════════════════════════════════
# DATA INGEST
# ══════════════════════════════════════════════════════════════════════════════

_AREA_CENTROIDS: dict[str, tuple] = {
    "achimota":         (5.6390, -0.2370),
    "lapaz":            (5.6100, -0.2440),
    "madina":           (5.6810, -0.1680),
    "legon":            (5.6500, -0.1920),
    "east legon hills": (5.6580, -0.1480),
    "east legon":       (5.6470, -0.1600),
    "upsa":             (5.6472, -0.1628),
    "circle":           (5.5710, -0.2215),
    "spintex":          (5.6180, -0.1100),
    "dansoman":         (5.5450, -0.2540),
    "kaneshie":         (5.5560, -0.2440),
    "nima":             (5.5890, -0.2110),
    "osu":              (5.5650, -0.1780),
    "teshie":           (5.5800, -0.1080),
    "nungua":           (5.5700, -0.0860),
    "kasoa":            (5.5330, -0.4190),
    "ashaiman":         (5.6975, 0.0310),
    "adabraka":         (5.5630, -0.2130),
    "abossey okai":     (5.5650, -0.2310),
    "korle-bu":         (5.5480, -0.2300),
    "korle bu":         (5.5480, -0.2300),
    "trade fair":       (5.5480, -0.1540),
    "tse addo":         (5.5460, -0.1520),
    "pokuase":          (5.6930, -0.2730),
    "dome":             (5.6720, -0.2380),
    "accra":            (5.5600, -0.2050),
}

_CAT_HINTS: list[tuple] = [
    (["station", "terminal", "trotro", "stc", "vip", "neoplan", "lorry park",
      "interchange", "underbridge", "overhead", "loading zone", "staging"],  "transport"),
    (["market", "spare parts", "wholesale", "plastic lane", "container",
      "texpo", "fulfillment", "distribution", "pharma"],                     "market"),
    (["mall", "melcom", "accra mall", "shopping"],                           "mall"),
    (["hostel", "airbnb", "apartments", "housing", "halls", "hotel"],        "hotel"),
    (["chop bar", "waakye", "canteen", "food", "tatale", "joint",
      "restaurant", "bar & grill", "bar and grill", "culinary"],             "food"),
    (["junction", "roundabout", "enclave", "cluster", "grid",
      "road", "street", "avenue", "highway", "alley"],                       "area"),
]


def _infer_category(name: str, desc: str, default: Optional[str]) -> str:
    if default:
        return default
    combined = (name + " " + desc).lower()
    for keywords, cat in _CAT_HINTS:
        if any(kw in combined for kw in keywords):
            return cat
    return "area"


def _haversine_m(lat1, lng1, lat2, lng2) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _proximity_guard(lat, lng, places, guard_m=20.0) -> bool:
    return any(_haversine_m(lat, lng, p["lat"], p["lng"]) <= guard_m for p in places)


def _infer_centroid(name: str, desc: str) -> Optional[tuple]:
    import random
    combined = (name + " " + desc).lower()
    for area_key in sorted(_AREA_CENTROIDS, key=len, reverse=True):
        if area_key in combined:
            base_lat, base_lng = _AREA_CENTROIDS[area_key]
            jitter = 0.0004
            return round(base_lat + random.uniform(-jitter, jitter), 6), \
                   round(base_lng + random.uniform(-jitter, jitter), 6)
    return None


@app.post("/booster/ingest")
def ingest_data(req: IngestRequest):
    pattern = re.compile(
        r"^[-*•]?\s*(?P<name>[A-Z][^(\n]{3,60}?)\s*"
        r"(?:\((?P<desc>[^)]{0,120})\))?\s*$",
        re.MULTILINE,
    )
    candidates = [
        (m.group("name").strip().strip("-•*").strip(), (m.group("desc") or "").strip())
        for m in pattern.finditer(req.raw_text)
        if len(m.group("name").strip()) >= 4
        and not re.match(r"^[-─=]+", m.group("name").strip())
    ]

    if not candidates:
        return {"status": "no_candidates", "parsed": 0, "added": 0, "skipped": 0}

    try:
        with open(PLACES_PATH, "r", encoding="utf-8") as f:
            places = json.load(f)
    except Exception as e:
        raise HTTPException(500, detail=f"Cannot read {PLACES_PATH}: {e}")

    added_names, skipped_names, unresolved = [], [], []
    for name, desc in candidates:
        coords = _infer_centroid(name, desc)
        if coords is None:
            unresolved.append(name)
            continue
        lat, lng = coords
        if _proximity_guard(lat, lng, places):
            skipped_names.append(name)
            continue
        places.append({
            "name": name, "aliases": [desc] if desc else [],
            "lat": lat, "lng": lng,
            "cat": _infer_category(name, desc, req.default_category),
            "source": "falconfx_ingest_api",
        })
        added_names.append(name)

    if added_names:
        try:
            with open(PLACES_PATH, "w", encoding="utf-8") as f:
                json.dump(places, f, ensure_ascii=False, separators=(",", ":"))
        except Exception as e:
            raise HTTPException(500, detail=f"Cannot write {PLACES_PATH}: {e}")

    return {
        "status": "ok", "parsed": len(candidates),
        "added": len(added_names), "skipped": len(skipped_names),
        "unresolved": unresolved, "total_pois": len(places),
        "added_names": added_names, "skipped_names": skipped_names,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
