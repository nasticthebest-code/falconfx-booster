"""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘  FalconFX â€” BOOSTER  |  Predictive Demand Engine  v4.0                     â•‘
â•‘  Accra, Ghana  |  Asymmetric Companion Weapon Architecture                  â•‘
â•‘                                                                              â•‘
â•‘  STRATEGIC PARADIGM: SECONDARY COMPANION MAP                                â•‘
â•‘  Runs alongside Yango / Bolt / Uber / Hubtel â€” NEVER replaces them.         â•‘
â•‘  Single loyalty: maximise rider net daily income per km.                    â•‘
â•‘                                                                              â•‘
â•‘  CORE ALGORITHM: PURE PREDICTION â€” NOT REACTION                             â•‘
â•‘  Ghost Penalty (Fading)   â†’ dying surge â‰¥85 score, velocity falling:       â•‘
â•‘                             75% haircut â€” mainstream sees it, dead zone.    â•‘
â•‘  Cash Cow Guard (Stable)  â†’ â‰¥85 score, velocity STABLE/RISING: zero        â•‘
â•‘                             haircut â€” active market rush, keep printing.    â•‘
â•‘  Acceleration Multiplier  â†’ 40-78 band: 1.5-2.0x bonus for imminent        â•‘
â•‘                             pre-checkout explosion (3-5 min before peak).   â•‘
â•‘  TTA Lock                 â†’ synchronises rider arrival to 3-5 min BEFORE   â•‘
â•‘                             checkout so rider is parked before Order fires. â•‘
â•‘  Mega-Church Waves        â†’ Perez Dome / Action Chapel / ICGC / BlackStar  â•‘
â•‘                             synchronized dismissal demand spikes injected.  â•‘
â•‘  Corporate Arbitrage      â†’ Landing zone gate delays baked into net yield.  â•‘
â•‘                             Legal/consular push + Pre-COB crunch vectors.   â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
"""

from __future__ import annotations

import json
import math
import random
import datetime
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Optional


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 1 â€” CONSTANTS & CONFIGURATION
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

EARTH_RADIUS_KM = 6371.0
GRID_RESOLUTION = 3          # decimal places â†’ ~110 m cell at Accra latitude
FUEL_COST_GHS_PER_KM = 1.80  # GHS per km (petrol-equivalent for motorbike)
MIN_PROFIT_THRESHOLD = 4.00  # GHS â€” below this, HOLD is recommended
ACCRA_LAT_CENTRE = 5.60
ACCRA_LNG_CENTRE = -0.18
OFF_PEAK_SPEED_KMH = 50.0    # baseline free-flow speed
ARTERIAL_PEAK_DEGRADATION = 0.60   # 60% slowdown on 70% of major arteries
ARTERIAL_PEAK_COVERAGE = 0.70      # fraction of arterial grid affected

# â”€â”€ Velocity Trend Validation â€” Cash Cow Guard threshold
# If a zone's demand_velocity >= this, the ghost haircut is SUPPRESSED even
# at score â‰¥ 85. The zone is still printing money (deep market rush, downpour).
VELOCITY_TREND_STABLE_THRESHOLD = 8.0    # velocity units â€” above = sustained cash cow

# â”€â”€ EXTERNAL POSITIONING OVERLAY â€” Predictive Front-Runner Offset
# Demand signals are injected for (current_time + PREDICTIVE_OFFSET_MINS) so riders
# are positioned BEFORE third-party apps trigger global surge visibility.
# Covers: corporate COB ramp, nightlife pre-loading, church dismissal, AM rush.
PREDICTIVE_OFFSET_MINS = 15              # minutes ahead of live clock

# â”€â”€ Category demand weights (how likely a place type generates delivery orders)
CATEGORY_DEMAND_WEIGHT = {
    "food":       10,
    "market":      9,
    "mall":        8,
    "hospital":    6,
    "university":  5,
    "school":      4,
    "bank":        3,
    "hotel":       5,
    "leisure":     4,
    "transport":   7,
    "office":      4,
    "govt":        2,
    "church":      1,
    "fuel":        1,
    "police":      0,
    "area":        2,
    "other":       1,
}

# â”€â”€ Kitchen prep buffers in minutes (category â†’ min, max)
KITCHEN_PREP_BUFFER = {
    "food":    (12, 15),   # chop bars, local restaurants â€” cook-to-order
    "mall":    (3,  5),    # retail pick-pack
    "market":  (5,  8),    # market vendors assembling orders
    "hotel":   (10, 20),   # room service / F&B
    "other":   (2,  4),
}
FUFU_LIGHTSOUP_BUFFER = (12, 15)   # dedicated buffer for heavy Ghanaian mains
INSTANT_CATEGORIES = {
    "hospital", "bank", "fuel", "transport", "university", "school", "office", "govt"
}

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CORRIDOR TRAFFIC CONSTRAINTS  (ACCRA_TRAFFIC_CONSTRAINTS)
# Exact degradation profiles per arterial corridor with 2026 constraints.
# peak_hours: list of (h_start, m_start, h_end, m_end) tuples (24-hr clock)
# speed_degradation: fraction of speed LOST (0.45 = 45% slower than baseline)
# disruption_flag: force reroute avoidance when True
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ACCRA_TRAFFIC_CONSTRAINTS = {
    "spintex_road": {
        "lat": 5.620, "lng": -0.110,
        "radius_km": 4.0,
        "peak_hours": [(6, 30, 9, 30), (16, 30, 20, 0)],
        "speed_degradation": 0.45,      # 45% slowdown near Flowerpot/Palace Mall
        "critical_nodes": ["flowerpot", "palace_mall", "teshie_link"],
    },
    "liberation_road": {
        "lat": 5.576, "lng": -0.196,
        "radius_km": 3.0,
        "peak_hours": [(7, 0, 9, 0), (16, 0, 19, 0)],
        "speed_degradation": 0.35,      # 35% airport merging drag
    },
    "tetteh_quarshie": {
        "lat": 5.650, "lng": -0.172,
        "radius_km": 2.5,
        "peak_hours": [(6, 30, 10, 0), (15, 30, 20, 30)],
        "speed_degradation": 0.75,      # 75% â€” 2026 lane closures + 4â†’3 lane reduction
        "accra_madina_degradation": 0.75,  # worst direction: Accra â†’ Madina
        "disruption_flag": True,           # engine avoids Accra-Madina cuts
    },
    "george_bush_n1": {
        "lat": 5.610, "lng": -0.206,
        "radius_km": 3.5,
        "peak_hours": [(6, 30, 9, 30), (12, 0, 14, 0), (16, 0, 20, 30)],
        "speed_degradation": 0.50,      # 50% tie-in choke at interchange
    },
}

# â”€â”€ Known Accra traffic bottlenecks (expanded â€” all major choke points)
#    (name, lat, lng, peak_h_start, peak_h_end, severity)
BOTTLENECKS = [
    # Spintex corridor
    ("Spintex / Flowerpot (AM)",    5.620, -0.110, 6,  10, 0.45),
    ("Spintex / Palace Mall (PM)",  5.622, -0.108, 16, 20, 0.45),
    # Liberation Road
    ("Liberation Road (AM)",        5.576, -0.196, 7,   9, 0.35),
    ("Liberation Road (PM)",        5.576, -0.196, 16, 19, 0.35),
    # Tetteh Quarshie â€” 2026 DISRUPTION FLAG: elevated to 75%
    ("Tetteh Quarshie (AM)",        5.650, -0.172, 6,  10, 0.75),
    ("Tetteh Quarshie (PM)",        5.650, -0.172, 15, 21, 0.70),
    # George Bush / N1
    ("George Bush N1 (AM)",         5.610, -0.206, 6,  10, 0.50),
    ("George Bush N1 (Midday)",     5.610, -0.206, 12, 14, 0.40),
    ("George Bush N1 (PM)",         5.610, -0.206, 16, 21, 0.50),
    # Legacy choke points
    ("Kwame Nkrumah Circle",        5.571, -0.222, 7,  19, 0.50),
    ("Kaneshie",                    5.560, -0.242, 7,  19, 0.55),
    ("Tema Motorway Toll",          5.620,  0.000, 7,   9, 0.60),
    ("37 Military Hospital Jct",    5.590, -0.188, 7,  19, 0.60),
    ("Achimota Overhead",           5.639, -0.237, 7,   9, 0.58),
    ("Caprice/Labone",              5.572, -0.166, 17, 20, 0.65),
    ("Adenta Barrier",              5.696, -0.163, 7,   9, 0.50),
    ("Madina Market",               5.680, -0.168, 8,  18, 0.55),
    # Narrow alley / AMA Clamp choke points
    ("Opera Square / M.A. Street",  5.551, -0.207, 7,  18, 0.60),
    ("Kantamanto / Baltimore St",   5.548, -0.208, 6,  10, 0.55),
    ("Nii Abose St (Abossey Okai)", 5.566, -0.231, 7,  19, 0.55),
    ("Shiashie Trotro Corridor",    5.608, -0.166, 11, 14, 0.50),
    ("Danquah Circle (Waakye AM)",  5.567, -0.178, 7,   9, 0.55),
    ("Independence Ave / KojoThom", 5.554, -0.204, 7,  20, 0.45),
]

# â”€â”€ Pedestrian Congestion Zones (separate friction layer, always-on during window)
#    (name, lat, lng, radius_km, h_start_float, h_end_float, ped_penalty)
PEDESTRIAN_CONGESTION_ZONES = [
    ("Danquah Circle Waakye Rush",   5.567, -0.178, 0.35, 7.0,  9.5,  0.30),
    ("Makola Market Foot Traffic",   5.550, -0.206, 0.50, 7.0, 18.0,  0.20),
    ("Kantamanto Street Press",      5.548, -0.208, 0.40, 6.0,  9.0,  0.35),
    ("Kantamanto Street Press (PM)", 5.548, -0.208, 0.40, 14.0, 16.0, 0.28),
    ("Opera Square Alley Clamp",     5.551, -0.207, 0.30, 7.0, 18.0,  0.40),
    ("Shiashie Trotro Terminal",     5.608, -0.166, 0.40, 11.5, 13.5, 0.35),
    ("Kaneshie Market Overflow",     5.556, -0.244, 0.45, 7.0, 19.0,  0.25),
    ("Agbogbloshie Morning Rush",    5.556, -0.231, 0.40, 6.0,  9.0,  0.30),
    ("Neoplan/STC Forecourt",        5.560, -0.205, 0.30, 6.0, 21.0,  0.22),
    ("Osu Oxford St Night (PM)",     5.564, -0.178, 0.50, 20.0, 23.0, 0.25),
]

# â”€â”€ Low-density outskirt zones for Return Ticket Arbitrage
LOW_DENSITY_ZONES = [
    ("Adenta",    5.706, -0.163, 5.0),
    ("Kasoa",     5.534, -0.419, 4.0),
    ("Weija",     5.567, -0.321, 3.5),
    ("Dodowa",    5.884, -0.104, 4.0),
    ("Ashaiman",  5.698,  0.031, 3.5),
    ("Bortianor", 5.557, -0.323, 3.0),
    ("Oyibi",     5.770, -0.120, 3.0),
]

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# CORPORATE LANDING ZONE FRICTION CONSTANTS
# Bakes physical door-to-desk delays (gate screening + walk + lift) into the
# Net Hourly Yield calculation to prevent the Invisible Non-Riding Time Drain.
# peak_windows: [(h_start_float, h_end_float)]  decimal hours
# sunday_closed: True â†’ 100% access denial on Sundays
# saturday_capacity: 0.5 = 50% reduced, 1.0 = full
# cutoff_hour: hard deadline â€” engine issues URGENT note if approaching
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CORPORATE_LANDING_ZONES = [
    {
        "name": "Ministries District / Accra Central Financial Core",
        "lat": 5.558, "lng": -0.197,
        "radius_km": 0.8,
        "gate_screening_min": 15,    # ID check + package inspection
        "walk_distance_m": 300,      # bikes banned inside â€” walk from perimeter
        "elevator_wait_min": 12,
        "peak_windows": [(8.0, 9.5), (11.0, 12.5), (14.5, 16.0)],
        "sunday_closed": True,
        "saturday_capacity": 1.0,
        "cutoff_hour": 16.5,         # Ministries shuts at 16:30 sharp
    },
    {
        "name": "Ridge / North Ridge Corporate Enclaves",
        "lat": 5.574, "lng": -0.191,
        "radius_km": 0.7,
        "gate_screening_min": 8,
        "walk_distance_m": 100,
        "elevator_wait_min": 9,
        "peak_windows": [(9.0, 10.5), (15.0, 16.5)],
        "sunday_closed": False,
        "saturday_capacity": 1.0,
        "cutoff_hour": 18.0,
    },
    {
        "name": "Airport City Commercial Hub",
        "lat": 5.605, "lng": -0.167,
        "radius_km": 0.9,
        "gate_screening_min": 10,    # package X-ray at aviation security
        "walk_distance_m": 200,      # 200m from airport perimeter
        "elevator_wait_min": 10,
        "peak_windows": [(8.5, 10.0), (11.5, 13.0)],
        "sunday_closed": False,
        "saturday_capacity": 0.5,    # 50% reduced Saturday capacity
        "cutoff_hour": 19.0,
    },
]

# â”€â”€ Centralized Pickup Nodes â€” exact access points for each corporate zone
CORPORATE_PICKUP_NODES = [
    {
        "name": "Ecobank HQ â€” Ground Floor Mailroom Annex",
        "lat": 5.572, "lng": -0.194,
        "flow": "A",
        "access": "Rear service gate, Morocco Lane, West Ridge",
    },
    {
        "name": "Standard Chartered Tower â€” Basement Courier Bays",
        "lat": 5.604, "lng": -0.168,
        "flow": "B",
        "access": "Basement courier bay B1 level, Airport City",
    },
    {
        "name": "Ministries â€” Ground Floor General Registry",
        "lat": 5.556, "lng": -0.198,
        "flow": "A",
        "access": "General Registry offices, manual stamp books required",
    },
]

# â”€â”€ Outbound Routing Flows (three destination categories)
CORPORATE_OUTBOUND_FLOWS = {
    "A": {
        "name": "Regulatory / Judicial Flow",
        "description": "High Street Courts + Registrar General's Dept, Accra Central",
        "destinations": [
            {"name": "High Street Courts", "lat": 5.548, "lng": -0.198},
            {"name": "Registrar General's Dept", "lat": 5.552, "lng": -0.202},
        ],
    },
    "B": {
        "name": "International Cargo Flow",
        "description": "KIA Logistics Village / GACC Ghana Customs",
        "destinations": [
            {"name": "KIA Logistics Village", "lat": 5.604, "lng": -0.173},
            {"name": "GACC / Customs Examination", "lat": 5.598, "lng": -0.165},
        ],
    },
    "C": {
        "name": "Upcountry Domestic Sorting Flow",
        "description": "Kwame Nkrumah Circle VIP/STC or North Industrial Area",
        "destinations": [
            {"name": "Kwame Nkrumah Circle VIP / STC", "lat": 5.571, "lng": -0.222},
            {"name": "North Industrial Area Sorting Hub", "lat": 5.580, "lng": -0.230},
        ],
    },
}

# â”€â”€ Terminal Schedules for WaybillInterceptor (exact real-world timetables)
#    windows: list of (h_start_float, h_end_float) â€” decimal hours
#    peak_stacking: high-density arrival clusters within windows
#    type: "FIRST_COME" | "STC_HOURLY" | "MIXED"
#    weekend_days: 0=Monâ€¦6=Sun; listed days get weekend_multiplier applied
TERMINAL_SCHEDULES = [
    {
        "name": "Kwame Nkrumah Circle (VIP/Odawna/Obra Spot/Mamobi)",
        "lat": 5.571, "lng": -0.222,
        "windows": [(5.5, 9.5), (12.0, 14.0), (16.5, 20.5)],
        "peak_stacking": [(6.0, 8.0), (17.0, 19.5)],
        "weekend_days": [4, 6],       # Friday (4), Sunday (6) + public holiday eves
        "weekend_multiplier": 1.4,
        "type": "FIRST_COME",         # VIP: first-come first-served
        "arrival_interval_min": 25,   # buses every 25-35 min during windows
    },
    {
        "name": "Kaneshie Motorway Terminal",
        "lat": 5.557, "lng": -0.244,
        "windows": [(5.0, 8.5), (16.0, 21.0)],
        "peak_stacking": [(5.0, 8.5), (17.0, 21.0)],
        "weekend_days": [3, 4, 5, 6],  # Thu-Sun peak: Thu(3) Fri(4) Sat(5) Sun(6)
        "weekend_multiplier": 1.5,     # Sun afternoon/evening heavily optimised inward
        "type": "FIRST_COME",
        "arrival_interval_min": 30,
    },
    {
        "name": "Neoplan Station / STC",
        "lat": 5.560, "lng": -0.205,
        "windows": [(6.0, 9.0), (13.0, 15.0), (18.0, 21.0)],
        "peak_stacking": [(8.0, 9.0)],  # Cape Coast inbound at 08:00
        "cape_coast_proxy_hour": 8.0,    # dedicated Cape Coast tracking proxy
        "stc_mon_fri_hourly": True,      # STC departs on the hour 06:00-18:00 Mon-Fri
        "weekend_days": [5, 6],
        "weekend_multiplier": 1.3,
        "type": "STC_HOURLY",
        "arrival_interval_min": 35,
    },
    {
        "name": "Tema Station",
        "lat": 5.673, "lng":  0.013,
        "windows": [(6.0, 21.0)],
        "peak_stacking": [(6.0, 9.0), (16.0, 20.0)],
        "weekend_days": [5, 6],
        "weekend_multiplier": 1.2,
        "type": "MIXED",
        "arrival_interval_min": 30,
    },
    {
        "name": "Madina Lorry Park",
        "lat": 5.682, "lng": -0.169,
        "windows": [(6.0, 20.0)],
        "peak_stacking": [(6.0, 9.0), (15.0, 19.0)],
        "weekend_days": [4, 5, 6],
        "weekend_multiplier": 1.2,
        "type": "FIRST_COME",
        "arrival_interval_min": 30,
    },
]

# â”€â”€ B2B Wholesale & Waybill Epicenters
#    day_weights: {weekday_int: multiplier}  0=Monâ€¦6=Sun
#    windows: [(h_start_float, h_end_float), ...]
#    primary_window: first dispatch wave
#    secondary_window: clearance wave
B2B_WHOLESALE_ZONES = [
    {
        "name": "Makola Market & Opera Square",
        "lat": 5.550, "lng": -0.206,
        "radius_km": 0.6,
        "day_weights": {0: 0.6, 1: 0.7, 2: 1.5, 3: 0.8, 4: 0.9, 5: 1.5, 6: 0.3},
        # Wed (2) and Sat (5) heavy restock multipliers
        "primary_window": (7.0, 10.0),    # morning wholesale dispatch wave
        "secondary_window": (15.0, 17.0), # afternoon clearance wave
        "ama_clamp_risk": True,            # narrow alleys â†’ rapid mobile pickup vectors
        "base_intensity": 70,
    },
    {
        "name": "Kantamanto Market (Second-Hand Clothing Transit)",
        "lat": 5.548, "lng": -0.208,
        "radius_km": 0.5,
        "day_weights": {0: 0.4, 1: 0.5, 2: 1.8, 3: 0.5, 4: 1.8, 5: 0.6, 6: 0.3},
        # Wed (2) and Fri (4) pre-weekend retail allocation runs
        "primary_window": (6.0, 9.0),     # 15M garments per week filter here
        "secondary_window": (14.0, 16.0),
        "ama_clamp_risk": True,
        "base_intensity": 65,
    },
    {
        "name": "Abossey Okai (Automotive Spare Parts Hub)",
        "lat": 5.566, "lng": -0.231,
        "radius_km": 0.6,
        # Mon-Tue 07:00-18:00, Wed-Thu 07:30-18:00, Fri-Sat 08:00-17:30
        "day_weights": {0: 1.0, 1: 1.2, 2: 1.0, 3: 1.2, 4: 1.3, 5: 0.9, 6: 0.1},
        # Tue/Thu/Fri mechanic run days
        "primary_window": (7.5, 10.5),   # mechanic run peak
        "secondary_window": (13.0, 15.0),
        "ama_clamp_risk": False,
        "base_intensity": 60,
    },
]

# â”€â”€ Rain-impacted district polygons
RAIN_FLOOD_ZONES = [
    ("Accra Central",  5.550, -0.206, 1.5),
    ("Lapaz",          5.609, -0.243, 1.2),
    ("Kaneshie Low",   5.556, -0.244, 1.0),
    ("Adabraka",       5.562, -0.212, 0.8),
    ("Nima",           5.589, -0.211, 1.0),
    ("Alajo",          5.591, -0.225, 0.9),
    ("Abossey Okai",   5.566, -0.231, 0.8),
]

# â”€â”€ Road Quality Zones: unpaved / potholed / unstructured secondary roads
ROAD_QUALITY_ZONES = [
    ("Nima/Maamobi Back Streets",    5.589, -0.211, 0.6, 0.30),
    ("Chorkor Coastal Track",        5.537, -0.243, 0.8, 0.42),
    ("James Town/Ussher Lanes",      5.548, -0.206, 0.5, 0.35),
    ("Agbogbloshie Unpaved",         5.556, -0.231, 0.6, 0.45),
    ("Kasoa Pothole Corridor",       5.534, -0.419, 1.5, 0.48),
    ("Ashaiman Back Roads",          5.698,  0.031, 0.8, 0.35),
    ("Oyibi/Dodowa Rural Gravel",    5.770, -0.120, 2.0, 0.55),
    ("Darkuman Secondary",           5.584, -0.242, 0.5, 0.25),
    ("Alajo Back Streets",           5.591, -0.225, 0.4, 0.28),
    ("Labadi Beach Track",           5.553, -0.148, 0.6, 0.22),
    ("Adenta Unpaved Links",         5.706, -0.163, 0.8, 0.30),
    ("Weija Gravel Road",            5.567, -0.321, 0.7, 0.38),
    ("Dansoman Back Lanes",          5.546, -0.253, 0.5, 0.25),
    ("Kotobabi Unpaved",             5.581, -0.220, 0.4, 0.28),
]

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# SHADOW MATRIX â€” Offline / WhatsApp / phone-in demand sources invisible
# to aggregator platforms. Fully expanded v3.0 (27 zones).
#
# Format: (name, lat, lng, radius_km, windows [(h_start, h_end)], intensity)
# h values are decimal hours: 7.5 = 07:30, 20.0 = 20:00
# intensity 0-100: demand boost score injected into nearby grid cells
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
SHADOW_MATRIX = [
    # â”€â”€ MORNING WAAKYE WAVE (07:00-09:00, peak 07:30-09:30)
    ("Nima Waakye Belt",              5.589, -0.211, 0.4, [(7.0, 9.5)],              62),
    ("Osu Danquah Circle Waakye",     5.567, -0.178, 0.4, [(7.0, 9.5)],              72),  # legendary
    ("Cantonments Road Waakye",       5.573, -0.175, 0.3, [(7.0, 9.5)],              58),
    ("Kojo Thompson Rd Accra Central",5.554, -0.204, 0.4, [(7.0, 9.5)],              66),  # peak 07:30-09:30
    ("Agbogbloshie Waakye Spot",      5.556, -0.231, 0.3, [(7.0, 9.5)],              60),
    ("Lapaz Waakye Corner",           5.609, -0.243, 0.3, [(7.0, 9.5)],              52),
    ("Madina Canteen Row",            5.682, -0.169, 0.3, [(7.0, 9.5),(12.0,14.0)],  55),
    ("Achimota Market Food",          5.639, -0.237, 0.4, [(7.0, 9.5),(12.0,14.0)],  52),
    ("Darkuman Junction Chop",        5.584, -0.242, 0.3, [(7.0, 9.5),(12.0,14.0)],  44),
    ("Ashaiman Market Food",          5.698,  0.031, 0.4, [(7.0, 9.5),(12.0,14.0)],  50),
    ("Dansoman Market Food",          5.546, -0.253, 0.4, [(7.0, 9.5),(12.0,14.0)],  46),

    # â”€â”€ MIDDAY BUSH CANTEEN LUNCH WAVE (11:30-13:30, 12-min kitchen prep buffer)
    ("Shiashie Market Junction",      5.608, -0.166, 0.4, [(11.5, 13.5)],            68),  # corporate lunch
    ("East Legon Main Road Canteen",  5.637, -0.158, 0.4, [(11.5, 13.5)],            64),
    ("North Ridge Ministries Chop",   5.580, -0.195, 0.4, [(11.5, 13.5)],            62),
    ("Circle Chop Bar Cluster",       5.571, -0.222, 0.5, [(7.0,9.5),(11.5,13.5),(18.0,21.0)], 65),
    ("Makola Market Canteens",        5.550, -0.206, 0.4, [(7.0, 9.5),(11.5,13.5)],  66),
    ("Kaneshie Market Chop",          5.556, -0.244, 0.4, [(7.0, 9.5),(11.5,13.5)],  60),
    ("Tema Comm 5 Canteens",          5.673,  0.013, 0.4, [(7.0, 9.5),(11.5,13.5)],  46),
    ("Adabraka Canteen Row",          5.562, -0.212, 0.3, [(11.5, 13.5),(18.0,21.0)],42),
    ("Pig Farm Jct Chop",             5.580, -0.230, 0.3, [(11.5, 13.5)],             36),

    # â”€â”€ NIGHT-MARKET STREET FOOD WAVE (20:00-23:00, active 18:00-03:00)
    ("Osu Oxford St Night Market",    5.564, -0.178, 0.5, [(18.0, 23.0)],            75),  # peak 20-23
    ("G&G Special Waakye (Osu)",      5.568, -0.177, 0.2, [(18.0, 23.0)],            70),  # legendary
    ("Osu Blue Gate Night Stalls",    5.562, -0.175, 0.3, [(18.0, 23.0)],            68),
    ("Labadi Market Evening Chop",    5.555, -0.148, 0.3, [(11.5,13.5),(18.0,21.0)], 40),
    ("Teshie Chop Bars (Evening)",    5.583, -0.107, 0.4, [(18.0, 21.0)],            40),
    ("Bubuashie Evening Chop",        5.577, -0.249, 0.3, [(18.0, 21.0)],            38),
    ("Osu Canteens (Dinner Run)",     5.565, -0.178, 0.4, [(11.5,13.5),(18.0,21.0)], 46),
]

# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# MEGA-CHURCH & HIGH-DENSITY EVENT SPATIAL WAVES  (v4.0)
# Synchronized exit rushes from Accra's largest worship centres + stadium events.
#
# windows format:
#   {"days": [0-6], "h_start": float, "h_end": float, "multiplier": float,
#    "label": str, "crosses_midnight": bool}
#   crosses_midnight=True â†’ h_float >= h_start OR h_float < (h_end % 24)
#
# spintex_friction: True â†’ Action Chapel triggers Spintex road gridlock bonus
# independence events handled via date check in _megachurch_event_boost
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MEGACHURCH_EVENT_ZONES = [
    {
        "name": "Perez Chapel International â€” The Perez Dome, Dzorwulu",
        "lat": 5.602, "lng": -0.186,
        "radius_km": 1.2,
        "capacity": 14000,
        "windows": [
            # Sunday bimodal dismissal
            {"days": [6], "h_start": 8.25,  "h_end": 9.0,
             "multiplier": 5.0, "label": "1st Service End", "crosses_midnight": False},
            {"days": [6], "h_start": 11.25, "h_end": 12.5,
             "multiplier": 6.0, "label": "2nd Service End", "crosses_midnight": False},
            # Friday Night Vigil 22:00-01:00 (+400% = 5x)
            {"days": [4], "h_start": 22.0,  "h_end": 25.0,
             "multiplier": 5.0, "label": "Friday Night Vigil", "crosses_midnight": True},
            # Saturday early morning vigil overflow (covers 00:00-01:00)
            {"days": [5], "h_start": 0.0,   "h_end": 1.0,
             "multiplier": 4.0, "label": "Vigil Overflow Saturday", "crosses_midnight": False},
        ],
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
    {
        "name": "Action Chapel International â€” Impact Arena, Spintex Road",
        "lat": 5.627, "lng": -0.103,
        "radius_km": 1.5,
        "capacity": 30000,
        "windows": [
            # Sunday bimodal dismissal
            {"days": [6], "h_start": 8.5,  "h_end": 9.5,
             "multiplier": 7.0, "label": "Sunday 1st Dismissal", "crosses_midnight": False},
            {"days": [6], "h_start": 10.5, "h_end": 11.5,
             "multiplier": 7.0, "label": "Sunday 2nd Dismissal", "crosses_midnight": False},
            # Friday Prayer Encounter 19:30-21:30
            {"days": [4], "h_start": 19.5, "h_end": 21.5,
             "multiplier": 4.0, "label": "Friday Prayer Encounter", "crosses_midnight": False},
        ],
        "spintex_friction": True,          # Spintex road gridlock during all windows
        "spintex_friction_penalty": 0.70,  # 70% speed degradation on Spintex during events
    },
    {
        "name": "ICGC Christ Temple â€” Abossey Okai Linked Campus",
        "lat": 5.556, "lng": -0.227,
        "radius_km": 0.8,
        "capacity": 8000,
        "windows": [
            # Sunday primary dismissal
            {"days": [6], "h_start": 9.25, "h_end": 10.5,
             "multiplier": 4.5, "label": "Sunday Dismissal", "crosses_midnight": False},
            # Thursday midweek corporate prayer spike
            {"days": [3], "h_start": 12.0, "h_end": 13.5,
             "multiplier": 2.0, "label": "Thursday Midweek Prayer", "crosses_midnight": False},
        ],
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
    {
        "name": "Black Star Square & Accra Sports Stadium",
        "lat": 5.548, "lng": -0.196,
        "radius_km": 1.0,
        "capacity": 40000,
        "windows": [
            # Weekend concert closing slots â€” +500-800% â†’ multiplier 7-9x
            {"days": [5, 6], "h_start": 21.0, "h_end": 23.0,
             "multiplier": 9.0, "label": "Weekend Concert Exit Surge", "crosses_midnight": False},
        ],
        # Independence Day calendar events handled separately in _megachurch_event_boost
        "independence_parade": {
            "month": 3, "day": 6,
            "windows": [(10.0, 13.0)],
            "multiplier": 9.0,    # +500-800% â†’ 9x for 30,000+ synchronized exit
            "label": "Independence Parade Exit",
        },
        "independence_run": {
            "month": 3, "day": 7,
            "windows": [(6.5, 10.0)],
            "multiplier": 8.0,
            "label": "Independence Day Run Dispersal",
        },
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 2 â€” DATA STRUCTURES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@dataclass
class GridCell:
    grid_lat: float
    grid_lng: float
    places: list = field(default_factory=list)
    base_weight: float = 0.0
    demand_score: float = 0.0
    surge_probability: float = 0.0
    checkout_eta_min: Optional[float] = None
    prep_buffer_min: float = 0.0
    is_hotspot: bool = False
    demand_velocity: float = 0.0    # rate of score increase (acceleration signal)

    @property
    def centroid(self):
        return (self.grid_lat + 0.0005, self.grid_lng + 0.0005)

    def __repr__(self):
        return (f"GridCell({self.grid_lat},{self.grid_lng} | "
                f"score={self.demand_score:.1f} | surge={self.surge_probability:.2f})")


@dataclass
class RiderTelemetry:
    lat: float
    lng: float
    speed_kmh: float
    heading_deg: float
    has_active_delivery: bool = False
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    fuel_level_pct: float = 100.0


@dataclass
class DriftVector:
    target_lat: float
    target_lng: float
    bearing_deg: float
    distance_km: float
    tta_min: float
    expected_yield_ghs: float
    confidence: float
    action: str      # "MOVE" | "HOLD" | "LEAPFROG" | "ARBITRAGE" | "WAYBILL"
    reason: str


@dataclass
class HotSpot:
    lat: float
    lng: float
    radius_km: float
    demand_score: float
    surge_probability: float
    checkout_eta_min: float
    category_mix: dict
    label: str
    acceleration_band: str   # "EMERGING" | "PEAKING" | "DECLINING"
    opportunity_score: float = 0.0  # v4.4 â€” single 0-100 combining demand+confidence+distance, for the rider-facing headline number


@dataclass
class BoosterOutput:
    timestamp: str
    rider: dict
    hold_recommended: bool
    hold_reason: str
    move_degraded: bool                     # v4.2 â€” True = moving on a below-threshold "long shot" zone, not a confident recommendation
    nearby_pick: Optional[dict]              # v4.3 â€” closest decent zone, alternative to the best-overall pick
    hotspots: list
    primary_vector: Optional[dict]
    leapfrog_vector: Optional[dict]
    arbitrage_alert: Optional[dict]
    waybill_alert: Optional[dict]
    weather_advisory: Optional[dict]
    corporate_arbitrage: Optional[dict]     # v4.0 â€” corporate landing zone routing
    grid_stats: dict
    next_poll_interval_seconds: int


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 3 â€” SPATIAL UTILITIES
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bearing_deg(lat1, lng1, lat2, lng2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlng = math.radians(lng2 - lng1)
    x = math.sin(dlng) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlng)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat, lng, bearing_deg_val, distance_km):
    R = EARTH_RADIUS_KM
    d = distance_km / R
    b = math.radians(bearing_deg_val)
    phi1 = math.radians(lat)
    lam1 = math.radians(lng)
    phi2 = math.asin(math.sin(phi1) * math.cos(d) + math.cos(phi1) * math.sin(d) * math.cos(b))
    lam2 = lam1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(phi1),
                              math.cos(d) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), math.degrees(lam2)


def grid_key(lat, lng) -> tuple:
    return (round(lat, GRID_RESOLUTION), round(lng, GRID_RESOLUTION))


def compass_label(deg) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]


def _hm_to_float(h: int, m: int) -> float:
    """Convert hour+minute to decimal float (e.g. 6h30m â†’ 6.5)."""
    return h + m / 60.0


def _offset_time(hour: int, minute: int, offset_mins: int) -> tuple:
    """Advance wall-clock time by offset_mins, wrapping at midnight.
    Returns (new_hour, new_minute). Used by predictive front-runner."""
    total = hour * 60 + minute + offset_mins
    return (total // 60) % 24, total % 60


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 4 â€” GRID ENGINE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class GridEngine:
    def __init__(self, places_path: str = "places.json"):
        self.cells: dict[tuple, GridCell] = {}
        self._load(places_path)

    def _load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            places = json.load(f)
        for p in places:
            lat, lng = p["lat"], p["lng"]
            key = grid_key(lat, lng)
            if key not in self.cells:
                self.cells[key] = GridCell(grid_lat=key[0], grid_lng=key[1])
            cell = self.cells[key]
            cell.places.append(p)
            cell.base_weight += CATEGORY_DEMAND_WEIGHT.get(p.get("cat", "other"), 1)
        if self.cells:
            max_w = max(c.base_weight for c in self.cells.values()) or 1
            for c in self.cells.values():
                c.base_weight = (c.base_weight / max_w) * 100
        print(f"  [GridEngine] Indexed {len(places):,} places â†’ {len(self.cells):,} grid cells")

    def get_cell(self, lat, lng) -> Optional[GridCell]:
        return self.cells.get(grid_key(lat, lng))

    def nearby_cells(self, lat, lng, radius_km: float) -> list:
        results = []
        dlat = radius_km / 111.0
        dlng = radius_km / (111.0 * math.cos(math.radians(lat)))
        for (glat, glng), cell in self.cells.items():
            if abs(glat - lat) <= dlat and abs(glng - lng) <= dlng:
                if haversine_km(lat, lng, glat, glng) <= radius_km:
                    results.append(cell)
        return results


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 5 â€” TRAFFIC FRICTION ENGINE  (4-layer model, v3.0)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class TrafficFriction:
    """
    Four-layer speed multiplier:
      Layer 1 â€” Bottleneck congestion (proximity + time-of-day)
      Layer 2 â€” Road surface quality (bikes always feel this)
      Layer 3 â€” Corridor constraints (ACCRA_TRAFFIC_CONSTRAINTS, minute-aware)
      Layer 4 â€” Pedestrian congestion zones (time-windowed density penalty)
    """

    def __init__(self):
        self.bottlenecks = BOTTLENECKS
        self.road_quality_zones = ROAD_QUALITY_ZONES
        self.corridors = ACCRA_TRAFFIC_CONSTRAINTS
        self.ped_zones = PEDESTRIAN_CONGESTION_ZONES

    # â”€â”€ helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @staticmethod
    def _in_peak_window(h_float: float, peak_hours: list) -> bool:
        """peak_hours: list of (h_start, m_start, h_end, m_end)."""
        for h0, m0, h1, m1 in peak_hours:
            start = h0 + m0 / 60.0
            end   = h1 + m1 / 60.0
            if start <= h_float < end:
                return True
        return False

    # â”€â”€ Layer 1: bottleneck congestion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _bottleneck_penalty(self, lat: float, lng: float, hour: int) -> float:
        penalty = 0.0
        for name, blat, blng, h_start, h_end, severity in self.bottlenecks:
            dist = haversine_km(lat, lng, blat, blng)
            if dist > 3.0:
                continue
            proximity_factor = max(0.0, 1.0 - (dist / 3.0))
            in_peak = h_start <= hour < h_end
            time_factor = 1.0 if in_peak else 0.25
            impact = severity * proximity_factor * time_factor
            penalty = max(penalty, impact)
        return penalty

    # â”€â”€ Layer 2: road surface quality â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def road_surface_penalty(self, lat: float, lng: float) -> float:
        penalty = 0.0
        for name, rlat, rlng, radius_km, sp in self.road_quality_zones:
            dist = haversine_km(lat, lng, rlat, rlng)
            if dist > radius_km:
                continue
            proximity = max(0.0, 1.0 - (dist / radius_km))
            penalty = max(penalty, sp * proximity)
        return penalty

    def road_quality_label(self, lat: float, lng: float) -> str:
        worst_name, worst_penalty = None, 0.0
        for name, rlat, rlng, radius_km, sp in self.road_quality_zones:
            dist = haversine_km(lat, lng, rlat, rlng)
            if dist <= radius_km and sp > worst_penalty:
                worst_name, worst_penalty = name, sp
        if worst_penalty >= 0.40:
            return f"ROUGH â€” {worst_name} (potholed/unpaved, -{worst_penalty*100:.0f}% speed)"
        if worst_penalty >= 0.20:
            return f"DEGRADED â€” {worst_name} (-{worst_penalty*100:.0f}% speed)"
        return "GOOD"

    # â”€â”€ Layer 3: corridor constraints â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _corridor_penalty(self, lat: float, lng: float,
                          hour: int, minute: int) -> float:
        h_float = _hm_to_float(hour, minute)
        penalty = 0.0
        for corridor_key, cfg in self.corridors.items():
            dist = haversine_km(lat, lng, cfg["lat"], cfg["lng"])
            if dist > cfg["radius_km"]:
                continue
            if not self._in_peak_window(h_float, cfg["peak_hours"]):
                continue
            proximity = max(0.0, 1.0 - (dist / cfg["radius_km"]))
            deg = cfg["speed_degradation"]
            # Tetteh Quarshie special: bump to 75% if disruption_flag active
            if cfg.get("disruption_flag") and corridor_key == "tetteh_quarshie":
                deg = cfg.get("accra_madina_degradation", deg)
            impact = deg * proximity
            penalty = max(penalty, impact)
        return penalty

    # â”€â”€ Layer 4: pedestrian congestion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def _pedestrian_penalty(self, lat: float, lng: float,
                            hour: int, minute: int) -> float:
        h_float = _hm_to_float(hour, minute)
        penalty = 0.0
        for name, plat, plng, radius_km, h_start, h_end, ped_pen in self.ped_zones:
            if not (h_start <= h_float < h_end):
                continue
            dist = haversine_km(lat, lng, plat, plng)
            if dist > radius_km:
                continue
            proximity = max(0.0, 1.0 - (dist / radius_km))
            penalty = max(penalty, ped_pen * proximity)
        return penalty

    # â”€â”€ Event friction info (Layer 5 â€” mega-church Spintex gridlock) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def event_friction_info(self, lat: float, lng: float,
                            hour: int, minute: int, weekday: int) -> Optional[dict]:
        """
        Returns event friction data if an active mega-church/stadium event is
        generating extra gridlock near the rider's position. Does NOT modify
        speed_multiplier (avoids signature changes); instead feeds into
        primary_vector reason string and grid_stats.
        """
        h_float = _hm_to_float(hour, minute)
        for zone in MEGACHURCH_EVENT_ZONES:
            if not zone.get("spintex_friction"):
                continue
            penalty = zone.get("spintex_friction_penalty", 0.0)
            for win in zone.get("windows", []):
                if weekday not in win["days"]:
                    continue
                if win.get("crosses_midnight"):
                    h_end_norm = win["h_end"] % 24
                    in_win = h_float >= win["h_start"] or h_float < h_end_norm
                else:
                    in_win = win["h_start"] <= h_float < win["h_end"]
                if not in_win:
                    continue
                r = zone["radius_km"] + 2.0
                dist = haversine_km(lat, lng, zone["lat"], zone["lng"])
                if dist > r:
                    continue
                return {
                    "zone": zone["name"],
                    "event": win["label"],
                    "penalty": penalty,
                    "dist_km": round(dist, 2),
                }
        return None

    def corporate_time_penalty_min(self, lat: float, lng: float,
                                   hour: int, weekday: int) -> float:
        """
        Returns total non-riding overhead (gate + walk + lift) in minutes if
        the rider is within a corporate landing zone during its peak window.
        Returns 0.0 otherwise (no penalty outside zone / outside peak hours).
        """
        h_float = float(hour)
        for zone in CORPORATE_LANDING_ZONES:
            if zone.get("sunday_closed") and weekday == 6:
                continue
            dist = haversine_km(lat, lng, zone["lat"], zone["lng"])
            if dist > zone["radius_km"]:
                continue
            in_peak = any(w[0] <= h_float < w[1] for w in zone["peak_windows"])
            if not in_peak:
                continue
            walk_min = zone["walk_distance_m"] / 80.0
            return zone["gate_screening_min"] + walk_min + zone["elevator_wait_min"]
        return 0.0

    # â”€â”€ Combined multiplier â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    def speed_multiplier(self, lat: float, lng: float,
                         hour: int, minute: int = 0) -> float:
        """
        Returns multiplier 0.10â€“1.0.
        1.0 = free flow, 0.10 = severe gridlock + road + pedestrian congestion.
        """
        # Start from arterial baseline considering peak hours
        h_float = _hm_to_float(hour, minute)
        is_arterial_peak = (7.5 <= h_float < 9.0) or (16.5 <= h_float < 18.0)
        base = 1.0 - (ARTERIAL_PEAK_DEGRADATION * ARTERIAL_PEAK_COVERAGE
                      if is_arterial_peak else 0.0)

        penalty = (
            self._bottleneck_penalty(lat, lng, hour) +
            self.road_surface_penalty(lat, lng) +
            self._corridor_penalty(lat, lng, hour, minute) +
            self._pedestrian_penalty(lat, lng, hour, minute)
        )
        return max(0.10, base - penalty)

    def effective_speed(self, rider: RiderTelemetry, hour: int,
                        minute: int = 0) -> float:
        base = max(rider.speed_kmh, 15.0)
        return base * self.speed_multiplier(rider.lat, rider.lng, hour, minute)


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 6 â€” DEMAND SIMULATOR  (pre-checkout flash trigger, v3.0)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class DemandSimulator:
    """
    Demand signal sources:
      1. Time-of-day base curve (updated for Accra reality)
      2. Shadow Matrix: 27 offline/WhatsApp food zones
      3. B2B Wholesale injection (day-of-week aware: Makola/Kantamanto/Abossey Okai)
      4. Platform API cart-spike injection (simulate_hotspots)
      5. AMA Clamp Risk Modifier (narrow alley de-boost on vehicle-hostile zones)
    """

    # Updated time-of-day demand curve (Accra ground truth)
    HOUR_CURVE = {
        0: 0.2,  1: 0.1,  2: 0.1,  3: 0.1,  4: 0.2,  5: 0.3,
        6: 0.5,  7: 0.8,  8: 1.0,  9: 0.9, 10: 0.7, 11: 1.1,
        12: 1.5, 13: 1.6, 14: 1.1, 15: 0.9, 16: 1.0, 17: 1.3,
        18: 1.7, 19: 1.8, 20: 1.5, 21: 1.2, 22: 0.8, 23: 0.5,
    }

    def __init__(self, grid: GridEngine, seed: int = None):
        self.grid = grid
        self.shadow_matrix = SHADOW_MATRIX
        self.b2b_zones = B2B_WHOLESALE_ZONES
        self.megachurch_zones = MEGACHURCH_EVENT_ZONES
        if seed is not None:
            random.seed(seed)

    def _time_multiplier(self, hour: int) -> float:
        return self.HOUR_CURVE.get(hour, 0.3)

    def _prep_buffer(self, cell: GridCell) -> float:
        cats = {p.get("cat", "other") for p in cell.places}
        max_buf = 0.0
        for cat in cats:
            if cat in INSTANT_CATEGORIES:
                continue
            if cat == "food":
                lo, hi = FUFU_LIGHTSOUP_BUFFER
            else:
                lo, hi = KITCHEN_PREP_BUFFER.get(cat, (2, 4))
            max_buf = max(max_buf, random.uniform(lo, hi))
        return max_buf

    def _shadow_boost(self, hour: int, minute: int = 0) -> list:
        h_float = _hm_to_float(hour, minute)
        spikes = []
        for name, slat, slng, radius_km, windows, intensity in self.shadow_matrix:
            for w_start, w_end in windows:
                if w_start <= h_float < w_end:
                    jitter = random.uniform(0.88, 1.12)
                    spikes.append((slat, slng, intensity * jitter, radius_km, name))
                    break
        return spikes

    def _b2b_boost(self, hour: int, minute: int, weekday: int) -> list:
        """
        Inject B2B wholesale demand for Makola, Kantamanto, and Abossey Okai.
        Respects day-of-week weights and primary/secondary dispatch windows.
        """
        h_float = _hm_to_float(hour, minute)
        spikes = []
        for zone in self.b2b_zones:
            day_w = zone["day_weights"].get(weekday, 0.5)
            if day_w < 0.3:
                continue  # closed or negligible
            p0, p1 = zone["primary_window"]
            s0, s1 = zone["secondary_window"]
            in_window = (p0 <= h_float < p1) or (s0 <= h_float < s1)
            if not in_window:
                continue
            intensity = zone["base_intensity"] * day_w
            jitter = random.uniform(0.90, 1.10)
            spikes.append((
                zone["lat"], zone["lng"],
                intensity * jitter,
                zone["radius_km"],
                zone["name"],
                zone.get("ama_clamp_risk", False),
            ))
        return spikes

    def _megachurch_event_boost(self, hour: int, minute: int,
                                weekday: int) -> list:
        """
        Inject synchronized demand spikes from mega-church dismissals and
        large-scale stadium events. Returns list of
        (lat, lng, intensity, radius_km, name, spintex_friction, friction_penalty).

        Handles windows that cross midnight (e.g., Friday Night Vigil 22:00-01:00).
        Also checks live calendar date for Independence Day events (March 6-7).
        """
        h_float = _hm_to_float(hour, minute)
        today = datetime.datetime.now()
        month, day = today.month, today.day
        spikes = []

        for zone in self.megachurch_zones:
            fired = False

            # â”€â”€ Regular time windows (dismissals, vigils, prayer nights)
            for win in zone.get("windows", []):
                if weekday not in win["days"]:
                    continue
                if win.get("crosses_midnight"):
                    # Window spans midnight, e.g. 22:00-01:00
                    h_end_norm = win["h_end"] % 24
                    in_win = h_float >= win["h_start"] or h_float < h_end_norm
                else:
                    in_win = win["h_start"] <= h_float < win["h_end"]
                if not in_win:
                    continue

                capacity = zone.get("capacity", 5000)
                intensity = min(100, (capacity / 200.0) * win["multiplier"])
                jitter = random.uniform(0.90, 1.10)
                spikes.append((
                    zone["lat"], zone["lng"],
                    intensity * jitter,
                    zone["radius_km"],
                    f"{zone['name']} â€” {win['label']}",
                    zone.get("spintex_friction", False),
                    zone.get("spintex_friction_penalty", 0.0),
                ))
                fired = True
                break   # Only fire once per zone per call

            # â”€â”€ Calendar-specific events (Independence Day parade + run)
            if not fired:
                for ev_key in ("independence_parade", "independence_run"):
                    ev = zone.get(ev_key)
                    if not ev:
                        continue
                    if ev["month"] != month or ev["day"] != day:
                        continue
                    for w0, w1 in ev["windows"]:
                        if w0 <= h_float < w1:
                            capacity = zone.get("capacity", 5000)
                            intensity = min(100, (capacity / 200.0) * ev["multiplier"])
                            spikes.append((
                                zone["lat"], zone["lng"],
                                intensity * random.uniform(0.95, 1.05),
                                zone.get("radius_km", 1.0),
                                f"{zone['name']} â€” {ev['label']}",
                                False, 0.0,
                            ))
                            break

        return spikes

    def inject_signals(self, hour: int, minute: int = 0,
                       simulate_hotspots=None, weekday: int = 0):
        time_mult = self._time_multiplier(hour)

        # â”€â”€ Base scoring
        for cell in self.grid.cells.values():
            noise = random.uniform(0.7, 1.3)
            cell.demand_score = cell.base_weight * time_mult * noise
            cell.prep_buffer_min = self._prep_buffer(cell)
            cell.surge_probability = min(1.0, cell.demand_score / 100.0)
            cell.is_hotspot = False
            cell.checkout_eta_min = None
            cell.demand_velocity = 0.0

        # â”€â”€ Shadow Matrix (offline/WhatsApp/phone-in food demand)
        for slat, slng, intensity, radius_km, sname in self._shadow_boost(hour, minute):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.5)

        # â”€â”€ B2B Wholesale injection (day-of-week aware)
        for slat, slng, intensity, radius_km, sname, ama_clamp in \
                self._b2b_boost(hour, minute, weekday):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                # AMA Clamp: narrow alleys penalise bulk vehicle pickups by 40%
                if ama_clamp:
                    boost *= 0.60
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.6)

        # â”€â”€ Mega-church & stadium event spatial waves (v4.0)
        for slat, slng, intensity, radius_km, sname, _evt_fric, _fric_pen in \
                self._megachurch_event_boost(hour, minute, weekday):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                # Synchronized exits are high-velocity spikes: velocity bonus 0.9x
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.9)

        # â”€â”€ Platform API / cart spike injection (Bolt/Yango pre-checkout)
        if simulate_hotspots:
            for slat, slng, intensity in simulate_hotspots:
                for cell in self.grid.nearby_cells(slat, slng, 0.5):
                    dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                    boost = intensity * max(0.0, 1.0 - dist / 0.5)
                    cell.demand_score = min(100, cell.demand_score + boost)
                    cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                    cell.demand_velocity = max(cell.demand_velocity, boost * 0.8)

        # â”€â”€ Mark hotspots (top 5%) and assign checkout ETAs
        scores = sorted(c.demand_score for c in self.grid.cells.values())
        if scores:
            threshold = scores[int(len(scores) * 0.95)]
            for cell in self.grid.cells.values():
                if cell.demand_score >= threshold:
                    cell.is_hotspot = True
                    cell.checkout_eta_min = cell.prep_buffer_min + random.uniform(2, 5)

    def active_shadow_windows(self, hour: int, minute: int = 0) -> list:
        h_float = _hm_to_float(hour, minute)
        active = []
        for name, *_, windows, intensity in self.shadow_matrix:
            for w_start, w_end in windows:
                if w_start <= h_float < w_end:
                    active.append(name)
                    break
        return active


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 7 â€” VELOCITY WAVE ENGINE  (FRONT-RUNNING OVERRIDE, v3.0)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class VelocityWaveEngine:
    """
    PURE PREDICTION â€” NOT REACTION.

    Ghost Penalty: zones already at demand_score â‰¥ 85 are PENALISED by 75%.
      Rationale: mainstream platforms already display these as "surge" â€” they
      are crowded ghost targets. Entering them gives zero competitive edge.

    Acceleration Multiplier: zones in the 40-75 "emerging" band receive a
      1.5-2.0x bonus because the transaction explosion is imminent and no
      competitor has seen it yet.

    TTA Lock: the engine targets cells where the rider's time-to-arrival
      equals checkout_eta_min exactly â€” parked at the merchant's door the
      millisecond the customer presses "Order".
    """

    GHOST_SCORE_THRESHOLD = 85.0   # already peaked â†’ ghost penalty applies
    GHOST_MULTIPLIER      = 0.25   # 75% score cut for ghost zones
    EMERGING_BAND_LOW     = 40.0   # minimum score for "emerging" classification
    EMERGING_BAND_HIGH    = 78.0   # ceiling â€” above this slides into ghost territory
    ACCEL_BONUS_MAX       = 2.0    # max acceleration multiplier at band centre
    ACCEL_BONUS_MIN       = 1.5    # multiplier at band entry (score=40)
    TTA_PRE_POSITION_WIN  = 3.0    # ideal: arrive 0-3 min before checkout_eta

    def __init__(self, friction: TrafficFriction):
        self.friction = friction

    def compute_tta(self, rider: RiderTelemetry, target_lat: float,
                    target_lng: float, hour: int, minute: int = 0) -> float:
        dist_km = haversine_km(rider.lat, rider.lng, target_lat, target_lng)
        eff_speed = self.friction.effective_speed(rider, hour, minute)
        return (dist_km / eff_speed) * 60.0 if eff_speed > 0 else 9999.0

    def _acceleration_band(self, score: float, velocity: float = 0.0) -> tuple:
        """
        v4.0 â€” Velocity Trend Validation Loop.

        Ghost Penalty (Fading Surge):
          score >= 85 AND velocity < STABLE_THRESHOLD â†’ 75% haircut.
          Zone is dying â€” mainstream platforms are already swarming it.
          Entering gives ZERO competitive edge; rider is ghost-chasing.

        Sustained Cash Cow Guard:
          score >= 85 AND velocity >= STABLE_THRESHOLD â†’ NO haircut.
          Deep market rush / downpour still actively driving transactions.
          Zone is printing money â€” rider should STAY or re-enter.

        Emerging Band (40-78):
          Pre-checkout explosion imminent. 1.5-2.0x multiplier locks rider
          onto the zone 3-5 minutes before competitors see the demand spike.
        """
        if score >= self.GHOST_SCORE_THRESHOLD:
            if velocity >= VELOCITY_TREND_STABLE_THRESHOLD:
                # Cash Cow Guard â€” velocity is stable/rising: suppress haircut
                return 1.0, "SUSTAINED_CASH_COW"
            # Fading Ghost â€” velocity is dropping: enforce 75% haircut
            return self.GHOST_MULTIPLIER, "GHOST (already peaked â€” mainstream sees it)"
        if score >= self.EMERGING_BAND_HIGH:
            # Upper transition â€” still building, moderate acceleration bonus
            fade = (score - self.EMERGING_BAND_HIGH) / (self.GHOST_SCORE_THRESHOLD - self.EMERGING_BAND_HIGH)
            mult = self.ACCEL_BONUS_MAX * (1.0 - fade * 0.5)
            return mult, "PEAKING"
        if score >= self.EMERGING_BAND_LOW:
            # Sweet spot: emerging pre-checkout grid
            t = (score - self.EMERGING_BAND_LOW) / (self.EMERGING_BAND_HIGH - self.EMERGING_BAND_LOW)
            mult = self.ACCEL_BONUS_MIN + t * (self.ACCEL_BONUS_MAX - self.ACCEL_BONUS_MIN)
            return mult, "EMERGING"
        # Too quiet
        return 0.70, "QUIET"

    def intercept_score(self, rider: RiderTelemetry, cell: GridCell,
                        hour: int, minute: int = 0) -> float:
        """
        Front-running composite score.

        TTA timing: ideal = arrive at checkout_eta_min (delta=0).
          â€¢ Arriving 0-3 min BEFORE peak  â†’ full score + 10% pre-position bonus
          â€¢ Arriving 0-5 min AFTER peak   â†’ decay (exp curve)
          â€¢ Arriving more than 5 min late â†’ heavy decay (zone is dead)

        Ghost penalty  â†’ zones already at peak get 75% score haircut.
        Acceleration   â†’ emerging zones get 1.5-2.0x multiplier.
        Velocity bonus â†’ cells with high demand_velocity (rising fast) get +20%.
        """
        if cell.checkout_eta_min is None:
            return 0.0

        tta = self.compute_tta(rider, cell.grid_lat, cell.grid_lng, hour, minute)
        delta = tta - cell.checkout_eta_min  # negative = early (good), positive = late

        # TTA timing score
        if delta <= 0 and delta >= -self.TTA_PRE_POSITION_WIN:
            # Perfect: arrive 0-3 min before checkout fires â†’ maximum intercept
            timing_score = 1.10 + 0.033 * abs(delta)   # slight bonus for being early
        elif delta < -self.TTA_PRE_POSITION_WIN:
            # Too early â€” surge hasn't built yet
            timing_score = math.exp(-0.06 * (abs(delta) - self.TTA_PRE_POSITION_WIN))
        elif 0 < delta <= 5:
            # Slightly late â€” still catchable but losing edge
            timing_score = math.exp(-0.18 * delta)
        else:
            # More than 5 min late â€” zone is stale, mainstream already swarmed
            timing_score = math.exp(-0.40 * (delta - 5))

        # Ghost penalty / acceleration multiplier (velocity-aware v4.0)
        accel_mult, _ = self._acceleration_band(cell.demand_score, cell.demand_velocity)

        # Velocity (rate-of-rise) bonus: fast-rising tiles get +20%
        velocity_bonus = 1.0 + min(0.20, cell.demand_velocity / 500.0)

        return (cell.demand_score * cell.surge_probability *
                timing_score * accel_mult * velocity_bonus)

    def acceleration_band_label(self, score: float, velocity: float = 0.0) -> str:
        _, label = self._acceleration_band(score, velocity)
        return label

    def rank_cells(self, rider: RiderTelemetry, cells: list,
                   hour: int, minute: int = 0, top_n: int = 5) -> list:
        scored = []
        for cell in cells:
            s = self.intercept_score(rider, cell, hour, minute)
            if s > 0:
                scored.append((s, cell))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_n]


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 8 â€” LEAPFROG SEQUENTIAL ROUTER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class LeapfrogRouter:
    def __init__(self, grid: GridEngine, wave: VelocityWaveEngine,
                 friction: TrafficFriction):
        self.grid = grid
        self.wave = wave
        self.friction = friction

    def next_zone(self, rider: RiderTelemetry, hour: int,
                  minute: int = 0, search_radius_km: float = 2.0) -> Optional[DriftVector]:
        if not rider.has_active_delivery or rider.dropoff_lat is None:
            return None
        nearby = self.grid.nearby_cells(rider.dropoff_lat, rider.dropoff_lng, search_radius_km)
        hotspots = [c for c in nearby if c.is_hotspot]
        if not hotspots:
            return None
        ranked = self.wave.rank_cells(rider, hotspots, hour, minute, top_n=1)
        if not ranked:
            return None
        score, best = ranked[0]
        dist = haversine_km(rider.dropoff_lat, rider.dropoff_lng,
                            best.grid_lat, best.grid_lng)
        bear = bearing_deg(rider.dropoff_lat, rider.dropoff_lng,
                           best.grid_lat, best.grid_lng)
        tta = self.wave.compute_tta(rider, best.grid_lat, best.grid_lng, hour, minute)
        expected = score * 0.08
        return DriftVector(
            target_lat=best.grid_lat,
            target_lng=best.grid_lng,
            bearing_deg=bear,
            distance_km=round(dist, 2),
            tta_min=round(tta, 1),
            expected_yield_ghs=round(expected, 2),
            confidence=round(min(0.95, score / 100.0), 2),
            action="LEAPFROG",
            reason=(f"Pre-cached next pickup zone {dist:.1f}km from your drop-off. "
                    f"ETA after delivery: {tta:.0f}min. Surge in ~{best.checkout_eta_min:.0f}min. "
                    f"Zone: {self.wave.acceleration_band_label(best.demand_score)}."),
        )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 9 â€” RETURN TICKET ARBITRAGE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class ReturnTicketArbitrage:
    def __init__(self, grid: GridEngine, wave: VelocityWaveEngine):
        self.grid = grid
        self.wave = wave

    def check(self, rider: RiderTelemetry, hour: int) -> Optional[dict]:
        if not rider.has_active_delivery or rider.dropoff_lat is None:
            return None
        for zone_name, zlat, zlng, radius_km in LOW_DENSITY_ZONES:
            dist_to_zone = haversine_km(rider.dropoff_lat, rider.dropoff_lng, zlat, zlng)
            if dist_to_zone > radius_km:
                continue
            nearby = self.grid.nearby_cells(zlat, zlng, radius_km)
            commercial = [c for c in nearby
                          if any(p.get("cat") in ("market", "mall", "office", "transport")
                                 for p in c.places)]
            if not commercial:
                continue
            best = max(commercial, key=lambda c: c.base_weight)
            return {
                "zone": zone_name,
                "alert": "RETURN_TICKET_ARBITRAGE",
                "message": (f"Drop-off is in {zone_name} â€” low-density outskirt. "
                            f"Pre-lock B2B/wholesale return run from "
                            f"{best.grid_lat:.4f},{best.grid_lng:.4f} "
                            f"(base demand weight {best.base_weight:.0f})."),
                "pickup_lat": best.grid_lat,
                "pickup_lng": best.grid_lng,
                "minutes_to_lock": 30,
            }
        return None


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 9.5 â€” CORPORATE ARBITRAGE ROUTER  (v4.0)
# Intercepts corporate landing zone exits and pre-populates outbound routing
# vectors. Two activation windows:
#   Mid-Morning Legal & Consular Push  10:00-11:30
#   Pre-COB Crunch                     15:30-17:00  (Ministries cut off 16:30)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class CorporateArbitrageRouter:
    """
    When a rider is within range of a corporate landing zone during either the
    Legal Push or Pre-COB Crunch windows, this router:
      1. Identifies the nearest zone and bakes in all non-riding overhead
         (gate screening + walk + lift) as a net-yield penalty.
      2. Selects the correct outbound flow (A/B/C) and centralized pickup node.
      3. Returns an actionable vector with destination, bearing, and access notes.
    """

    LEGAL_PUSH_WINDOW    = (10.0, 11.5)   # 10:00-11:30
    PRE_COB_WINDOW       = (15.5, 17.0)   # 15:30-17:00
    MINISTRIES_CUTOFF    = 16.5           # 16:30 â€” Ministries hard close
    ACTIVATION_RADIUS_KM = 1.5            # rider must be within this of the zone

    def check(self, rider: RiderTelemetry, hour: int, minute: int,
              weekday: int = 0) -> Optional[dict]:
        h_float = _hm_to_float(hour, minute)
        in_legal = self.LEGAL_PUSH_WINDOW[0] <= h_float < self.LEGAL_PUSH_WINDOW[1]
        in_cob   = self.PRE_COB_WINDOW[0]    <= h_float < self.PRE_COB_WINDOW[1]

        if not (in_legal or in_cob):
            return None

        best_zone = None
        best_dist = 999.0

        for zone in CORPORATE_LANDING_ZONES:
            # Sunday access denial
            if zone.get("sunday_closed") and weekday == 6:
                continue
            # Saturday reduced capacity
            sat_cap = zone.get("saturday_capacity", 1.0)
            if weekday == 5 and sat_cap <= 0:
                continue
            # Ministries cuts off at 16:30 in pre-COB window
            if in_cob and "Ministries" in zone["name"] and h_float >= self.MINISTRIES_CUTOFF:
                continue

            dist = haversine_km(rider.lat, rider.lng, zone["lat"], zone["lng"])
            if dist > self.ACTIVATION_RADIUS_KM + zone["radius_km"]:
                continue
            if dist < best_dist:
                best_dist = dist
                best_zone = zone

        if best_zone is None:
            return None

        # Determine outbound flow
        if in_legal:
            flow_key = "A"     # Legal push always routes to courts
        elif "Airport City" in best_zone["name"]:
            flow_key = "B"     # Airport City â†’ KIA / customs
        elif "Ministries" in best_zone["name"]:
            flow_key = "A"     # Ministries â†’ High Street courts
        else:
            flow_key = "C"     # Ridge / others â†’ upcountry sorting

        flow = CORPORATE_OUTBOUND_FLOWS[flow_key]

        # Nearest pickup node for this flow
        flow_nodes = [n for n in CORPORATE_PICKUP_NODES if n["flow"] == flow_key]
        nearest_node = min(
            flow_nodes,
            key=lambda n: haversine_km(rider.lat, rider.lng, n["lat"], n["lng"]),
            default=None,
        ) if flow_nodes else None

        node_lat = nearest_node["lat"] if nearest_node else best_zone["lat"]
        node_lng = nearest_node["lng"] if nearest_node else best_zone["lng"]
        bear_node = bearing_deg(rider.lat, rider.lng, node_lat, node_lng)
        dist_node = haversine_km(rider.lat, rider.lng, node_lat, node_lng)

        primary_dest = flow["destinations"][0]
        bear_dest = bearing_deg(node_lat, node_lng,
                                primary_dest["lat"], primary_dest["lng"])

        # Non-riding time penalty (gate + walk + lift)
        walk_min = best_zone["walk_distance_m"] / 80.0   # 80 m/min walking pace
        total_overhead_min = (best_zone["gate_screening_min"] +
                              walk_min +
                              best_zone["elevator_wait_min"])

        # Saturday reduced capacity note
        sat_note = ""
        if weekday == 5 and best_zone.get("saturday_capacity", 1.0) < 1.0:
            sat_note = f" âš  Saturday â€” {best_zone['saturday_capacity']*100:.0f}% capacity."

        # Ministries deadline warning
        cutoff_note = ""
        if in_cob and "Ministries" in best_zone["name"]:
            mins_left = (self.MINISTRIES_CUTOFF - h_float) * 60
            cutoff_note = f" âš  MINISTRIES CLOSES IN {mins_left:.0f}min â€” execute BEFORE 16:30."

        window_type = "MID_MORNING_LEGAL_PUSH" if in_legal else "PRE_COB_CRUNCH"

        return {
            "alert": "CORPORATE_ARBITRAGE",
            "window_type": window_type,
            "zone": best_zone["name"],
            "zone_lat": best_zone["lat"],
            "zone_lng": best_zone["lng"],
            "distance_km": round(best_dist, 2),
            "flow": flow_key,
            "flow_name": flow["name"],
            "pickup_node": nearest_node["name"] if nearest_node else best_zone["name"],
            "pickup_access": nearest_node["access"] if nearest_node else "main entrance",
            "pickup_lat": node_lat,
            "pickup_lng": node_lng,
            "bearing_to_pickup": round(bear_node, 1),
            "dist_to_pickup_km": round(dist_node, 2),
            "primary_destination": primary_dest["name"],
            "dest_lat": primary_dest["lat"],
            "dest_lng": primary_dest["lng"],
            "bearing_to_dest": round(bear_dest, 1),
            "non_riding_overhead_min": round(total_overhead_min, 1),
            "gate_screening_min": best_zone["gate_screening_min"],
            "walk_distance_m": best_zone["walk_distance_m"],
            "elevator_wait_min": best_zone["elevator_wait_min"],
            "saturday_capacity_pct": int(best_zone.get("saturday_capacity", 1.0) * 100),
            "message": (
                f"[{window_type.replace('_', ' ')}] {flow['name']} â†’ {primary_dest['name']}. "
                f"Pickup: {nearest_node['name'] if nearest_node else best_zone['name']}. "
                f"Access: {nearest_node['access'] if nearest_node else 'main entrance'}. "
                f"Non-riding overhead: {total_overhead_min:.0f}min "
                f"(gate {best_zone['gate_screening_min']}min + "
                f"walk {best_zone['walk_distance_m']}m + "
                f"lift {best_zone['elevator_wait_min']}min)."
                f"{sat_note}{cutoff_note}"
            ),
        }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 10 â€” WAYBILL PIPELINE INTERCEPTOR  (exact terminal schedules, v4.0)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class WaybillInterceptor:
    """
    Maps exact arrival patterns of inter-city buses to three Accra terminal
    clusters. Incorporates day-of-week demand multipliers, VIP first-come
    vs STC hourly schedules, and the Cape Coast 08:00 proxy.
    """

    MAX_INTERCEPT_RANGE_KM = 9.0
    ALERT_THRESHOLD_MIN    = 18    # trigger alert if bus arrives within N minutes

    def _is_in_window(self, h_float: float, windows: list) -> bool:
        for w0, w1 in windows:
            if w0 <= h_float < w1:
                return True
        return False

    def _is_peak_stacking(self, h_float: float, stacking: list) -> bool:
        for s0, s1 in stacking:
            if s0 <= h_float < s1:
                return True
        return False

    def _weekend_multiplier(self, h_float: float, terminal: dict,
                             weekday: int) -> float:
        if weekday in terminal.get("weekend_days", []):
            return terminal.get("weekend_multiplier", 1.0)
        return 1.0

    def _next_arrival(self, h_float: float, interval_min: int,
                      terminal: dict) -> int:
        """
        For STC_HOURLY terminals: next departure is on the hour.
        For FIRST_COME / MIXED: modulo interval.
        """
        if terminal.get("type") == "STC_HOURLY" and terminal.get("stc_mon_fri_hourly"):
            frac = h_float % 1.0
            return int((1.0 - frac) * 60)
        minute_within = int((h_float * 60) % interval_min)
        return interval_min - minute_within

    def check(self, rider: RiderTelemetry, hour: int, minute: int,
              weekday: int = 0) -> Optional[dict]:
        h_float = _hm_to_float(hour, minute)
        best_terminal = None
        best_dist = 999.0
        best_meta = {}

        for terminal in TERMINAL_SCHEDULES:
            if not self._is_in_window(h_float, terminal["windows"]):
                continue
            dist = haversine_km(rider.lat, rider.lng,
                                terminal["lat"], terminal["lng"])
            if dist > self.MAX_INTERCEPT_RANGE_KM:
                continue

            score = (1.0 / (dist + 0.01)) * self._weekend_multiplier(
                h_float, terminal, weekday)
            # Cape Coast proxy bonus at 08:00
            if terminal.get("cape_coast_proxy_hour") and \
               abs(h_float - terminal["cape_coast_proxy_hour"]) < 0.25:
                score *= 1.3

            if score > (1.0 / (best_dist + 0.01)):
                best_dist = dist
                best_terminal = terminal
                best_meta = {
                    "stacking": self._is_peak_stacking(
                        h_float, terminal.get("peak_stacking", [])),
                    "weekend_mult": self._weekend_multiplier(
                        h_float, terminal, weekday),
                    "next_arrival": self._next_arrival(
                        h_float, terminal["arrival_interval_min"], terminal),
                }

        if best_terminal is None:
            return None

        next_arrival = best_meta["next_arrival"]
        if next_arrival > self.ALERT_THRESHOLD_MIN:
            return None

        bear = bearing_deg(rider.lat, rider.lng,
                           best_terminal["lat"], best_terminal["lng"])
        stacking_note = " PEAK STACKING ACTIVE â€” multi-bus arrival cluster." \
            if best_meta["stacking"] else ""
        weekend_note = f" Weekend demand Ã—{best_meta['weekend_mult']:.1f}." \
            if best_meta["weekend_mult"] > 1.0 else ""

        return {
            "alert": "WAYBILL_INTERCEPT",
            "hub": best_terminal["name"],
            "hub_lat": best_terminal["lat"],
            "hub_lng": best_terminal["lng"],
            "distance_km": round(best_dist, 2),
            "bearing_deg": round(bear, 1),
            "next_arrival_min": next_arrival,
            "terminal_type": best_terminal["type"],
            "message": (f"{'Inter-city bus' if best_terminal['type']=='FIRST_COME' else 'STC departure'} "
                        f"at {best_terminal['name']} in ~{next_arrival}min. "
                        f"Hub is {best_dist:.1f}km {compass_label(bear)}. "
                        f"Position for wholesale multi-package waybill run.{stacking_note}{weekend_note}"),
        }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 11 â€” MONSOON MICRO-CLIMATE MULTIPLIER
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class MonsoonLayer:
    def __init__(self, grid: GridEngine):
        self.grid = grid

    def apply(self, rider: RiderTelemetry, rain_active_zones: list,
              hour: int) -> Optional[dict]:
        if not rain_active_zones:
            return None
        flooded_centres = [
            (zlat, zlng, zrad) for zname, zlat, zlng, zrad in RAIN_FLOOD_ZONES
            if zname in rain_active_zones
        ]
        if not flooded_centres:
            return None
        dry_edge_cells = []
        for zlat, zlng, zrad in flooded_centres:
            outer = self.grid.nearby_cells(zlat, zlng, zrad + 1.5)
            inner_keys = {grid_key(c.grid_lat, c.grid_lng)
                          for c in self.grid.nearby_cells(zlat, zlng, zrad)}
            for cell in outer:
                if grid_key(cell.grid_lat, cell.grid_lng) not in inner_keys:
                    cell.demand_score = min(100, cell.demand_score * 2.0)
                    cell.surge_probability = min(1.0, cell.surge_probability * 2.0)
                    dry_edge_cells.append(cell)
        if not dry_edge_cells:
            return None
        best = max(dry_edge_cells, key=lambda c: c.demand_score)
        dist = haversine_km(rider.lat, rider.lng, best.grid_lat, best.grid_lng)
        bear = bearing_deg(rider.lat, rider.lng, best.grid_lat, best.grid_lng)
        return {
            "alert": "MONSOON_DRY_EDGE",
            "flooded_zones": rain_active_zones,
            "dry_edge_lat": best.grid_lat,
            "dry_edge_lng": best.grid_lng,
            "distance_km": round(dist, 2),
            "bearing_deg": round(bear, 1),
            "demand_score": round(best.demand_score, 1),
            "message": (f"Rain blocking {', '.join(rain_active_zones)}. "
                        f"Courier deficit spiking at dry edge "
                        f"{dist:.1f}km {compass_label(bear)}. "
                        f"Move there NOW â€” demand multiplier 2x."),
        }


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 12 â€” PREDICTIVE HOLD STATE MACHINE
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class PredictiveHoldSM:
    """
    Fuel-cost vs. intercept-probability gate. States: MOVE | MOVE_CAUTIOUS | HOLD | CHARGE.

    v4.2 CHANGE â€” the original version defaulted to HOLD any time the best
    available zone fell short of MIN_PROFIT_THRESHOLD or the confidence
    floor. In practice this is wrong: a rider standing still earns exactly
    GHS 0.00/hour. A zone projecting GHS 3.50 (just under the old GHS 4.00
    cliff) still beats standing still, AND moving keeps the rider in
    position to catch the next real surge as conditions change â€” standing
    still doesn't. HOLD is now reserved for situations where moving is
    genuinely the wrong call (fuel-critical, deep overnight, or truly
    nothing in range at all) â€” not just "the best option isn't great."

    Returns (should_hold: bool, reason: str, degraded: bool) â€” degraded=True
    means "moving, but be honest this isn't a top-tier call" so the
    frontend can show it differently from a confident MOVE.
    """

    # Below this net yield, moving is still allowed but flagged as a
    # low-confidence move rather than presented as a strong recommendation.
    DEGRADED_PROFIT_FLOOR = 1.00   # GHS â€” below THIS, genuinely not worth the fuel
    DEGRADED_CONFIDENCE_FLOOR = 0.12  # below this, the signal is closer to noise than data

    def evaluate(self, rider: RiderTelemetry, primary_vector: Optional[DriftVector],
                 hour: int) -> tuple:
        if rider.fuel_level_pct < 15:
            return True, "CHARGE â€” fuel critically low (<15%). Locate nearest fuel station.", False

        if primary_vector is None:
            return True, ("HOLD â€” nothing in range at all right now. "
                          "Save fuel. Stand by â€” this will refresh as soon as something appears."), False

        fuel_cost = primary_vector.distance_km * FUEL_COST_GHS_PER_KM
        net_yield = primary_vector.expected_yield_ghs - fuel_cost

        # Only a genuinely worthless move (net yield below fuel cost itself,
        # or near-zero signal) gets vetoed into HOLD. Everything else moves â€”
        # just labeled honestly if it's a long shot rather than a sure thing.
        if net_yield < self.DEGRADED_PROFIT_FLOOR and primary_vector.confidence < self.DEGRADED_CONFIDENCE_FLOOR:
            return True, (f"HOLD â€” best option nets only GHS {net_yield:.2f} after fuel, "
                          f"with very low confidence ({primary_vector.confidence:.0%}). "
                          f"Genuinely not worth the trip. Wait for a stronger signal."), False

        if 23 <= hour or hour < 5:
            return True, "HOLD â€” low overnight demand. Rest until 05:00.", False

        if net_yield < MIN_PROFIT_THRESHOLD or primary_vector.confidence < 0.30:
            # Below the "ideal" bar, but still positive expected value and
            # not zero-confidence noise â€” move, but say so honestly.
            return False, (f"MOVE (long shot) â€” projected GHS {net_yield:.2f} net, "
                           f"{primary_vector.confidence:.0%} confidence. Below our usual bar, "
                           f"but still beats standing still. Your call."), True

        return False, "", False


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 13 â€” ADAPTIVE POLLER  (kinematic battery & data optimizer)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class AdaptivePoller:
    """
    STATIONARY  (speed â‰¤ 2 km/h or HOLD)  â†’ 90-120s  (battery saver)
    CRUISING    (speed 3-20 km/h)          â†’ 25-35s   (standard tracking)
    INTERCEPTING (speed > 20 + confâ‰¥0.55)  â†’ 8-10s    (precision mode)
    """

    STATIONARY_RANGE  = (90, 120)
    CRUISING_RANGE    = (25, 35)
    INTERCEPT_RANGE   = (8, 10)
    CONFIDENCE_THRESH = 0.55

    def compute(self, rider: RiderTelemetry, hold: bool,
                primary_vector: Optional[DriftVector]) -> int:
        if hold or rider.speed_kmh <= 2:
            return random.randint(*self.STATIONARY_RANGE)
        conf = primary_vector.confidence if primary_vector else 0.0
        if rider.speed_kmh > 20 and conf >= self.CONFIDENCE_THRESH:
            return random.randint(*self.INTERCEPT_RANGE)
        return random.randint(*self.CRUISING_RANGE)

    @staticmethod
    def label(interval: int) -> str:
        if interval >= 90:
            return "STATIONARY â€” battery saver mode"
        if interval <= 10:
            return "INTERCEPT â€” high-precision tracking"
        return "CRUISING â€” standard tracking"


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 14 â€” BOOSTER ENGINE  (main orchestrator, v4.0)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

class BoosterEngine:
    def __init__(self, places_path: str = "places.json"):
        print("\n  Initialising FalconFX Booster Engine v4.0...")
        self.grid      = GridEngine(places_path)
        self.friction  = TrafficFriction()
        self.demand    = DemandSimulator(self.grid)
        self.wave      = VelocityWaveEngine(self.friction)
        self.leapfrog  = LeapfrogRouter(self.grid, self.wave, self.friction)
        self.arbitrage = ReturnTicketArbitrage(self.grid, self.wave)
        self.corp_arb  = CorporateArbitrageRouter()
        self.waybill   = WaybillInterceptor()
        self.monsoon   = MonsoonLayer(self.grid)
        self.hold_sm   = PredictiveHoldSM()
        self.poller    = AdaptivePoller()
        print("  Engine ready. [Cash Cow Guard | Ghost Penalty | Mega-Church Waves | Corp Arbitrage]\n")

    def compute(self,
                rider: RiderTelemetry,
                hour: int,
                minute: int = 0,
                search_radius_km: float = 5.0,
                simulate_hotspots=None,
                rain_active_zones=None,
                weekday: int = None,
                cell_weight_overrides: dict = None) -> BoosterOutput:

        ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Infer weekday if not supplied
        if weekday is None:
            weekday = datetime.datetime.now().weekday()  # 0=Monâ€¦6=Sun

        # â”€â”€ 0. Predictive front-runner: advance wall-clock by PREDICTIVE_OFFSET_MINS
        #    Demand signals are scored against WHERE THE MARKET WILL BE, not where it is.
        #    Corp/waybill/hold logic continues to use the real clock (window-based gates).
        future_h, future_m = _offset_time(hour, minute, PREDICTIVE_OFFSET_MINS)

        # â”€â”€ 1. Inject demand signals at FUTURE time (+15 min offset)
        self.demand.inject_signals(future_h, minute=future_m,
                                   simulate_hotspots=simulate_hotspots,
                                   weekday=weekday)

        # â”€â”€ 1b. Apply external match telemetry weight overrides (rider feedback loop)
        if cell_weight_overrides:
            for cell in self.grid.cells.values():
                key = (round(cell.grid_lat, GRID_RESOLUTION),
                       round(cell.grid_lng, GRID_RESOLUTION))
                mod = cell_weight_overrides.get(key)
                if mod is not None and mod != 1.0:
                    cell.demand_score = max(0.0, cell.demand_score * mod)

        # â”€â”€ 2. Candidate hotspot cells within rider's search radius
        nearby = self.grid.nearby_cells(rider.lat, rider.lng, search_radius_km)
        hotspot_cells = [c for c in nearby if c.is_hotspot]

        # â”€â”€ 3. Rank by front-running intercept score (future time window)
        ranked = self.wave.rank_cells(rider, hotspot_cells, future_h, future_m, top_n=5)

        # â”€â”€ 4. Build primary drift vector
        primary_vector = None
        ghost_penalty_applied = False
        top_band = "N/A"

        if ranked:
            top_score, top_cell = ranked[0]
            dist = haversine_km(rider.lat, rider.lng,
                                top_cell.grid_lat, top_cell.grid_lng)
            bear = bearing_deg(rider.lat, rider.lng,
                               top_cell.grid_lat, top_cell.grid_lng)
            tta  = self.wave.compute_tta(rider, top_cell.grid_lat,
                                         top_cell.grid_lng, hour, minute)
            friction_mult = self.friction.speed_multiplier(rider.lat, rider.lng,
                                                           hour, minute)
            road_label    = self.friction.road_quality_label(rider.lat, rider.lng)
            # v4.0: corporate non-riding overhead baked into yield
            corp_penalty_min = self.friction.corporate_time_penalty_min(
                top_cell.grid_lat, top_cell.grid_lng, hour, weekday)
            corp_yield_discount = (corp_penalty_min / 60.0) * 8.0  # GHS 8/hr opportunity cost
            expected_ghs  = max(0.0, top_score * 0.08 - corp_yield_discount)
            # v4.0: velocity-aware band label + Cash Cow Guard
            top_band      = self.wave.acceleration_band_label(
                top_cell.demand_score, top_cell.demand_velocity)
            ghost_penalty_applied = top_band.startswith("GHOST")
            cash_cow_active       = (top_band == "SUSTAINED_CASH_COW")

            # Event friction advisory (Action Chapel / Spintex gridlock)
            evt_friction = self.friction.event_friction_info(
                rider.lat, rider.lng, hour, minute, weekday)
            evt_note = (f" âš¡ EVENT FRICTION: {evt_friction['zone']} â€” "
                        f"{evt_friction['event']} gridlock ({evt_friction['penalty']*100:.0f}% "
                        f"speed loss, {evt_friction['dist_km']}km away)."
                        if evt_friction else "")
            corp_note = (f" Corp overhead baked in: {corp_penalty_min:.0f}min gate+walk+lift."
                         if corp_penalty_min > 0 else "")

            primary_vector = DriftVector(
                target_lat=top_cell.grid_lat,
                target_lng=top_cell.grid_lng,
                bearing_deg=round(bear, 1),
                distance_km=round(dist, 2),
                tta_min=round(tta, 1),
                expected_yield_ghs=round(expected_ghs, 2),
                confidence=round(min(0.99, top_score / 100.0), 2),
                action="MOVE",
                reason=(
                    f"[{top_band}] Surge wave peaking in {top_cell.checkout_eta_min:.0f}min "
                    f"at {top_cell.grid_lat:.4f},{top_cell.grid_lng:.4f}. "
                    f"Head {compass_label(bear)} â€” arrive in {tta:.0f}min. "
                    f"Road: {road_label}. "
                    f"Traffic friction: {(1-friction_mult)*100:.0f}% total degradation."
                    f"{evt_note}{corp_note}"
                ),
            )

        # â”€â”€ 5. Hold state machine
        hold, hold_reason, move_degraded = self.hold_sm.evaluate(rider, primary_vector, hour)

        # â”€â”€ 6. HotSpot summary objects
        hotspots_out = []
        for score, cell in ranked[:3]:
            cat_counter = defaultdict(int)
            for p in cell.places:
                cat_counter[p.get("cat", "other")] += 1
            band = self.wave.acceleration_band_label(cell.demand_score, cell.demand_velocity)
            dist_km = haversine_km(rider.lat, rider.lng, cell.grid_lat, cell.grid_lng)
            # Decay curve, not linear fuel-only deduction: a zone twice as
            # far needs meaningfully higher demand/confidence to score the
            # same â€” addresses riders being sent unnecessarily far for only
            # a marginal yield edge over something closer.
            distance_factor = 1 / (1 + dist_km) ** 1.5
            raw_opportunity = (cell.demand_score * 0.5 + cell.surge_probability * 100 * 0.5) * distance_factor
            hotspots_out.append(HotSpot(
                lat=cell.grid_lat,
                lng=cell.grid_lng,
                radius_km=0.11,
                demand_score=round(cell.demand_score, 1),
                surge_probability=round(cell.surge_probability, 2),
                checkout_eta_min=round(cell.checkout_eta_min or 0, 1),
                category_mix=dict(cat_counter),
                label=", ".join(p["name"] for p in cell.places[:2]) or "Unnamed cluster",
                acceleration_band=band,
                opportunity_score=round(min(100, max(0, raw_opportunity)), 1),
            ))

        # â”€â”€ 6.5 Nearby pick: closest of the top-3 that still clears the
        # yield floor â€” gives the rider a short-trip option alongside the
        # best-overall pick, instead of only ever pointing at the highest
        # yield regardless of distance.
        nearby_pick = None
        candidates = [(score, cell) for score, cell in ranked[:3] if cell.demand_score >= MIN_PROFIT_THRESHOLD * 0.5]
        if candidates:
            _, nearest_cell = min(candidates, key=lambda sc: haversine_km(
                rider.lat, rider.lng, sc[1].grid_lat, sc[1].grid_lng))
            nearby_pick = {
                "lat": nearest_cell.grid_lat, "lng": nearest_cell.grid_lng,
                "label": ", ".join(p["name"] for p in nearest_cell.places[:2]) or "Unnamed cluster",
                "distance_km": round(haversine_km(rider.lat, rider.lng, nearest_cell.grid_lat, nearest_cell.grid_lng), 2),
            }

        # â”€â”€ 7. Leapfrog
        leapfrog_vector = self.leapfrog.next_zone(rider, hour, minute)

        # â”€â”€ 8. Return ticket arbitrage
        arb_alert = self.arbitrage.check(rider, hour)

        # â”€â”€ 9. Waybill intercept
        waybill_alert = self.waybill.check(rider, hour, minute, weekday)

        # â”€â”€ 9.5. Corporate arbitrage (v4.0)
        corp_arb_alert = self.corp_arb.check(rider, hour, minute, weekday)

        # â”€â”€ 10. Monsoon layer
        weather_advisory = self.monsoon.apply(rider, rain_active_zones or [], hour)

        # â”€â”€ 11. Adaptive poll interval
        poll_interval = self.poller.compute(rider, hold, primary_vector)

        # â”€â”€ 12. Grid stats
        active_cells   = [c for c in nearby if c.demand_score > 0]
        avg_score      = (sum(c.demand_score for c in active_cells) / len(active_cells)
                          if active_cells else 0)
        friction_here  = self.friction.speed_multiplier(rider.lat, rider.lng, hour, minute)
        road_surface   = self.friction.road_quality_label(rider.lat, rider.lng)
        shadow_active  = self.demand.active_shadow_windows(hour, minute)
        emerging_count = sum(1 for c in hotspot_cells
                             if VelocityWaveEngine.EMERGING_BAND_LOW
                             <= c.demand_score < VelocityWaveEngine.GHOST_SCORE_THRESHOLD)
        ghost_count    = sum(1 for c in hotspot_cells
                             if c.demand_score >= VelocityWaveEngine.GHOST_SCORE_THRESHOLD
                             and c.demand_velocity < VELOCITY_TREND_STABLE_THRESHOLD)
        cash_cow_count = sum(1 for c in hotspot_cells
                             if c.demand_score >= VelocityWaveEngine.GHOST_SCORE_THRESHOLD
                             and c.demand_velocity >= VELOCITY_TREND_STABLE_THRESHOLD)
        # v4.0 â€” megachurch event waves currently firing
        megachurch_active = self.demand._megachurch_event_boost(hour, minute, weekday)
        megachurch_names  = [s[4] for s in megachurch_active]
        event_fric = self.friction.event_friction_info(
            rider.lat, rider.lng, hour, minute, weekday)

        grid_stats = {
            "cells_scanned":              len(nearby),
            "hotspot_cells":              len(hotspot_cells),
            "avg_demand_score":           round(avg_score, 1),
            "traffic_friction_at_rider":  round(friction_here, 2),
            "effective_speed_kmh":        round(self.friction.effective_speed(rider, hour, minute), 1),
            "road_surface":               road_surface,
            "shadow_matrix_active":       shadow_active,
            "shadow_windows_firing":      len(shadow_active),
            "poll_mode":                  AdaptivePoller.label(poll_interval),
            # Front-running intelligence stats (v4.0)
            "front_running_mode":         True,
            "top_zone_band":              top_band,
            "ghost_penalty_applied":      ghost_penalty_applied,
            "cash_cow_guard_active":      cash_cow_active if ranked else False,
            "emerging_cells":             emerging_count,
            "ghost_cells_suppressed":     ghost_count,
            "cash_cow_cells":             cash_cow_count,
            # v4.0 additions
            "megachurch_waves_firing":    len(megachurch_active),
            "megachurch_events_active":   megachurch_names[:4],
            "event_friction":             event_fric,
            "weekday":                    weekday,
            # v4.1 â€” External Positioning Overlay / Predictive Front-Runner
            "predictive_offset_mins":     PREDICTIVE_OFFSET_MINS,
            "scored_at_future_hour":      future_h,
            "scored_at_future_min":       future_m,
            "telemetry_overrides_applied": bool(cell_weight_overrides),
        }

        return BoosterOutput(
            timestamp=ts,
            rider=asdict(rider),
            hold_recommended=hold,
            hold_reason=hold_reason,
            move_degraded=move_degraded,
            nearby_pick=nearby_pick,
            hotspots=[asdict(h) for h in hotspots_out],
            primary_vector=asdict(primary_vector) if primary_vector else None,
            leapfrog_vector=asdict(leapfrog_vector) if leapfrog_vector else None,
            arbitrage_alert=arb_alert,
            waybill_alert=waybill_alert,
            weather_advisory=weather_advisory,
            corporate_arbitrage=corp_arb_alert,
            grid_stats=grid_stats,
            next_poll_interval_seconds=poll_interval,
        )


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# SECTION 17 â€” CONSOLE SIMULATION DEMO  (v4.0 â€” 7 scenarios)
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

def _divider(char="â•", width=72): print(char * width)
def _title(t): _divider(); print(f"  {t}"); _divider()
def _section(t): print(f"\n  â”€â”€ {t} " + "â”€" * (65 - len(t)))


def _print_vector(label, v):
    if not v:
        print(f"    {label}: none")
        return
    print(f"    {label}:")
    print(f"      Action     : {v['action']}")
    print(f"      Target     : {v['target_lat']:.4f}, {v['target_lng']:.4f}")
    print(f"      Bearing    : {v['bearing_deg']:.1f}Â° ({compass_label(v['bearing_deg'])})")
    print(f"      Distance   : {v['distance_km']} km")
    print(f"      TTA        : {v['tta_min']} min")
    print(f"      Yield Est  : GHS {v['expected_yield_ghs']:.2f}")
    print(f"      Confidence : {v['confidence']:.0%}")
    print(f"      Reason     : {v['reason']}")


def _print_grid(g, poll_interval):
    print(f"    Cells scanned       : {g['cells_scanned']}")
    print(f"    Hotspot cells       : {g['hotspot_cells']}")
    print(f"    Avg demand score    : {g['avg_demand_score']}")
    print(f"    Traffic friction    : {g['traffic_friction_at_rider']:.0%} speed retained")
    print(f"    Effective speed     : {g['effective_speed_kmh']} km/h")
    print(f"    Road surface        : {g['road_surface']}")
    print(f"    Shadow windows      : {g['shadow_windows_firing']} firing")
    for sw in g['shadow_matrix_active'][:4]:
        print(f"                          â€¢ {sw}")
    print(f"    â”€â”€ FRONT-RUNNING ENGINE â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    print(f"    Top zone band       : {g['top_zone_band']}")
    print(f"    Ghost penalty       : {'YES â€” competitive dead zone suppressed' if g['ghost_penalty_applied'] else 'NO â€” clean target'}")
    print(f"    Emerging cells      : {g['emerging_cells']}  â† pre-checkout explosion targets")
    print(f"    Ghost cells suppressed: {g['ghost_cells_suppressed']}  â† mainstream already sees these")
    print(f"    â”€â”€ ADAPTIVE POLL â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€")
    print(f"    Next poll in        : {poll_interval}s")
    print(f"    Mode                : {g['poll_mode']}")


def run_simulation():
    _title("FalconFX BOOSTER v4.0 â€” Asymmetric Companion Weapon  |  Console Simulation")

    engine = BoosterEngine("places.json")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 1 â€” Front-Running Override: Evening peak, Osu cluster
    # Demonstrates: ghost penalty suppression + emerging band targeting
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    print("  SCENARIO 1 â€” Front-Running Override: Evening Peak, Osu/Airport")
    print("  Rider: Airport Residential, 28 km/h SE. Time: 18:12 (peak dinner)")
    print("  Proves: engine ignores already-peaked ghost zones â†’ targets EMERGING cells")
    _divider("â”€")

    rider1 = RiderTelemetry(
        lat=5.605, lng=-0.173, speed_kmh=28, heading_deg=135,
        has_active_delivery=False, fuel_level_pct=78,
    )
    signal_spikes = [
        (5.570, -0.170, 65),   # Osu food cluster (could be ghost)
        (5.560, -0.205, 55),   # Accra Central markets
        (5.617, -0.172, 45),   # Airport strip (emerging)
    ]
    out1 = engine.compute(
        rider=rider1, hour=18, minute=12,
        search_radius_km=5.0,
        simulate_hotspots=signal_spikes,
        rain_active_zones=[],
        weekday=0,   # Monday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider1.lat}Â°N, {rider1.lng}Â°E")
    print(f"    Speed      : {rider1.speed_kmh} km/h  |  Heading: {rider1.heading_deg}Â° {compass_label(rider1.heading_deg)}")
    print(f"    Fuel       : {rider1.fuel_level_pct}%")

    _section("GRID REPORT + FRONT-RUNNING INTELLIGENCE")
    _print_grid(out1.grid_stats, out1.next_poll_interval_seconds)

    _section("HOT SPOT CENTROIDS")
    for i, hs in enumerate(out1.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"eta=~{hs['checkout_eta_min']}min  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    _section("HOLD STATE MACHINE")
    status = "ðŸ›‘ HOLD" if out1.hold_recommended else ("âš ï¸ MOVE (long shot)" if out1.move_degraded else "âœ… MOVE")
    print(f"    Recommendation: {status}")
    if out1.hold_reason:
        print(f"    Reason: {out1.hold_reason}")

    _section("PRIMARY DRIFT VECTOR")
    _print_vector("Primary", out1.primary_vector)

    _section("WAYBILL INTERCEPT")
    if out1.waybill_alert:
        print(f"    âš¡ {out1.waybill_alert['message']}")
    else:
        print("    No waybill window active.")

    _section("WEATHER ADVISORY")
    if out1.weather_advisory:
        print(f"    ðŸŒ§  {out1.weather_advisory['message']}")
    else:
        print("    Clear conditions.")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 2 â€” Waybill Intercept: Friday Morning, Kaneshie Terminal
    # Demonstrates: weekend_multiplier + peak stacking + STC vs first-come
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    print("\n\n")
    _title("SCENARIO 2 â€” Waybill Intercept: Friday AM, Kaneshie + Rain Displacement")
    print("  Rider: near Madina, active delivery to Adenta. Time: 07:22 Friday")
    print("  Proves: Fri multiplier on Kaneshie terminal + rain dry-edge surge")
    _divider("â”€")

    rider2 = RiderTelemetry(
        lat=5.680, lng=-0.168, speed_kmh=38, heading_deg=10,
        has_active_delivery=True,
        dropoff_lat=5.706, dropoff_lng=-0.163,
        fuel_level_pct=55,
    )
    out2 = engine.compute(
        rider=rider2, hour=7, minute=22,
        search_radius_km=6.0,
        simulate_hotspots=[(5.706, -0.160, 30), (5.557, -0.244, 70)],
        rain_active_zones=["Accra Central", "Kaneshie Low", "Adabraka"],
        weekday=4,   # Friday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider2.lat}Â°N, {rider2.lng}Â°E")
    print(f"    Delivering : YES â†’ {rider2.dropoff_lat},{rider2.dropoff_lng} (Adenta)")
    print(f"    Speed      : {rider2.speed_kmh} km/h | Heading: {rider2.heading_deg}Â° {compass_label(rider2.heading_deg)}")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out2.grid_stats, out2.next_poll_interval_seconds)

    _section("LEAPFROG â€” Post Drop-off Pre-cache")
    _print_vector("Leapfrog", out2.leapfrog_vector)

    _section("RETURN TICKET ARBITRAGE")
    if out2.arbitrage_alert:
        print(f"    ðŸ“¦ {out2.arbitrage_alert['message']}")
    else:
        print("    No arbitrage opportunity.")

    _section("WAYBILL INTERCEPT  [FRIDAY MULTIPLIER]")
    if out2.waybill_alert:
        w = out2.waybill_alert
        print(f"    âš¡ {w['message']}")
        print(f"       Terminal type : {w['terminal_type']}")
        print(f"       Next arrival  : {w['next_arrival_min']} min")
    else:
        print("    No waybill window active.")

    _section("MONSOON DRY-EDGE ADVISORY")
    if out2.weather_advisory:
        print(f"    ðŸŒ§  {out2.weather_advisory['message']}")
    else:
        print("    No rain displacement.")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 3 â€” B2B Wholesale: Wednesday Makola + Kantamanto Run
    # Demonstrates: day-of-week B2B injection, AMA Clamp, pedestrian penalty
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    print("\n\n")
    _title("SCENARIO 3 â€” B2B Wholesale Wednesday: Makola + Kantamanto")
    print("  Rider: near Accra Central, 08:15 Wednesday (maximum restock day)")
    print("  Proves: B2B day_weight 1.5-1.8x, AMA Clamp Risk, pedestrian friction")
    _divider("â”€")

    rider3 = RiderTelemetry(
        lat=5.555, lng=-0.207, speed_kmh=18, heading_deg=45,
        has_active_delivery=False, fuel_level_pct=88,
    )
    out3 = engine.compute(
        rider=rider3, hour=8, minute=15,
        search_radius_km=3.0,
        simulate_hotspots=None,
        rain_active_zones=[],
        weekday=2,   # Wednesday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider3.lat}Â°N, {rider3.lng}Â°E  (Accra Central / Makola)")
    print(f"    Speed      : {rider3.speed_kmh} km/h")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out3.grid_stats, out3.next_poll_interval_seconds)

    _section("HOLD / MOVE")
    status3 = "ðŸ›‘ HOLD" if out3.hold_recommended else "âœ… MOVE"
    print(f"    Recommendation: {status3}")
    if out3.hold_reason:
        print(f"    Reason: {out3.hold_reason}")

    _section("PRIMARY DRIFT VECTOR  [B2B WHOLESALE ZONE]")
    _print_vector("Primary", out3.primary_vector)

    _section("HOT SPOT CENTROIDS  [B2B INJECTION ACTIVE]")
    for i, hs in enumerate(out3.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"band={hs['acceleration_band']}")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 4 â€” Predictive HOLD: Tema outskirts, 14:30 inter-peak
    # Demonstrates: fuel cost > yield, HOLD, battery saver
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    print("\n\n")
    _title("SCENARIO 4 â€” Predictive HOLD: fuel cost > yield (Tema outskirts)")
    print("  Rider: Tema, 14:30, low inter-peak demand. Fuel 42%.")
    _divider("â”€")

    rider4 = RiderTelemetry(
        lat=5.673, lng=0.013, speed_kmh=5, heading_deg=270,
        has_active_delivery=False, fuel_level_pct=42,
    )
    out4 = engine.compute(
        rider=rider4, hour=14, minute=30,
        search_radius_km=4.0,
        simulate_hotspots=[],
        rain_active_zones=[],
        weekday=0,
    )

    g4 = out4.grid_stats
    _section("GRID REPORT")
    print(f"    Cells scanned     : {g4['cells_scanned']}")
    print(f"    Hotspot cells     : {g4['hotspot_cells']}")
    print(f"    Avg demand score  : {g4['avg_demand_score']}")
    print(f"    Emerging cells    : {g4['emerging_cells']} (pre-checkout targets)")
    print(f"    Ghost cells       : {g4['ghost_cells_suppressed']} (suppressed)")
    print(f"    Next poll         : {out4.next_poll_interval_seconds}s â† battery saver")
    print(f"    Mode              : {g4['poll_mode']}")

    _section("HOLD STATE MACHINE")
    status4 = "ðŸ›‘ HOLD" if out4.hold_recommended else "âœ… MOVE"
    print(f"    Recommendation: {status4}")
    if out4.hold_reason:
        print(f"    Reason: {out4.hold_reason}")

    if out4.primary_vector:
        _section("PRIMARY DRIFT VECTOR (low confidence â€” for reference)")
        _print_vector("Primary", out4.primary_vector)

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 5 â€” Night Market: Osu Oxford St, 21:00 (G&G + Osu Blue Gate)
    # Demonstrates: night food wave, Shadow Matrix peak 20:00-23:00
    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    print("\n\n")
    _title("SCENARIO 5 â€” Osu Night Market: G&G Special + Blue Gate, 21:00")
    print("  Rider: near Labone, 21:00 Saturday. Night-market wave ACTIVE.")
    print("  Proves: Oxford St/Osu night cluster (20-23h) + Tetteh Quarshie avoided")
    _divider("â”€")

    rider5 = RiderTelemetry(
        lat=5.576, lng=-0.166, speed_kmh=32, heading_deg=90,
        has_active_delivery=False, fuel_level_pct=65,
    )
    out5 = engine.compute(
        rider=rider5, hour=21, minute=0,
        search_radius_km=4.0,
        simulate_hotspots=None,
        rain_active_zones=[],
        weekday=5,   # Saturday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider5.lat}Â°N, {rider5.lng}Â°E  (Labone area)")
    print(f"    Speed      : {rider5.speed_kmh} km/h | Heading: {rider5.heading_deg}Â° {compass_label(rider5.heading_deg)}")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out5.grid_stats, out5.next_poll_interval_seconds)

    _section("NIGHT SHADOW MATRIX (active windows 21:00)")
    for sw in out5.grid_stats['shadow_matrix_active'][:8]:
        print(f"    â€¢ {sw}")

    _section("HOLD / MOVE")
    status5 = "ðŸ›‘ HOLD" if out5.hold_recommended else "âœ… MOVE"
    print(f"    Recommendation: {status5}")
    if out5.hold_reason:
        print(f"    Reason: {out5.hold_reason}")

    _section("PRIMARY DRIFT VECTOR  [NIGHT MARKET INTERCEPT]")
    _print_vector("Primary", out5.primary_vector)

    _section("HOT SPOT CENTROIDS  [NIGHT CLUSTER]")
    for i, hs in enumerate(out5.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"eta=~{hs['checkout_eta_min']}min  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    _section("WAYBILL")
    if out5.waybill_alert:
        print(f"    âš¡ {out5.waybill_alert['message']}")
    else:
        print("    No waybill window at 21:00.")

    # SCENARIO 6 â€” Mega-Church Spatial Wave: Action Chapel Sunday 2nd Dismissal
    # Rider near Spintex Rd, 10:52 Sunday (weekday=6)
    # Expected: massive demand spike injected near Action Chapel (capacity 30,000)
    #           Spintex event friction advisory fires
    #           top_zone_band reflects velocity spike from synchronized exit

    _title("SCENARIO 6 â€” Mega-Church Wave: Action Chapel Spintex, Sunday 10:52")

    rider6 = RiderTelemetry(
        lat=5.618, lng=-0.111,   # ~1.4km from Action Chapel Impact Arena
        speed_kmh=0.0,
        heading_deg=90.0,
        fuel_level_pct=80,
    )
    out6 = engine.compute(
        rider6, hour=10, minute=52, weekday=6,
        simulate_hotspots=None,
    )

    _section("PRIMARY VECTOR")
    if out6.primary_vector:
        pv = out6.primary_vector
        print(f"    Action  : {pv['action']}")
        print(f"    Bearing : {pv['bearing_deg']}Â° â€” {compass_label(pv['bearing_deg'])}")
        print(f"    TTA     : {pv['tta_min']}min  Dist: {pv['distance_km']}km")
        print(f"    Yield   : GHS {pv['expected_yield_ghs']}")
        print(f"    Band    : {pv['confidence']:.0%} confidence")
        print(f"    Reason  : {pv['reason'][:180]}")

    _section("GRID STATS â€” v4.0 Mega-Church Fields")
    g6 = out6.grid_stats
    print(f"    Top band              : {g6['top_zone_band']}")
    print(f"    Cash cow active       : {g6.get('cash_cow_guard_active')}")
    print(f"    Ghost penalty applied : {g6['ghost_penalty_applied']}")
    print(f"    Megachurch waves fire : {g6['megachurch_waves_firing']}")
    print(f"    Events active         : {g6.get('megachurch_events_active')}")
    print(f"    Event friction        : {g6.get('event_friction')}")

    _section("HOTSPOTS")
    for i, hs in enumerate(out6.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    # â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    # SCENARIO 7 â€” Corporate Arbitrage: Pre-COB Crunch, Ridge, 15:45 Thursday

    _title("SCENARIO 7 â€” Corporate Arbitrage: Pre-COB Crunch, North Ridge, Thu 15:45")

    rider7 = RiderTelemetry(
        lat=5.576, lng=-0.193,   # inside North Ridge Corporate Enclave radius
        speed_kmh=0.0,
        heading_deg=180.0,
        fuel_level_pct=65,
    )
    out7 = engine.compute(
        rider7, hour=15, minute=45, weekday=3,  # Thursday
        simulate_hotspots=None,
    )

    _section("CORPORATE ARBITRAGE ALERT")
    if out7.corporate_arbitrage:
        ca = out7.corporate_arbitrage
        print(f"    Alert     : {ca['alert']}")
        print(f"    Window    : {ca['window_type']}")
        print(f"    Zone      : {ca['zone']}")
        print(f"    Flow      : {ca['flow']} â€” {ca['flow_name']}")
        print(f"    Pickup    : {ca['pickup_node']}")
        print(f"    Access    : {ca['pickup_access']}")
        print(f"    Bearing â†’ : {ca['bearing_to_pickup']}Â°  ({ca['dist_to_pickup_km']}km)")
        print(f"    â†’ Dest    : {ca['primary_destination']}")
        print(f"    Overhead  : {ca['non_riding_overhead_min']}min total")
        print(f"              : gate={ca['gate_screening_min']}min + "
              f"walk={ca['walk_distance_m']}m + lift={ca['elevator_wait_min']}min")
        print(f"    Message   : {ca['message'][:200]}")
    else:
        print("    No corporate arbitrage window active at this location/time.")
        print(f"    (rider at {rider7.lat},{rider7.lng}  hour={15}:{45}  weekday={3})")

    _section("PRIMARY VECTOR")
    if out7.primary_vector:
        pv7 = out7.primary_vector
        print(f"    Action  : {pv7['action']}")
        print(f"    Band    : {pv7['reason'][:140]}")

    _divider()
    print(f"  v4.0 Simulation complete.  Timestamp: {out1.timestamp}")
    print(f"  7 scenarios verified:")
    print(f"    1. Ghost Penalty + Acceleration Scoring (Osu/Airport evening peak)")
    print(f"    2. Waybill Intercept + Rain Displacement (Kaneshie Friday AM)")
    print(f"    3. B2B Wholesale Wednesday (Makola + Kantamanto)")
    print(f"    4. Predictive HOLD: fuel cost > yield (Tema outskirts)")
    print(f"    5. Night Market: Osu Oxford St 21:00")
    print(f"    6. â˜… Mega-Church Spatial Wave: Action Chapel Spintex Sunday 10:52")
    print(f"    7. â˜… Corporate Arbitrage: Pre-COB Crunch Ridge Thursday 15:45")
    print(f"  FastAPI â†’ python3 api.py  |  POST /booster/compute")
    _divider()

    with open("booster_output_sample.json", "w") as f:
        json.dump(asdict(out1), f, indent=2, default=str)
    print(f"\n  Sample JSON â†’ booster_output_sample.json")


if __name__ == "__main__":
    run_simulation()# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONSTANTS & CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

EARTH_RADIUS_KM = 6371.0
GRID_RESOLUTION = 3          # decimal places → ~110 m cell at Accra latitude
FUEL_COST_GHS_PER_KM = 1.80  # GHS per km (petrol-equivalent for motorbike)
MIN_PROFIT_THRESHOLD = 4.00  # GHS — below this, HOLD is recommended
ACCRA_LAT_CENTRE = 5.60
ACCRA_LNG_CENTRE = -0.18
OFF_PEAK_SPEED_KMH = 50.0    # baseline free-flow speed
ARTERIAL_PEAK_DEGRADATION = 0.60   # 60% slowdown on 70% of major arteries
ARTERIAL_PEAK_COVERAGE = 0.70      # fraction of arterial grid affected

# ── Velocity Trend Validation — Cash Cow Guard threshold
# If a zone's demand_velocity >= this, the ghost haircut is SUPPRESSED even
# at score ≥ 85. The zone is still printing money (deep market rush, downpour).
VELOCITY_TREND_STABLE_THRESHOLD = 8.0    # velocity units — above = sustained cash cow

# ── EXTERNAL POSITIONING OVERLAY — Predictive Front-Runner Offset
# Demand signals are injected for (current_time + PREDICTIVE_OFFSET_MINS) so riders
# are positioned BEFORE third-party apps trigger global surge visibility.
# Covers: corporate COB ramp, nightlife pre-loading, church dismissal, AM rush.
PREDICTIVE_OFFSET_MINS = 15              # minutes ahead of live clock

# ── Category demand weights (how likely a place type generates delivery orders)
CATEGORY_DEMAND_WEIGHT = {
    "food":       10,
    "market":      9,
    "mall":        8,
    "hospital":    6,
    "university":  5,
    "school":      4,
    "bank":        3,
    "hotel":       5,
    "leisure":     4,
    "transport":   7,
    "office":      4,
    "govt":        2,
    "church":      1,
    "fuel":        1,
    "police":      0,
    "area":        2,
    "other":       1,
}

# ── Kitchen prep buffers in minutes (category → min, max)
KITCHEN_PREP_BUFFER = {
    "food":    (12, 15),   # chop bars, local restaurants — cook-to-order
    "mall":    (3,  5),    # retail pick-pack
    "market":  (5,  8),    # market vendors assembling orders
    "hotel":   (10, 20),   # room service / F&B
    "other":   (2,  4),
}
FUFU_LIGHTSOUP_BUFFER = (12, 15)   # dedicated buffer for heavy Ghanaian mains
INSTANT_CATEGORIES = {
    "hospital", "bank", "fuel", "transport", "university", "school", "office", "govt"
}

# ──────────────────────────────────────────────────────────────────────────────
# CORRIDOR TRAFFIC CONSTRAINTS  (ACCRA_TRAFFIC_CONSTRAINTS)
# Exact degradation profiles per arterial corridor with 2026 constraints.
# peak_hours: list of (h_start, m_start, h_end, m_end) tuples (24-hr clock)
# speed_degradation: fraction of speed LOST (0.45 = 45% slower than baseline)
# disruption_flag: force reroute avoidance when True
# ──────────────────────────────────────────────────────────────────────────────
ACCRA_TRAFFIC_CONSTRAINTS = {
    "spintex_road": {
        "lat": 5.620, "lng": -0.110,
        "radius_km": 4.0,
        "peak_hours": [(6, 30, 9, 30), (16, 30, 20, 0)],
        "speed_degradation": 0.45,      # 45% slowdown near Flowerpot/Palace Mall
        "critical_nodes": ["flowerpot", "palace_mall", "teshie_link"],
    },
    "liberation_road": {
        "lat": 5.576, "lng": -0.196,
        "radius_km": 3.0,
        "peak_hours": [(7, 0, 9, 0), (16, 0, 19, 0)],
        "speed_degradation": 0.35,      # 35% airport merging drag
    },
    "tetteh_quarshie": {
        "lat": 5.650, "lng": -0.172,
        "radius_km": 2.5,
        "peak_hours": [(6, 30, 10, 0), (15, 30, 20, 30)],
        "speed_degradation": 0.75,      # 75% — 2026 lane closures + 4→3 lane reduction
        "accra_madina_degradation": 0.75,  # worst direction: Accra → Madina
        "disruption_flag": True,           # engine avoids Accra-Madina cuts
    },
    "george_bush_n1": {
        "lat": 5.610, "lng": -0.206,
        "radius_km": 3.5,
        "peak_hours": [(6, 30, 9, 30), (12, 0, 14, 0), (16, 0, 20, 30)],
        "speed_degradation": 0.50,      # 50% tie-in choke at interchange
    },
}

# ── Known Accra traffic bottlenecks (expanded — all major choke points)
#    (name, lat, lng, peak_h_start, peak_h_end, severity)
BOTTLENECKS = [
    # Spintex corridor
    ("Spintex / Flowerpot (AM)",    5.620, -0.110, 6,  10, 0.45),
    ("Spintex / Palace Mall (PM)",  5.622, -0.108, 16, 20, 0.45),
    # Liberation Road
    ("Liberation Road (AM)",        5.576, -0.196, 7,   9, 0.35),
    ("Liberation Road (PM)",        5.576, -0.196, 16, 19, 0.35),
    # Tetteh Quarshie — 2026 DISRUPTION FLAG: elevated to 75%
    ("Tetteh Quarshie (AM)",        5.650, -0.172, 6,  10, 0.75),
    ("Tetteh Quarshie (PM)",        5.650, -0.172, 15, 21, 0.70),
    # George Bush / N1
    ("George Bush N1 (AM)",         5.610, -0.206, 6,  10, 0.50),
    ("George Bush N1 (Midday)",     5.610, -0.206, 12, 14, 0.40),
    ("George Bush N1 (PM)",         5.610, -0.206, 16, 21, 0.50),
    # Legacy choke points
    ("Kwame Nkrumah Circle",        5.571, -0.222, 7,  19, 0.50),
    ("Kaneshie",                    5.560, -0.242, 7,  19, 0.55),
    ("Tema Motorway Toll",          5.620,  0.000, 7,   9, 0.60),
    ("37 Military Hospital Jct",    5.590, -0.188, 7,  19, 0.60),
    ("Achimota Overhead",           5.639, -0.237, 7,   9, 0.58),
    ("Caprice/Labone",              5.572, -0.166, 17, 20, 0.65),
    ("Adenta Barrier",              5.696, -0.163, 7,   9, 0.50),
    ("Madina Market",               5.680, -0.168, 8,  18, 0.55),
    # Narrow alley / AMA Clamp choke points
    ("Opera Square / M.A. Street",  5.551, -0.207, 7,  18, 0.60),
    ("Kantamanto / Baltimore St",   5.548, -0.208, 6,  10, 0.55),
    ("Nii Abose St (Abossey Okai)", 5.566, -0.231, 7,  19, 0.55),
    ("Shiashie Trotro Corridor",    5.608, -0.166, 11, 14, 0.50),
    ("Danquah Circle (Waakye AM)",  5.567, -0.178, 7,   9, 0.55),
    ("Independence Ave / KojoThom", 5.554, -0.204, 7,  20, 0.45),
]

# ── Pedestrian Congestion Zones (separate friction layer, always-on during window)
#    (name, lat, lng, radius_km, h_start_float, h_end_float, ped_penalty)
PEDESTRIAN_CONGESTION_ZONES = [
    ("Danquah Circle Waakye Rush",   5.567, -0.178, 0.35, 7.0,  9.5,  0.30),
    ("Makola Market Foot Traffic",   5.550, -0.206, 0.50, 7.0, 18.0,  0.20),
    ("Kantamanto Street Press",      5.548, -0.208, 0.40, 6.0,  9.0,  0.35),
    ("Kantamanto Street Press (PM)", 5.548, -0.208, 0.40, 14.0, 16.0, 0.28),
    ("Opera Square Alley Clamp",     5.551, -0.207, 0.30, 7.0, 18.0,  0.40),
    ("Shiashie Trotro Terminal",     5.608, -0.166, 0.40, 11.5, 13.5, 0.35),
    ("Kaneshie Market Overflow",     5.556, -0.244, 0.45, 7.0, 19.0,  0.25),
    ("Agbogbloshie Morning Rush",    5.556, -0.231, 0.40, 6.0,  9.0,  0.30),
    ("Neoplan/STC Forecourt",        5.560, -0.205, 0.30, 6.0, 21.0,  0.22),
    ("Osu Oxford St Night (PM)",     5.564, -0.178, 0.50, 20.0, 23.0, 0.25),
]

# ── Low-density outskirt zones for Return Ticket Arbitrage
LOW_DENSITY_ZONES = [
    ("Adenta",    5.706, -0.163, 5.0),
    ("Kasoa",     5.534, -0.419, 4.0),
    ("Weija",     5.567, -0.321, 3.5),
    ("Dodowa",    5.884, -0.104, 4.0),
    ("Ashaiman",  5.698,  0.031, 3.5),
    ("Bortianor", 5.557, -0.323, 3.0),
    ("Oyibi",     5.770, -0.120, 3.0),
]

# ──────────────────────────────────────────────────────────────────────────────
# CORPORATE LANDING ZONE FRICTION CONSTANTS
# Bakes physical door-to-desk delays (gate screening + walk + lift) into the
# Net Hourly Yield calculation to prevent the Invisible Non-Riding Time Drain.
# peak_windows: [(h_start_float, h_end_float)]  decimal hours
# sunday_closed: True → 100% access denial on Sundays
# saturday_capacity: 0.5 = 50% reduced, 1.0 = full
# cutoff_hour: hard deadline — engine issues URGENT note if approaching
# ──────────────────────────────────────────────────────────────────────────────
CORPORATE_LANDING_ZONES = [
    {
        "name": "Ministries District / Accra Central Financial Core",
        "lat": 5.558, "lng": -0.197,
        "radius_km": 0.8,
        "gate_screening_min": 15,    # ID check + package inspection
        "walk_distance_m": 300,      # bikes banned inside — walk from perimeter
        "elevator_wait_min": 12,
        "peak_windows": [(8.0, 9.5), (11.0, 12.5), (14.5, 16.0)],
        "sunday_closed": True,
        "saturday_capacity": 1.0,
        "cutoff_hour": 16.5,         # Ministries shuts at 16:30 sharp
    },
    {
        "name": "Ridge / North Ridge Corporate Enclaves",
        "lat": 5.574, "lng": -0.191,
        "radius_km": 0.7,
        "gate_screening_min": 8,
        "walk_distance_m": 100,
        "elevator_wait_min": 9,
        "peak_windows": [(9.0, 10.5), (15.0, 16.5)],
        "sunday_closed": False,
        "saturday_capacity": 1.0,
        "cutoff_hour": 18.0,
    },
    {
        "name": "Airport City Commercial Hub",
        "lat": 5.605, "lng": -0.167,
        "radius_km": 0.9,
        "gate_screening_min": 10,    # package X-ray at aviation security
        "walk_distance_m": 200,      # 200m from airport perimeter
        "elevator_wait_min": 10,
        "peak_windows": [(8.5, 10.0), (11.5, 13.0)],
        "sunday_closed": False,
        "saturday_capacity": 0.5,    # 50% reduced Saturday capacity
        "cutoff_hour": 19.0,
    },
]

# ── Centralized Pickup Nodes — exact access points for each corporate zone
CORPORATE_PICKUP_NODES = [
    {
        "name": "Ecobank HQ — Ground Floor Mailroom Annex",
        "lat": 5.572, "lng": -0.194,
        "flow": "A",
        "access": "Rear service gate, Morocco Lane, West Ridge",
    },
    {
        "name": "Standard Chartered Tower — Basement Courier Bays",
        "lat": 5.604, "lng": -0.168,
        "flow": "B",
        "access": "Basement courier bay B1 level, Airport City",
    },
    {
        "name": "Ministries — Ground Floor General Registry",
        "lat": 5.556, "lng": -0.198,
        "flow": "A",
        "access": "General Registry offices, manual stamp books required",
    },
]

# ── Outbound Routing Flows (three destination categories)
CORPORATE_OUTBOUND_FLOWS = {
    "A": {
        "name": "Regulatory / Judicial Flow",
        "description": "High Street Courts + Registrar General's Dept, Accra Central",
        "destinations": [
            {"name": "High Street Courts", "lat": 5.548, "lng": -0.198},
            {"name": "Registrar General's Dept", "lat": 5.552, "lng": -0.202},
        ],
    },
    "B": {
        "name": "International Cargo Flow",
        "description": "KIA Logistics Village / GACC Ghana Customs",
        "destinations": [
            {"name": "KIA Logistics Village", "lat": 5.604, "lng": -0.173},
            {"name": "GACC / Customs Examination", "lat": 5.598, "lng": -0.165},
        ],
    },
    "C": {
        "name": "Upcountry Domestic Sorting Flow",
        "description": "Kwame Nkrumah Circle VIP/STC or North Industrial Area",
        "destinations": [
            {"name": "Kwame Nkrumah Circle VIP / STC", "lat": 5.571, "lng": -0.222},
            {"name": "North Industrial Area Sorting Hub", "lat": 5.580, "lng": -0.230},
        ],
    },
}

# ── Terminal Schedules for WaybillInterceptor (exact real-world timetables)
#    windows: list of (h_start_float, h_end_float) — decimal hours
#    peak_stacking: high-density arrival clusters within windows
#    type: "FIRST_COME" | "STC_HOURLY" | "MIXED"
#    weekend_days: 0=Mon…6=Sun; listed days get weekend_multiplier applied
TERMINAL_SCHEDULES = [
    {
        "name": "Kwame Nkrumah Circle (VIP/Odawna/Obra Spot/Mamobi)",
        "lat": 5.571, "lng": -0.222,
        "windows": [(5.5, 9.5), (12.0, 14.0), (16.5, 20.5)],
        "peak_stacking": [(6.0, 8.0), (17.0, 19.5)],
        "weekend_days": [4, 6],       # Friday (4), Sunday (6) + public holiday eves
        "weekend_multiplier": 1.4,
        "type": "FIRST_COME",         # VIP: first-come first-served
        "arrival_interval_min": 25,   # buses every 25-35 min during windows
    },
    {
        "name": "Kaneshie Motorway Terminal",
        "lat": 5.557, "lng": -0.244,
        "windows": [(5.0, 8.5), (16.0, 21.0)],
        "peak_stacking": [(5.0, 8.5), (17.0, 21.0)],
        "weekend_days": [3, 4, 5, 6],  # Thu-Sun peak: Thu(3) Fri(4) Sat(5) Sun(6)
        "weekend_multiplier": 1.5,     # Sun afternoon/evening heavily optimised inward
        "type": "FIRST_COME",
        "arrival_interval_min": 30,
    },
    {
        "name": "Neoplan Station / STC",
        "lat": 5.560, "lng": -0.205,
        "windows": [(6.0, 9.0), (13.0, 15.0), (18.0, 21.0)],
        "peak_stacking": [(8.0, 9.0)],  # Cape Coast inbound at 08:00
        "cape_coast_proxy_hour": 8.0,    # dedicated Cape Coast tracking proxy
        "stc_mon_fri_hourly": True,      # STC departs on the hour 06:00-18:00 Mon-Fri
        "weekend_days": [5, 6],
        "weekend_multiplier": 1.3,
        "type": "STC_HOURLY",
        "arrival_interval_min": 35,
    },
    {
        "name": "Tema Station",
        "lat": 5.673, "lng":  0.013,
        "windows": [(6.0, 21.0)],
        "peak_stacking": [(6.0, 9.0), (16.0, 20.0)],
        "weekend_days": [5, 6],
        "weekend_multiplier": 1.2,
        "type": "MIXED",
        "arrival_interval_min": 30,
    },
    {
        "name": "Madina Lorry Park",
        "lat": 5.682, "lng": -0.169,
        "windows": [(6.0, 20.0)],
        "peak_stacking": [(6.0, 9.0), (15.0, 19.0)],
        "weekend_days": [4, 5, 6],
        "weekend_multiplier": 1.2,
        "type": "FIRST_COME",
        "arrival_interval_min": 30,
    },
]

# ── B2B Wholesale & Waybill Epicenters
#    day_weights: {weekday_int: multiplier}  0=Mon…6=Sun
#    windows: [(h_start_float, h_end_float), ...]
#    primary_window: first dispatch wave
#    secondary_window: clearance wave
B2B_WHOLESALE_ZONES = [
    {
        "name": "Makola Market & Opera Square",
        "lat": 5.550, "lng": -0.206,
        "radius_km": 0.6,
        "day_weights": {0: 0.6, 1: 0.7, 2: 1.5, 3: 0.8, 4: 0.9, 5: 1.5, 6: 0.3},
        # Wed (2) and Sat (5) heavy restock multipliers
        "primary_window": (7.0, 10.0),    # morning wholesale dispatch wave
        "secondary_window": (15.0, 17.0), # afternoon clearance wave
        "ama_clamp_risk": True,            # narrow alleys → rapid mobile pickup vectors
        "base_intensity": 70,
    },
    {
        "name": "Kantamanto Market (Second-Hand Clothing Transit)",
        "lat": 5.548, "lng": -0.208,
        "radius_km": 0.5,
        "day_weights": {0: 0.4, 1: 0.5, 2: 1.8, 3: 0.5, 4: 1.8, 5: 0.6, 6: 0.3},
        # Wed (2) and Fri (4) pre-weekend retail allocation runs
        "primary_window": (6.0, 9.0),     # 15M garments per week filter here
        "secondary_window": (14.0, 16.0),
        "ama_clamp_risk": True,
        "base_intensity": 65,
    },
    {
        "name": "Abossey Okai (Automotive Spare Parts Hub)",
        "lat": 5.566, "lng": -0.231,
        "radius_km": 0.6,
        # Mon-Tue 07:00-18:00, Wed-Thu 07:30-18:00, Fri-Sat 08:00-17:30
        "day_weights": {0: 1.0, 1: 1.2, 2: 1.0, 3: 1.2, 4: 1.3, 5: 0.9, 6: 0.1},
        # Tue/Thu/Fri mechanic run days
        "primary_window": (7.5, 10.5),   # mechanic run peak
        "secondary_window": (13.0, 15.0),
        "ama_clamp_risk": False,
        "base_intensity": 60,
    },
]

# ── Rain-impacted district polygons
RAIN_FLOOD_ZONES = [
    ("Accra Central",  5.550, -0.206, 1.5),
    ("Lapaz",          5.609, -0.243, 1.2),
    ("Kaneshie Low",   5.556, -0.244, 1.0),
    ("Adabraka",       5.562, -0.212, 0.8),
    ("Nima",           5.589, -0.211, 1.0),
    ("Alajo",          5.591, -0.225, 0.9),
    ("Abossey Okai",   5.566, -0.231, 0.8),
]

# ── Road Quality Zones: unpaved / potholed / unstructured secondary roads
ROAD_QUALITY_ZONES = [
    ("Nima/Maamobi Back Streets",    5.589, -0.211, 0.6, 0.30),
    ("Chorkor Coastal Track",        5.537, -0.243, 0.8, 0.42),
    ("James Town/Ussher Lanes",      5.548, -0.206, 0.5, 0.35),
    ("Agbogbloshie Unpaved",         5.556, -0.231, 0.6, 0.45),
    ("Kasoa Pothole Corridor",       5.534, -0.419, 1.5, 0.48),
    ("Ashaiman Back Roads",          5.698,  0.031, 0.8, 0.35),
    ("Oyibi/Dodowa Rural Gravel",    5.770, -0.120, 2.0, 0.55),
    ("Darkuman Secondary",           5.584, -0.242, 0.5, 0.25),
    ("Alajo Back Streets",           5.591, -0.225, 0.4, 0.28),
    ("Labadi Beach Track",           5.553, -0.148, 0.6, 0.22),
    ("Adenta Unpaved Links",         5.706, -0.163, 0.8, 0.30),
    ("Weija Gravel Road",            5.567, -0.321, 0.7, 0.38),
    ("Dansoman Back Lanes",          5.546, -0.253, 0.5, 0.25),
    ("Kotobabi Unpaved",             5.581, -0.220, 0.4, 0.28),
]

# ──────────────────────────────────────────────────────────────────────────────
# SHADOW MATRIX — Offline / WhatsApp / phone-in demand sources invisible
# to aggregator platforms. Fully expanded v3.0 (27 zones).
#
# Format: (name, lat, lng, radius_km, windows [(h_start, h_end)], intensity)
# h values are decimal hours: 7.5 = 07:30, 20.0 = 20:00
# intensity 0-100: demand boost score injected into nearby grid cells
# ──────────────────────────────────────────────────────────────────────────────
SHADOW_MATRIX = [
    # ── MORNING WAAKYE WAVE (07:00-09:00, peak 07:30-09:30)
    ("Nima Waakye Belt",              5.589, -0.211, 0.4, [(7.0, 9.5)],              62),
    ("Osu Danquah Circle Waakye",     5.567, -0.178, 0.4, [(7.0, 9.5)],              72),  # legendary
    ("Cantonments Road Waakye",       5.573, -0.175, 0.3, [(7.0, 9.5)],              58),
    ("Kojo Thompson Rd Accra Central",5.554, -0.204, 0.4, [(7.0, 9.5)],              66),  # peak 07:30-09:30
    ("Agbogbloshie Waakye Spot",      5.556, -0.231, 0.3, [(7.0, 9.5)],              60),
    ("Lapaz Waakye Corner",           5.609, -0.243, 0.3, [(7.0, 9.5)],              52),
    ("Madina Canteen Row",            5.682, -0.169, 0.3, [(7.0, 9.5),(12.0,14.0)],  55),
    ("Achimota Market Food",          5.639, -0.237, 0.4, [(7.0, 9.5),(12.0,14.0)],  52),
    ("Darkuman Junction Chop",        5.584, -0.242, 0.3, [(7.0, 9.5),(12.0,14.0)],  44),
    ("Ashaiman Market Food",          5.698,  0.031, 0.4, [(7.0, 9.5),(12.0,14.0)],  50),
    ("Dansoman Market Food",          5.546, -0.253, 0.4, [(7.0, 9.5),(12.0,14.0)],  46),

    # ── MIDDAY BUSH CANTEEN LUNCH WAVE (11:30-13:30, 12-min kitchen prep buffer)
    ("Shiashie Market Junction",      5.608, -0.166, 0.4, [(11.5, 13.5)],            68),  # corporate lunch
    ("East Legon Main Road Canteen",  5.637, -0.158, 0.4, [(11.5, 13.5)],            64),
    ("North Ridge Ministries Chop",   5.580, -0.195, 0.4, [(11.5, 13.5)],            62),
    ("Circle Chop Bar Cluster",       5.571, -0.222, 0.5, [(7.0,9.5),(11.5,13.5),(18.0,21.0)], 65),
    ("Makola Market Canteens",        5.550, -0.206, 0.4, [(7.0, 9.5),(11.5,13.5)],  66),
    ("Kaneshie Market Chop",          5.556, -0.244, 0.4, [(7.0, 9.5),(11.5,13.5)],  60),
    ("Tema Comm 5 Canteens",          5.673,  0.013, 0.4, [(7.0, 9.5),(11.5,13.5)],  46),
    ("Adabraka Canteen Row",          5.562, -0.212, 0.3, [(11.5, 13.5),(18.0,21.0)],42),
    ("Pig Farm Jct Chop",             5.580, -0.230, 0.3, [(11.5, 13.5)],             36),

    # ── NIGHT-MARKET STREET FOOD WAVE (20:00-23:00, active 18:00-03:00)
    ("Osu Oxford St Night Market",    5.564, -0.178, 0.5, [(18.0, 23.0)],            75),  # peak 20-23
    ("G&G Special Waakye (Osu)",      5.568, -0.177, 0.2, [(18.0, 23.0)],            70),  # legendary
    ("Osu Blue Gate Night Stalls",    5.562, -0.175, 0.3, [(18.0, 23.0)],            68),
    ("Labadi Market Evening Chop",    5.555, -0.148, 0.3, [(11.5,13.5),(18.0,21.0)], 40),
    ("Teshie Chop Bars (Evening)",    5.583, -0.107, 0.4, [(18.0, 21.0)],            40),
    ("Bubuashie Evening Chop",        5.577, -0.249, 0.3, [(18.0, 21.0)],            38),
    ("Osu Canteens (Dinner Run)",     5.565, -0.178, 0.4, [(11.5,13.5),(18.0,21.0)], 46),
]

# ──────────────────────────────────────────────────────────────────────────────
# MEGA-CHURCH & HIGH-DENSITY EVENT SPATIAL WAVES  (v4.0)
# Synchronized exit rushes from Accra's largest worship centres + stadium events.
#
# windows format:
#   {"days": [0-6], "h_start": float, "h_end": float, "multiplier": float,
#    "label": str, "crosses_midnight": bool}
#   crosses_midnight=True → h_float >= h_start OR h_float < (h_end % 24)
#
# spintex_friction: True → Action Chapel triggers Spintex road gridlock bonus
# independence events handled via date check in _megachurch_event_boost
# ──────────────────────────────────────────────────────────────────────────────
MEGACHURCH_EVENT_ZONES = [
    {
        "name": "Perez Chapel International — The Perez Dome, Dzorwulu",
        "lat": 5.602, "lng": -0.186,
        "radius_km": 1.2,
        "capacity": 14000,
        "windows": [
            # Sunday bimodal dismissal
            {"days": [6], "h_start": 8.25,  "h_end": 9.0,
             "multiplier": 5.0, "label": "1st Service End", "crosses_midnight": False},
            {"days": [6], "h_start": 11.25, "h_end": 12.5,
             "multiplier": 6.0, "label": "2nd Service End", "crosses_midnight": False},
            # Friday Night Vigil 22:00-01:00 (+400% = 5x)
            {"days": [4], "h_start": 22.0,  "h_end": 25.0,
             "multiplier": 5.0, "label": "Friday Night Vigil", "crosses_midnight": True},
            # Saturday early morning vigil overflow (covers 00:00-01:00)
            {"days": [5], "h_start": 0.0,   "h_end": 1.0,
             "multiplier": 4.0, "label": "Vigil Overflow Saturday", "crosses_midnight": False},
        ],
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
    {
        "name": "Action Chapel International — Impact Arena, Spintex Road",
        "lat": 5.627, "lng": -0.103,
        "radius_km": 1.5,
        "capacity": 30000,
        "windows": [
            # Sunday bimodal dismissal
            {"days": [6], "h_start": 8.5,  "h_end": 9.5,
             "multiplier": 7.0, "label": "Sunday 1st Dismissal", "crosses_midnight": False},
            {"days": [6], "h_start": 10.5, "h_end": 11.5,
             "multiplier": 7.0, "label": "Sunday 2nd Dismissal", "crosses_midnight": False},
            # Friday Prayer Encounter 19:30-21:30
            {"days": [4], "h_start": 19.5, "h_end": 21.5,
             "multiplier": 4.0, "label": "Friday Prayer Encounter", "crosses_midnight": False},
        ],
        "spintex_friction": True,          # Spintex road gridlock during all windows
        "spintex_friction_penalty": 0.70,  # 70% speed degradation on Spintex during events
    },
    {
        "name": "ICGC Christ Temple — Abossey Okai Linked Campus",
        "lat": 5.556, "lng": -0.227,
        "radius_km": 0.8,
        "capacity": 8000,
        "windows": [
            # Sunday primary dismissal
            {"days": [6], "h_start": 9.25, "h_end": 10.5,
             "multiplier": 4.5, "label": "Sunday Dismissal", "crosses_midnight": False},
            # Thursday midweek corporate prayer spike
            {"days": [3], "h_start": 12.0, "h_end": 13.5,
             "multiplier": 2.0, "label": "Thursday Midweek Prayer", "crosses_midnight": False},
        ],
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
    {
        "name": "Black Star Square & Accra Sports Stadium",
        "lat": 5.548, "lng": -0.196,
        "radius_km": 1.0,
        "capacity": 40000,
        "windows": [
            # Weekend concert closing slots — +500-800% → multiplier 7-9x
            {"days": [5, 6], "h_start": 21.0, "h_end": 23.0,
             "multiplier": 9.0, "label": "Weekend Concert Exit Surge", "crosses_midnight": False},
        ],
        # Independence Day calendar events handled separately in _megachurch_event_boost
        "independence_parade": {
            "month": 3, "day": 6,
            "windows": [(10.0, 13.0)],
            "multiplier": 9.0,    # +500-800% → 9x for 30,000+ synchronized exit
            "label": "Independence Parade Exit",
        },
        "independence_run": {
            "month": 3, "day": 7,
            "windows": [(6.5, 10.0)],
            "multiplier": 8.0,
            "label": "Independence Day Run Dispersal",
        },
        "spintex_friction": False,
        "spintex_friction_penalty": 0.0,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class GridCell:
    grid_lat: float
    grid_lng: float
    places: list = field(default_factory=list)
    base_weight: float = 0.0
    demand_score: float = 0.0
    surge_probability: float = 0.0
    checkout_eta_min: Optional[float] = None
    prep_buffer_min: float = 0.0
    is_hotspot: bool = False
    demand_velocity: float = 0.0    # rate of score increase (acceleration signal)

    @property
    def centroid(self):
        return (self.grid_lat + 0.0005, self.grid_lng + 0.0005)

    def __repr__(self):
        return (f"GridCell({self.grid_lat},{self.grid_lng} | "
                f"score={self.demand_score:.1f} | surge={self.surge_probability:.2f})")


@dataclass
class RiderTelemetry:
    lat: float
    lng: float
    speed_kmh: float
    heading_deg: float
    has_active_delivery: bool = False
    dropoff_lat: Optional[float] = None
    dropoff_lng: Optional[float] = None
    fuel_level_pct: float = 100.0


@dataclass
class DriftVector:
    target_lat: float
    target_lng: float
    bearing_deg: float
    distance_km: float
    tta_min: float
    expected_yield_ghs: float
    confidence: float
    action: str      # "MOVE" | "HOLD" | "LEAPFROG" | "ARBITRAGE" | "WAYBILL"
    reason: str


@dataclass
class HotSpot:
    lat: float
    lng: float
    radius_km: float
    demand_score: float
    surge_probability: float
    checkout_eta_min: float
    category_mix: dict
    label: str
    acceleration_band: str   # "EMERGING" | "PEAKING" | "DECLINING"


@dataclass
class BoosterOutput:
    timestamp: str
    rider: dict
    hold_recommended: bool
    hold_reason: str
    hotspots: list
    primary_vector: Optional[dict]
    leapfrog_vector: Optional[dict]
    arbitrage_alert: Optional[dict]
    waybill_alert: Optional[dict]
    weather_advisory: Optional[dict]
    corporate_arbitrage: Optional[dict]     # v4.0 — corporate landing zone routing
    grid_stats: dict
    next_poll_interval_seconds: int


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — SPATIAL UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bearing_deg(lat1, lng1, lat2, lng2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlng = math.radians(lng2 - lng1)
    x = math.sin(dlng) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlng)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def destination_point(lat, lng, bearing_deg_val, distance_km):
    R = EARTH_RADIUS_KM
    d = distance_km / R
    b = math.radians(bearing_deg_val)
    phi1 = math.radians(lat)
    lam1 = math.radians(lng)
    phi2 = math.asin(math.sin(phi1) * math.cos(d) + math.cos(phi1) * math.sin(d) * math.cos(b))
    lam2 = lam1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(phi1),
                              math.cos(d) - math.sin(phi1) * math.sin(phi2))
    return math.degrees(phi2), math.degrees(lam2)


def grid_key(lat, lng) -> tuple:
    return (round(lat, GRID_RESOLUTION), round(lng, GRID_RESOLUTION))


def compass_label(deg) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(deg / 22.5) % 16]


def _hm_to_float(h: int, m: int) -> float:
    """Convert hour+minute to decimal float (e.g. 6h30m → 6.5)."""
    return h + m / 60.0


def _offset_time(hour: int, minute: int, offset_mins: int) -> tuple:
    """Advance wall-clock time by offset_mins, wrapping at midnight.
    Returns (new_hour, new_minute). Used by predictive front-runner."""
    total = hour * 60 + minute + offset_mins
    return (total // 60) % 24, total % 60


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — GRID ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class GridEngine:
    def __init__(self, places_path: str = "places.json"):
        self.cells: dict[tuple, GridCell] = {}
        self._load(places_path)

    def _load(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            places = json.load(f)
        for p in places:
            lat, lng = p["lat"], p["lng"]
            key = grid_key(lat, lng)
            if key not in self.cells:
                self.cells[key] = GridCell(grid_lat=key[0], grid_lng=key[1])
            cell = self.cells[key]
            cell.places.append(p)
            cell.base_weight += CATEGORY_DEMAND_WEIGHT.get(p.get("cat", "other"), 1)
        if self.cells:
            max_w = max(c.base_weight for c in self.cells.values()) or 1
            for c in self.cells.values():
                c.base_weight = (c.base_weight / max_w) * 100
        print(f"  [GridEngine] Indexed {len(places):,} places → {len(self.cells):,} grid cells")

    def get_cell(self, lat, lng) -> Optional[GridCell]:
        return self.cells.get(grid_key(lat, lng))

    def nearby_cells(self, lat, lng, radius_km: float) -> list:
        results = []
        dlat = radius_km / 111.0
        dlng = radius_km / (111.0 * math.cos(math.radians(lat)))
        for (glat, glng), cell in self.cells.items():
            if abs(glat - lat) <= dlat and abs(glng - lng) <= dlng:
                if haversine_km(lat, lng, glat, glng) <= radius_km:
                    results.append(cell)
        return results


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — TRAFFIC FRICTION ENGINE  (4-layer model, v3.0)
# ══════════════════════════════════════════════════════════════════════════════

class TrafficFriction:
    """
    Four-layer speed multiplier:
      Layer 1 — Bottleneck congestion (proximity + time-of-day)
      Layer 2 — Road surface quality (bikes always feel this)
      Layer 3 — Corridor constraints (ACCRA_TRAFFIC_CONSTRAINTS, minute-aware)
      Layer 4 — Pedestrian congestion zones (time-windowed density penalty)
    """

    def __init__(self):
        self.bottlenecks = BOTTLENECKS
        self.road_quality_zones = ROAD_QUALITY_ZONES
        self.corridors = ACCRA_TRAFFIC_CONSTRAINTS
        self.ped_zones = PEDESTRIAN_CONGESTION_ZONES

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _in_peak_window(h_float: float, peak_hours: list) -> bool:
        """peak_hours: list of (h_start, m_start, h_end, m_end)."""
        for h0, m0, h1, m1 in peak_hours:
            start = h0 + m0 / 60.0
            end   = h1 + m1 / 60.0
            if start <= h_float < end:
                return True
        return False

    # ── Layer 1: bottleneck congestion ───────────────────────────────────────

    def _bottleneck_penalty(self, lat: float, lng: float, hour: int) -> float:
        penalty = 0.0
        for name, blat, blng, h_start, h_end, severity in self.bottlenecks:
            dist = haversine_km(lat, lng, blat, blng)
            if dist > 3.0:
                continue
            proximity_factor = max(0.0, 1.0 - (dist / 3.0))
            in_peak = h_start <= hour < h_end
            time_factor = 1.0 if in_peak else 0.25
            impact = severity * proximity_factor * time_factor
            penalty = max(penalty, impact)
        return penalty

    # ── Layer 2: road surface quality ────────────────────────────────────────

    def road_surface_penalty(self, lat: float, lng: float) -> float:
        penalty = 0.0
        for name, rlat, rlng, radius_km, sp in self.road_quality_zones:
            dist = haversine_km(lat, lng, rlat, rlng)
            if dist > radius_km:
                continue
            proximity = max(0.0, 1.0 - (dist / radius_km))
            penalty = max(penalty, sp * proximity)
        return penalty

    def road_quality_label(self, lat: float, lng: float) -> str:
        worst_name, worst_penalty = None, 0.0
        for name, rlat, rlng, radius_km, sp in self.road_quality_zones:
            dist = haversine_km(lat, lng, rlat, rlng)
            if dist <= radius_km and sp > worst_penalty:
                worst_name, worst_penalty = name, sp
        if worst_penalty >= 0.40:
            return f"ROUGH — {worst_name} (potholed/unpaved, -{worst_penalty*100:.0f}% speed)"
        if worst_penalty >= 0.20:
            return f"DEGRADED — {worst_name} (-{worst_penalty*100:.0f}% speed)"
        return "GOOD"

    # ── Layer 3: corridor constraints ────────────────────────────────────────

    def _corridor_penalty(self, lat: float, lng: float,
                          hour: int, minute: int) -> float:
        h_float = _hm_to_float(hour, minute)
        penalty = 0.0
        for corridor_key, cfg in self.corridors.items():
            dist = haversine_km(lat, lng, cfg["lat"], cfg["lng"])
            if dist > cfg["radius_km"]:
                continue
            if not self._in_peak_window(h_float, cfg["peak_hours"]):
                continue
            proximity = max(0.0, 1.0 - (dist / cfg["radius_km"]))
            deg = cfg["speed_degradation"]
            # Tetteh Quarshie special: bump to 75% if disruption_flag active
            if cfg.get("disruption_flag") and corridor_key == "tetteh_quarshie":
                deg = cfg.get("accra_madina_degradation", deg)
            impact = deg * proximity
            penalty = max(penalty, impact)
        return penalty

    # ── Layer 4: pedestrian congestion ───────────────────────────────────────

    def _pedestrian_penalty(self, lat: float, lng: float,
                            hour: int, minute: int) -> float:
        h_float = _hm_to_float(hour, minute)
        penalty = 0.0
        for name, plat, plng, radius_km, h_start, h_end, ped_pen in self.ped_zones:
            if not (h_start <= h_float < h_end):
                continue
            dist = haversine_km(lat, lng, plat, plng)
            if dist > radius_km:
                continue
            proximity = max(0.0, 1.0 - (dist / radius_km))
            penalty = max(penalty, ped_pen * proximity)
        return penalty

    # ── Event friction info (Layer 5 — mega-church Spintex gridlock) ──────────

    def event_friction_info(self, lat: float, lng: float,
                            hour: int, minute: int, weekday: int) -> Optional[dict]:
        """
        Returns event friction data if an active mega-church/stadium event is
        generating extra gridlock near the rider's position. Does NOT modify
        speed_multiplier (avoids signature changes); instead feeds into
        primary_vector reason string and grid_stats.
        """
        h_float = _hm_to_float(hour, minute)
        for zone in MEGACHURCH_EVENT_ZONES:
            if not zone.get("spintex_friction"):
                continue
            penalty = zone.get("spintex_friction_penalty", 0.0)
            for win in zone.get("windows", []):
                if weekday not in win["days"]:
                    continue
                if win.get("crosses_midnight"):
                    h_end_norm = win["h_end"] % 24
                    in_win = h_float >= win["h_start"] or h_float < h_end_norm
                else:
                    in_win = win["h_start"] <= h_float < win["h_end"]
                if not in_win:
                    continue
                r = zone["radius_km"] + 2.0
                dist = haversine_km(lat, lng, zone["lat"], zone["lng"])
                if dist > r:
                    continue
                return {
                    "zone": zone["name"],
                    "event": win["label"],
                    "penalty": penalty,
                    "dist_km": round(dist, 2),
                }
        return None

    def corporate_time_penalty_min(self, lat: float, lng: float,
                                   hour: int, weekday: int) -> float:
        """
        Returns total non-riding overhead (gate + walk + lift) in minutes if
        the rider is within a corporate landing zone during its peak window.
        Returns 0.0 otherwise (no penalty outside zone / outside peak hours).
        """
        h_float = float(hour)
        for zone in CORPORATE_LANDING_ZONES:
            if zone.get("sunday_closed") and weekday == 6:
                continue
            dist = haversine_km(lat, lng, zone["lat"], zone["lng"])
            if dist > zone["radius_km"]:
                continue
            in_peak = any(w[0] <= h_float < w[1] for w in zone["peak_windows"])
            if not in_peak:
                continue
            walk_min = zone["walk_distance_m"] / 80.0
            return zone["gate_screening_min"] + walk_min + zone["elevator_wait_min"]
        return 0.0

    # ── Combined multiplier ───────────────────────────────────────────────────

    def speed_multiplier(self, lat: float, lng: float,
                         hour: int, minute: int = 0) -> float:
        """
        Returns multiplier 0.10–1.0.
        1.0 = free flow, 0.10 = severe gridlock + road + pedestrian congestion.
        """
        # Start from arterial baseline considering peak hours
        h_float = _hm_to_float(hour, minute)
        is_arterial_peak = (7.5 <= h_float < 9.0) or (16.5 <= h_float < 18.0)
        base = 1.0 - (ARTERIAL_PEAK_DEGRADATION * ARTERIAL_PEAK_COVERAGE
                      if is_arterial_peak else 0.0)

        penalty = (
            self._bottleneck_penalty(lat, lng, hour) +
            self.road_surface_penalty(lat, lng) +
            self._corridor_penalty(lat, lng, hour, minute) +
            self._pedestrian_penalty(lat, lng, hour, minute)
        )
        return max(0.10, base - penalty)

    def effective_speed(self, rider: RiderTelemetry, hour: int,
                        minute: int = 0) -> float:
        base = max(rider.speed_kmh, 15.0)
        return base * self.speed_multiplier(rider.lat, rider.lng, hour, minute)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — DEMAND SIMULATOR  (pre-checkout flash trigger, v3.0)
# ══════════════════════════════════════════════════════════════════════════════

class DemandSimulator:
    """
    Demand signal sources:
      1. Time-of-day base curve (updated for Accra reality)
      2. Shadow Matrix: 27 offline/WhatsApp food zones
      3. B2B Wholesale injection (day-of-week aware: Makola/Kantamanto/Abossey Okai)
      4. Platform API cart-spike injection (simulate_hotspots)
      5. AMA Clamp Risk Modifier (narrow alley de-boost on vehicle-hostile zones)
    """

    # Updated time-of-day demand curve (Accra ground truth)
    HOUR_CURVE = {
        0: 0.2,  1: 0.1,  2: 0.1,  3: 0.1,  4: 0.2,  5: 0.3,
        6: 0.5,  7: 0.8,  8: 1.0,  9: 0.9, 10: 0.7, 11: 1.1,
        12: 1.5, 13: 1.6, 14: 1.1, 15: 0.9, 16: 1.0, 17: 1.3,
        18: 1.7, 19: 1.8, 20: 1.5, 21: 1.2, 22: 0.8, 23: 0.5,
    }

    def __init__(self, grid: GridEngine, seed: int = None):
        self.grid = grid
        self.shadow_matrix = SHADOW_MATRIX
        self.b2b_zones = B2B_WHOLESALE_ZONES
        self.megachurch_zones = MEGACHURCH_EVENT_ZONES
        if seed is not None:
            random.seed(seed)

    def _time_multiplier(self, hour: int) -> float:
        return self.HOUR_CURVE.get(hour, 0.3)

    def _prep_buffer(self, cell: GridCell) -> float:
        cats = {p.get("cat", "other") for p in cell.places}
        max_buf = 0.0
        for cat in cats:
            if cat in INSTANT_CATEGORIES:
                continue
            if cat == "food":
                lo, hi = FUFU_LIGHTSOUP_BUFFER
            else:
                lo, hi = KITCHEN_PREP_BUFFER.get(cat, (2, 4))
            max_buf = max(max_buf, random.uniform(lo, hi))
        return max_buf

    def _shadow_boost(self, hour: int, minute: int = 0) -> list:
        h_float = _hm_to_float(hour, minute)
        spikes = []
        for name, slat, slng, radius_km, windows, intensity in self.shadow_matrix:
            for w_start, w_end in windows:
                if w_start <= h_float < w_end:
                    jitter = random.uniform(0.88, 1.12)
                    spikes.append((slat, slng, intensity * jitter, radius_km, name))
                    break
        return spikes

    def _b2b_boost(self, hour: int, minute: int, weekday: int) -> list:
        """
        Inject B2B wholesale demand for Makola, Kantamanto, and Abossey Okai.
        Respects day-of-week weights and primary/secondary dispatch windows.
        """
        h_float = _hm_to_float(hour, minute)
        spikes = []
        for zone in self.b2b_zones:
            day_w = zone["day_weights"].get(weekday, 0.5)
            if day_w < 0.3:
                continue  # closed or negligible
            p0, p1 = zone["primary_window"]
            s0, s1 = zone["secondary_window"]
            in_window = (p0 <= h_float < p1) or (s0 <= h_float < s1)
            if not in_window:
                continue
            intensity = zone["base_intensity"] * day_w
            jitter = random.uniform(0.90, 1.10)
            spikes.append((
                zone["lat"], zone["lng"],
                intensity * jitter,
                zone["radius_km"],
                zone["name"],
                zone.get("ama_clamp_risk", False),
            ))
        return spikes

    def _megachurch_event_boost(self, hour: int, minute: int,
                                weekday: int) -> list:
        """
        Inject synchronized demand spikes from mega-church dismissals and
        large-scale stadium events. Returns list of
        (lat, lng, intensity, radius_km, name, spintex_friction, friction_penalty).

        Handles windows that cross midnight (e.g., Friday Night Vigil 22:00-01:00).
        Also checks live calendar date for Independence Day events (March 6-7).
        """
        h_float = _hm_to_float(hour, minute)
        today = datetime.datetime.now()
        month, day = today.month, today.day
        spikes = []

        for zone in self.megachurch_zones:
            fired = False

            # ── Regular time windows (dismissals, vigils, prayer nights)
            for win in zone.get("windows", []):
                if weekday not in win["days"]:
                    continue
                if win.get("crosses_midnight"):
                    # Window spans midnight, e.g. 22:00-01:00
                    h_end_norm = win["h_end"] % 24
                    in_win = h_float >= win["h_start"] or h_float < h_end_norm
                else:
                    in_win = win["h_start"] <= h_float < win["h_end"]
                if not in_win:
                    continue

                capacity = zone.get("capacity", 5000)
                intensity = min(100, (capacity / 200.0) * win["multiplier"])
                jitter = random.uniform(0.90, 1.10)
                spikes.append((
                    zone["lat"], zone["lng"],
                    intensity * jitter,
                    zone["radius_km"],
                    f"{zone['name']} — {win['label']}",
                    zone.get("spintex_friction", False),
                    zone.get("spintex_friction_penalty", 0.0),
                ))
                fired = True
                break   # Only fire once per zone per call

            # ── Calendar-specific events (Independence Day parade + run)
            if not fired:
                for ev_key in ("independence_parade", "independence_run"):
                    ev = zone.get(ev_key)
                    if not ev:
                        continue
                    if ev["month"] != month or ev["day"] != day:
                        continue
                    for w0, w1 in ev["windows"]:
                        if w0 <= h_float < w1:
                            capacity = zone.get("capacity", 5000)
                            intensity = min(100, (capacity / 200.0) * ev["multiplier"])
                            spikes.append((
                                zone["lat"], zone["lng"],
                                intensity * random.uniform(0.95, 1.05),
                                zone.get("radius_km", 1.0),
                                f"{zone['name']} — {ev['label']}",
                                False, 0.0,
                            ))
                            break

        return spikes

    def inject_signals(self, hour: int, minute: int = 0,
                       simulate_hotspots=None, weekday: int = 0):
        time_mult = self._time_multiplier(hour)

        # ── Base scoring
        for cell in self.grid.cells.values():
            noise = random.uniform(0.7, 1.3)
            cell.demand_score = cell.base_weight * time_mult * noise
            cell.prep_buffer_min = self._prep_buffer(cell)
            cell.surge_probability = min(1.0, cell.demand_score / 100.0)
            cell.is_hotspot = False
            cell.checkout_eta_min = None
            cell.demand_velocity = 0.0

        # ── Shadow Matrix (offline/WhatsApp/phone-in food demand)
        for slat, slng, intensity, radius_km, sname in self._shadow_boost(hour, minute):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.5)

        # ── B2B Wholesale injection (day-of-week aware)
        for slat, slng, intensity, radius_km, sname, ama_clamp in \
                self._b2b_boost(hour, minute, weekday):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                # AMA Clamp: narrow alleys penalise bulk vehicle pickups by 40%
                if ama_clamp:
                    boost *= 0.60
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.6)

        # ── Mega-church & stadium event spatial waves (v4.0)
        for slat, slng, intensity, radius_km, sname, _evt_fric, _fric_pen in \
                self._megachurch_event_boost(hour, minute, weekday):
            for cell in self.grid.nearby_cells(slat, slng, radius_km):
                dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                boost = intensity * max(0.0, 1.0 - dist / radius_km)
                cell.demand_score = min(100, cell.demand_score + boost)
                cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                # Synchronized exits are high-velocity spikes: velocity bonus 0.9x
                cell.demand_velocity = max(cell.demand_velocity, boost * 0.9)

        # ── Platform API / cart spike injection (Bolt/Yango pre-checkout)
        if simulate_hotspots:
            for slat, slng, intensity in simulate_hotspots:
                for cell in self.grid.nearby_cells(slat, slng, 0.5):
                    dist = haversine_km(slat, slng, cell.grid_lat, cell.grid_lng)
                    boost = intensity * max(0.0, 1.0 - dist / 0.5)
                    cell.demand_score = min(100, cell.demand_score + boost)
                    cell.surge_probability = min(1.0, cell.demand_score / 100.0)
                    cell.demand_velocity = max(cell.demand_velocity, boost * 0.8)

        # ── Mark hotspots (top 5%) and assign checkout ETAs
        scores = sorted(c.demand_score for c in self.grid.cells.values())
        if scores:
            threshold = scores[int(len(scores) * 0.95)]
            for cell in self.grid.cells.values():
                if cell.demand_score >= threshold:
                    cell.is_hotspot = True
                    cell.checkout_eta_min = cell.prep_buffer_min + random.uniform(2, 5)

    def active_shadow_windows(self, hour: int, minute: int = 0) -> list:
        h_float = _hm_to_float(hour, minute)
        active = []
        for name, *_, windows, intensity in self.shadow_matrix:
            for w_start, w_end in windows:
                if w_start <= h_float < w_end:
                    active.append(name)
                    break
        return active


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — VELOCITY WAVE ENGINE  (FRONT-RUNNING OVERRIDE, v3.0)
# ══════════════════════════════════════════════════════════════════════════════

class VelocityWaveEngine:
    """
    PURE PREDICTION — NOT REACTION.

    Ghost Penalty: zones already at demand_score ≥ 85 are PENALISED by 75%.
      Rationale: mainstream platforms already display these as "surge" — they
      are crowded ghost targets. Entering them gives zero competitive edge.

    Acceleration Multiplier: zones in the 40-75 "emerging" band receive a
      1.5-2.0x bonus because the transaction explosion is imminent and no
      competitor has seen it yet.

    TTA Lock: the engine targets cells where the rider's time-to-arrival
      equals checkout_eta_min exactly — parked at the merchant's door the
      millisecond the customer presses "Order".
    """

    GHOST_SCORE_THRESHOLD = 85.0   # already peaked → ghost penalty applies
    GHOST_MULTIPLIER      = 0.25   # 75% score cut for ghost zones
    EMERGING_BAND_LOW     = 40.0   # minimum score for "emerging" classification
    EMERGING_BAND_HIGH    = 78.0   # ceiling — above this slides into ghost territory
    ACCEL_BONUS_MAX       = 2.0    # max acceleration multiplier at band centre
    ACCEL_BONUS_MIN       = 1.5    # multiplier at band entry (score=40)
    TTA_PRE_POSITION_WIN  = 3.0    # ideal: arrive 0-3 min before checkout_eta

    def __init__(self, friction: TrafficFriction):
        self.friction = friction

    def compute_tta(self, rider: RiderTelemetry, target_lat: float,
                    target_lng: float, hour: int, minute: int = 0) -> float:
        dist_km = haversine_km(rider.lat, rider.lng, target_lat, target_lng)
        eff_speed = self.friction.effective_speed(rider, hour, minute)
        return (dist_km / eff_speed) * 60.0 if eff_speed > 0 else 9999.0

    def _acceleration_band(self, score: float, velocity: float = 0.0) -> tuple:
        """
        v4.0 — Velocity Trend Validation Loop.

        Ghost Penalty (Fading Surge):
          score >= 85 AND velocity < STABLE_THRESHOLD → 75% haircut.
          Zone is dying — mainstream platforms are already swarming it.
          Entering gives ZERO competitive edge; rider is ghost-chasing.

        Sustained Cash Cow Guard:
          score >= 85 AND velocity >= STABLE_THRESHOLD → NO haircut.
          Deep market rush / downpour still actively driving transactions.
          Zone is printing money — rider should STAY or re-enter.

        Emerging Band (40-78):
          Pre-checkout explosion imminent. 1.5-2.0x multiplier locks rider
          onto the zone 3-5 minutes before competitors see the demand spike.
        """
        if score >= self.GHOST_SCORE_THRESHOLD:
            if velocity >= VELOCITY_TREND_STABLE_THRESHOLD:
                # Cash Cow Guard — velocity is stable/rising: suppress haircut
                return 1.0, "SUSTAINED_CASH_COW"
            # Fading Ghost — velocity is dropping: enforce 75% haircut
            return self.GHOST_MULTIPLIER, "GHOST (already peaked — mainstream sees it)"
        if score >= self.EMERGING_BAND_HIGH:
            # Upper transition — still building, moderate acceleration bonus
            fade = (score - self.EMERGING_BAND_HIGH) / (self.GHOST_SCORE_THRESHOLD - self.EMERGING_BAND_HIGH)
            mult = self.ACCEL_BONUS_MAX * (1.0 - fade * 0.5)
            return mult, "PEAKING"
        if score >= self.EMERGING_BAND_LOW:
            # Sweet spot: emerging pre-checkout grid
            t = (score - self.EMERGING_BAND_LOW) / (self.EMERGING_BAND_HIGH - self.EMERGING_BAND_LOW)
            mult = self.ACCEL_BONUS_MIN + t * (self.ACCEL_BONUS_MAX - self.ACCEL_BONUS_MIN)
            return mult, "EMERGING"
        # Too quiet
        return 0.70, "QUIET"

    def intercept_score(self, rider: RiderTelemetry, cell: GridCell,
                        hour: int, minute: int = 0) -> float:
        """
        Front-running composite score.

        TTA timing: ideal = arrive at checkout_eta_min (delta=0).
          • Arriving 0-3 min BEFORE peak  → full score + 10% pre-position bonus
          • Arriving 0-5 min AFTER peak   → decay (exp curve)
          • Arriving more than 5 min late → heavy decay (zone is dead)

        Ghost penalty  → zones already at peak get 75% score haircut.
        Acceleration   → emerging zones get 1.5-2.0x multiplier.
        Velocity bonus → cells with high demand_velocity (rising fast) get +20%.
        """
        if cell.checkout_eta_min is None:
            return 0.0

        tta = self.compute_tta(rider, cell.grid_lat, cell.grid_lng, hour, minute)
        delta = tta - cell.checkout_eta_min  # negative = early (good), positive = late

        # TTA timing score
        if delta <= 0 and delta >= -self.TTA_PRE_POSITION_WIN:
            # Perfect: arrive 0-3 min before checkout fires → maximum intercept
            timing_score = 1.10 + 0.033 * abs(delta)   # slight bonus for being early
        elif delta < -self.TTA_PRE_POSITION_WIN:
            # Too early — surge hasn't built yet
            timing_score = math.exp(-0.06 * (abs(delta) - self.TTA_PRE_POSITION_WIN))
        elif 0 < delta <= 5:
            # Slightly late — still catchable but losing edge
            timing_score = math.exp(-0.18 * delta)
        else:
            # More than 5 min late — zone is stale, mainstream already swarmed
            timing_score = math.exp(-0.40 * (delta - 5))

        # Ghost penalty / acceleration multiplier (velocity-aware v4.0)
        accel_mult, _ = self._acceleration_band(cell.demand_score, cell.demand_velocity)

        # Velocity (rate-of-rise) bonus: fast-rising tiles get +20%
        velocity_bonus = 1.0 + min(0.20, cell.demand_velocity / 500.0)

        return (cell.demand_score * cell.surge_probability *
                timing_score * accel_mult * velocity_bonus)

    def acceleration_band_label(self, score: float, velocity: float = 0.0) -> str:
        _, label = self._acceleration_band(score, velocity)
        return label

    def rank_cells(self, rider: RiderTelemetry, cells: list,
                   hour: int, minute: int = 0, top_n: int = 5) -> list:
        scored = []
        for cell in cells:
            s = self.intercept_score(rider, cell, hour, minute)
            if s > 0:
                scored.append((s, cell))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_n]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — LEAPFROG SEQUENTIAL ROUTER
# ══════════════════════════════════════════════════════════════════════════════

class LeapfrogRouter:
    def __init__(self, grid: GridEngine, wave: VelocityWaveEngine,
                 friction: TrafficFriction):
        self.grid = grid
        self.wave = wave
        self.friction = friction

    def next_zone(self, rider: RiderTelemetry, hour: int,
                  minute: int = 0, search_radius_km: float = 2.0) -> Optional[DriftVector]:
        if not rider.has_active_delivery or rider.dropoff_lat is None:
            return None
        nearby = self.grid.nearby_cells(rider.dropoff_lat, rider.dropoff_lng, search_radius_km)
        hotspots = [c for c in nearby if c.is_hotspot]
        if not hotspots:
            return None
        ranked = self.wave.rank_cells(rider, hotspots, hour, minute, top_n=1)
        if not ranked:
            return None
        score, best = ranked[0]
        dist = haversine_km(rider.dropoff_lat, rider.dropoff_lng,
                            best.grid_lat, best.grid_lng)
        bear = bearing_deg(rider.dropoff_lat, rider.dropoff_lng,
                           best.grid_lat, best.grid_lng)
        tta = self.wave.compute_tta(rider, best.grid_lat, best.grid_lng, hour, minute)
        expected = score * 0.08
        return DriftVector(
            target_lat=best.grid_lat,
            target_lng=best.grid_lng,
            bearing_deg=bear,
            distance_km=round(dist, 2),
            tta_min=round(tta, 1),
            expected_yield_ghs=round(expected, 2),
            confidence=round(min(0.95, score / 100.0), 2),
            action="LEAPFROG",
            reason=(f"Pre-cached next pickup zone {dist:.1f}km from your drop-off. "
                    f"ETA after delivery: {tta:.0f}min. Surge in ~{best.checkout_eta_min:.0f}min. "
                    f"Zone: {self.wave.acceleration_band_label(best.demand_score)}."),
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — RETURN TICKET ARBITRAGE
# ══════════════════════════════════════════════════════════════════════════════

class ReturnTicketArbitrage:
    def __init__(self, grid: GridEngine, wave: VelocityWaveEngine):
        self.grid = grid
        self.wave = wave

    def check(self, rider: RiderTelemetry, hour: int) -> Optional[dict]:
        if not rider.has_active_delivery or rider.dropoff_lat is None:
            return None
        for zone_name, zlat, zlng, radius_km in LOW_DENSITY_ZONES:
            dist_to_zone = haversine_km(rider.dropoff_lat, rider.dropoff_lng, zlat, zlng)
            if dist_to_zone > radius_km:
                continue
            nearby = self.grid.nearby_cells(zlat, zlng, radius_km)
            commercial = [c for c in nearby
                          if any(p.get("cat") in ("market", "mall", "office", "transport")
                                 for p in c.places)]
            if not commercial:
                continue
            best = max(commercial, key=lambda c: c.base_weight)
            return {
                "zone": zone_name,
                "alert": "RETURN_TICKET_ARBITRAGE",
                "message": (f"Drop-off is in {zone_name} — low-density outskirt. "
                            f"Pre-lock B2B/wholesale return run from "
                            f"{best.grid_lat:.4f},{best.grid_lng:.4f} "
                            f"(base demand weight {best.base_weight:.0f})."),
                "pickup_lat": best.grid_lat,
                "pickup_lng": best.grid_lng,
                "minutes_to_lock": 30,
            }
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9.5 — CORPORATE ARBITRAGE ROUTER  (v4.0)
# Intercepts corporate landing zone exits and pre-populates outbound routing
# vectors. Two activation windows:
#   Mid-Morning Legal & Consular Push  10:00-11:30
#   Pre-COB Crunch                     15:30-17:00  (Ministries cut off 16:30)
# ══════════════════════════════════════════════════════════════════════════════

class CorporateArbitrageRouter:
    """
    When a rider is within range of a corporate landing zone during either the
    Legal Push or Pre-COB Crunch windows, this router:
      1. Identifies the nearest zone and bakes in all non-riding overhead
         (gate screening + walk + lift) as a net-yield penalty.
      2. Selects the correct outbound flow (A/B/C) and centralized pickup node.
      3. Returns an actionable vector with destination, bearing, and access notes.
    """

    LEGAL_PUSH_WINDOW    = (10.0, 11.5)   # 10:00-11:30
    PRE_COB_WINDOW       = (15.5, 17.0)   # 15:30-17:00
    MINISTRIES_CUTOFF    = 16.5           # 16:30 — Ministries hard close
    ACTIVATION_RADIUS_KM = 1.5            # rider must be within this of the zone

    def check(self, rider: RiderTelemetry, hour: int, minute: int,
              weekday: int = 0) -> Optional[dict]:
        h_float = _hm_to_float(hour, minute)
        in_legal = self.LEGAL_PUSH_WINDOW[0] <= h_float < self.LEGAL_PUSH_WINDOW[1]
        in_cob   = self.PRE_COB_WINDOW[0]    <= h_float < self.PRE_COB_WINDOW[1]

        if not (in_legal or in_cob):
            return None

        best_zone = None
        best_dist = 999.0

        for zone in CORPORATE_LANDING_ZONES:
            # Sunday access denial
            if zone.get("sunday_closed") and weekday == 6:
                continue
            # Saturday reduced capacity
            sat_cap = zone.get("saturday_capacity", 1.0)
            if weekday == 5 and sat_cap <= 0:
                continue
            # Ministries cuts off at 16:30 in pre-COB window
            if in_cob and "Ministries" in zone["name"] and h_float >= self.MINISTRIES_CUTOFF:
                continue

            dist = haversine_km(rider.lat, rider.lng, zone["lat"], zone["lng"])
            if dist > self.ACTIVATION_RADIUS_KM + zone["radius_km"]:
                continue
            if dist < best_dist:
                best_dist = dist
                best_zone = zone

        if best_zone is None:
            return None

        # Determine outbound flow
        if in_legal:
            flow_key = "A"     # Legal push always routes to courts
        elif "Airport City" in best_zone["name"]:
            flow_key = "B"     # Airport City → KIA / customs
        elif "Ministries" in best_zone["name"]:
            flow_key = "A"     # Ministries → High Street courts
        else:
            flow_key = "C"     # Ridge / others → upcountry sorting

        flow = CORPORATE_OUTBOUND_FLOWS[flow_key]

        # Nearest pickup node for this flow
        flow_nodes = [n for n in CORPORATE_PICKUP_NODES if n["flow"] == flow_key]
        nearest_node = min(
            flow_nodes,
            key=lambda n: haversine_km(rider.lat, rider.lng, n["lat"], n["lng"]),
            default=None,
        ) if flow_nodes else None

        node_lat = nearest_node["lat"] if nearest_node else best_zone["lat"]
        node_lng = nearest_node["lng"] if nearest_node else best_zone["lng"]
        bear_node = bearing_deg(rider.lat, rider.lng, node_lat, node_lng)
        dist_node = haversine_km(rider.lat, rider.lng, node_lat, node_lng)

        primary_dest = flow["destinations"][0]
        bear_dest = bearing_deg(node_lat, node_lng,
                                primary_dest["lat"], primary_dest["lng"])

        # Non-riding time penalty (gate + walk + lift)
        walk_min = best_zone["walk_distance_m"] / 80.0   # 80 m/min walking pace
        total_overhead_min = (best_zone["gate_screening_min"] +
                              walk_min +
                              best_zone["elevator_wait_min"])

        # Saturday reduced capacity note
        sat_note = ""
        if weekday == 5 and best_zone.get("saturday_capacity", 1.0) < 1.0:
            sat_note = f" ⚠ Saturday — {best_zone['saturday_capacity']*100:.0f}% capacity."

        # Ministries deadline warning
        cutoff_note = ""
        if in_cob and "Ministries" in best_zone["name"]:
            mins_left = (self.MINISTRIES_CUTOFF - h_float) * 60
            cutoff_note = f" ⚠ MINISTRIES CLOSES IN {mins_left:.0f}min — execute BEFORE 16:30."

        window_type = "MID_MORNING_LEGAL_PUSH" if in_legal else "PRE_COB_CRUNCH"

        return {
            "alert": "CORPORATE_ARBITRAGE",
            "window_type": window_type,
            "zone": best_zone["name"],
            "zone_lat": best_zone["lat"],
            "zone_lng": best_zone["lng"],
            "distance_km": round(best_dist, 2),
            "flow": flow_key,
            "flow_name": flow["name"],
            "pickup_node": nearest_node["name"] if nearest_node else best_zone["name"],
            "pickup_access": nearest_node["access"] if nearest_node else "main entrance",
            "pickup_lat": node_lat,
            "pickup_lng": node_lng,
            "bearing_to_pickup": round(bear_node, 1),
            "dist_to_pickup_km": round(dist_node, 2),
            "primary_destination": primary_dest["name"],
            "dest_lat": primary_dest["lat"],
            "dest_lng": primary_dest["lng"],
            "bearing_to_dest": round(bear_dest, 1),
            "non_riding_overhead_min": round(total_overhead_min, 1),
            "gate_screening_min": best_zone["gate_screening_min"],
            "walk_distance_m": best_zone["walk_distance_m"],
            "elevator_wait_min": best_zone["elevator_wait_min"],
            "saturday_capacity_pct": int(best_zone.get("saturday_capacity", 1.0) * 100),
            "message": (
                f"[{window_type.replace('_', ' ')}] {flow['name']} → {primary_dest['name']}. "
                f"Pickup: {nearest_node['name'] if nearest_node else best_zone['name']}. "
                f"Access: {nearest_node['access'] if nearest_node else 'main entrance'}. "
                f"Non-riding overhead: {total_overhead_min:.0f}min "
                f"(gate {best_zone['gate_screening_min']}min + "
                f"walk {best_zone['walk_distance_m']}m + "
                f"lift {best_zone['elevator_wait_min']}min)."
                f"{sat_note}{cutoff_note}"
            ),
        }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — WAYBILL PIPELINE INTERCEPTOR  (exact terminal schedules, v4.0)
# ══════════════════════════════════════════════════════════════════════════════

class WaybillInterceptor:
    """
    Maps exact arrival patterns of inter-city buses to three Accra terminal
    clusters. Incorporates day-of-week demand multipliers, VIP first-come
    vs STC hourly schedules, and the Cape Coast 08:00 proxy.
    """

    MAX_INTERCEPT_RANGE_KM = 9.0
    ALERT_THRESHOLD_MIN    = 18    # trigger alert if bus arrives within N minutes

    def _is_in_window(self, h_float: float, windows: list) -> bool:
        for w0, w1 in windows:
            if w0 <= h_float < w1:
                return True
        return False

    def _is_peak_stacking(self, h_float: float, stacking: list) -> bool:
        for s0, s1 in stacking:
            if s0 <= h_float < s1:
                return True
        return False

    def _weekend_multiplier(self, h_float: float, terminal: dict,
                             weekday: int) -> float:
        if weekday in terminal.get("weekend_days", []):
            return terminal.get("weekend_multiplier", 1.0)
        return 1.0

    def _next_arrival(self, h_float: float, interval_min: int,
                      terminal: dict) -> int:
        """
        For STC_HOURLY terminals: next departure is on the hour.
        For FIRST_COME / MIXED: modulo interval.
        """
        if terminal.get("type") == "STC_HOURLY" and terminal.get("stc_mon_fri_hourly"):
            frac = h_float % 1.0
            return int((1.0 - frac) * 60)
        minute_within = int((h_float * 60) % interval_min)
        return interval_min - minute_within

    def check(self, rider: RiderTelemetry, hour: int, minute: int,
              weekday: int = 0) -> Optional[dict]:
        h_float = _hm_to_float(hour, minute)
        best_terminal = None
        best_dist = 999.0
        best_meta = {}

        for terminal in TERMINAL_SCHEDULES:
            if not self._is_in_window(h_float, terminal["windows"]):
                continue
            dist = haversine_km(rider.lat, rider.lng,
                                terminal["lat"], terminal["lng"])
            if dist > self.MAX_INTERCEPT_RANGE_KM:
                continue

            score = (1.0 / (dist + 0.01)) * self._weekend_multiplier(
                h_float, terminal, weekday)
            # Cape Coast proxy bonus at 08:00
            if terminal.get("cape_coast_proxy_hour") and \
               abs(h_float - terminal["cape_coast_proxy_hour"]) < 0.25:
                score *= 1.3

            if score > (1.0 / (best_dist + 0.01)):
                best_dist = dist
                best_terminal = terminal
                best_meta = {
                    "stacking": self._is_peak_stacking(
                        h_float, terminal.get("peak_stacking", [])),
                    "weekend_mult": self._weekend_multiplier(
                        h_float, terminal, weekday),
                    "next_arrival": self._next_arrival(
                        h_float, terminal["arrival_interval_min"], terminal),
                }

        if best_terminal is None:
            return None

        next_arrival = best_meta["next_arrival"]
        if next_arrival > self.ALERT_THRESHOLD_MIN:
            return None

        bear = bearing_deg(rider.lat, rider.lng,
                           best_terminal["lat"], best_terminal["lng"])
        stacking_note = " PEAK STACKING ACTIVE — multi-bus arrival cluster." \
            if best_meta["stacking"] else ""
        weekend_note = f" Weekend demand ×{best_meta['weekend_mult']:.1f}." \
            if best_meta["weekend_mult"] > 1.0 else ""

        return {
            "alert": "WAYBILL_INTERCEPT",
            "hub": best_terminal["name"],
            "hub_lat": best_terminal["lat"],
            "hub_lng": best_terminal["lng"],
            "distance_km": round(best_dist, 2),
            "bearing_deg": round(bear, 1),
            "next_arrival_min": next_arrival,
            "terminal_type": best_terminal["type"],
            "message": (f"{'Inter-city bus' if best_terminal['type']=='FIRST_COME' else 'STC departure'} "
                        f"at {best_terminal['name']} in ~{next_arrival}min. "
                        f"Hub is {best_dist:.1f}km {compass_label(bear)}. "
                        f"Position for wholesale multi-package waybill run.{stacking_note}{weekend_note}"),
        }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 11 — MONSOON MICRO-CLIMATE MULTIPLIER
# ══════════════════════════════════════════════════════════════════════════════

class MonsoonLayer:
    def __init__(self, grid: GridEngine):
        self.grid = grid

    def apply(self, rider: RiderTelemetry, rain_active_zones: list,
              hour: int) -> Optional[dict]:
        if not rain_active_zones:
            return None
        flooded_centres = [
            (zlat, zlng, zrad) for zname, zlat, zlng, zrad in RAIN_FLOOD_ZONES
            if zname in rain_active_zones
        ]
        if not flooded_centres:
            return None
        dry_edge_cells = []
        for zlat, zlng, zrad in flooded_centres:
            outer = self.grid.nearby_cells(zlat, zlng, zrad + 1.5)
            inner_keys = {grid_key(c.grid_lat, c.grid_lng)
                          for c in self.grid.nearby_cells(zlat, zlng, zrad)}
            for cell in outer:
                if grid_key(cell.grid_lat, cell.grid_lng) not in inner_keys:
                    cell.demand_score = min(100, cell.demand_score * 2.0)
                    cell.surge_probability = min(1.0, cell.surge_probability * 2.0)
                    dry_edge_cells.append(cell)
        if not dry_edge_cells:
            return None
        best = max(dry_edge_cells, key=lambda c: c.demand_score)
        dist = haversine_km(rider.lat, rider.lng, best.grid_lat, best.grid_lng)
        bear = bearing_deg(rider.lat, rider.lng, best.grid_lat, best.grid_lng)
        return {
            "alert": "MONSOON_DRY_EDGE",
            "flooded_zones": rain_active_zones,
            "dry_edge_lat": best.grid_lat,
            "dry_edge_lng": best.grid_lng,
            "distance_km": round(dist, 2),
            "bearing_deg": round(bear, 1),
            "demand_score": round(best.demand_score, 1),
            "message": (f"Rain blocking {', '.join(rain_active_zones)}. "
                        f"Courier deficit spiking at dry edge "
                        f"{dist:.1f}km {compass_label(bear)}. "
                        f"Move there NOW — demand multiplier 2x."),
        }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 12 — PREDICTIVE HOLD STATE MACHINE
# ══════════════════════════════════════════════════════════════════════════════

class PredictiveHoldSM:
    """Fuel-cost vs. intercept-probability gate. States: MOVE | HOLD | CHARGE."""

    def evaluate(self, rider: RiderTelemetry, primary_vector: Optional[DriftVector],
                 hour: int) -> tuple:
        if rider.fuel_level_pct < 15:
            return True, "CHARGE — fuel critically low (<15%). Locate nearest fuel station."

        if primary_vector is None:
            return True, ("HOLD — no high-confidence surge detected in your radius. "
                          "Save fuel. Stand by.")

        fuel_cost = primary_vector.distance_km * FUEL_COST_GHS_PER_KM
        net_yield = primary_vector.expected_yield_ghs - fuel_cost

        if net_yield < MIN_PROFIT_THRESHOLD:
            return True, (f"HOLD — projected net yield GHS {net_yield:.2f} after fuel is below "
                          f"threshold GHS {MIN_PROFIT_THRESHOLD:.2f}. Wait for stronger surge.")

        if primary_vector.confidence < 0.30:
            return True, (f"HOLD — surge confidence {primary_vector.confidence:.0%} too low. "
                          f"Insufficient pre-checkout signal. Stand by.")

        if 23 <= hour or hour < 5:
            return True, "HOLD — low overnight demand. Rest until 05:00."

        return False, ""


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 13 — ADAPTIVE POLLER  (kinematic battery & data optimizer)
# ══════════════════════════════════════════════════════════════════════════════

class AdaptivePoller:
    """
    STATIONARY  (speed ≤ 2 km/h or HOLD)  → 90-120s  (battery saver)
    CRUISING    (speed 3-20 km/h)          → 25-35s   (standard tracking)
    INTERCEPTING (speed > 20 + conf≥0.55)  → 8-10s    (precision mode)
    """

    STATIONARY_RANGE  = (90, 120)
    CRUISING_RANGE    = (25, 35)
    INTERCEPT_RANGE   = (8, 10)
    CONFIDENCE_THRESH = 0.55

    def compute(self, rider: RiderTelemetry, hold: bool,
                primary_vector: Optional[DriftVector]) -> int:
        if hold or rider.speed_kmh <= 2:
            return random.randint(*self.STATIONARY_RANGE)
        conf = primary_vector.confidence if primary_vector else 0.0
        if rider.speed_kmh > 20 and conf >= self.CONFIDENCE_THRESH:
            return random.randint(*self.INTERCEPT_RANGE)
        return random.randint(*self.CRUISING_RANGE)

    @staticmethod
    def label(interval: int) -> str:
        if interval >= 90:
            return "STATIONARY — battery saver mode"
        if interval <= 10:
            return "INTERCEPT — high-precision tracking"
        return "CRUISING — standard tracking"


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 14 — BOOSTER ENGINE  (main orchestrator, v4.0)
# ══════════════════════════════════════════════════════════════════════════════

class BoosterEngine:
    def __init__(self, places_path: str = "places.json"):
        print("\n  Initialising FalconFX Booster Engine v4.0...")
        self.grid      = GridEngine(places_path)
        self.friction  = TrafficFriction()
        self.demand    = DemandSimulator(self.grid)
        self.wave      = VelocityWaveEngine(self.friction)
        self.leapfrog  = LeapfrogRouter(self.grid, self.wave, self.friction)
        self.arbitrage = ReturnTicketArbitrage(self.grid, self.wave)
        self.corp_arb  = CorporateArbitrageRouter()
        self.waybill   = WaybillInterceptor()
        self.monsoon   = MonsoonLayer(self.grid)
        self.hold_sm   = PredictiveHoldSM()
        self.poller    = AdaptivePoller()
        print("  Engine ready. [Cash Cow Guard | Ghost Penalty | Mega-Church Waves | Corp Arbitrage]\n")

    def compute(self,
                rider: RiderTelemetry,
                hour: int,
                minute: int = 0,
                search_radius_km: float = 5.0,
                simulate_hotspots=None,
                rain_active_zones=None,
                weekday: int = None,
                cell_weight_overrides: dict = None) -> BoosterOutput:

        ts = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        # Infer weekday if not supplied
        if weekday is None:
            weekday = datetime.datetime.now().weekday()  # 0=Mon…6=Sun

        # ── 0. Predictive front-runner: advance wall-clock by PREDICTIVE_OFFSET_MINS
        #    Demand signals are scored against WHERE THE MARKET WILL BE, not where it is.
        #    Corp/waybill/hold logic continues to use the real clock (window-based gates).
        future_h, future_m = _offset_time(hour, minute, PREDICTIVE_OFFSET_MINS)

        # ── 1. Inject demand signals at FUTURE time (+15 min offset)
        self.demand.inject_signals(future_h, minute=future_m,
                                   simulate_hotspots=simulate_hotspots,
                                   weekday=weekday)

        # ── 1b. Apply external match telemetry weight overrides (rider feedback loop)
        if cell_weight_overrides:
            for cell in self.grid.cells.values():
                key = (round(cell.grid_lat, GRID_RESOLUTION),
                       round(cell.grid_lng, GRID_RESOLUTION))
                mod = cell_weight_overrides.get(key)
                if mod is not None and mod != 1.0:
                    cell.demand_score = max(0.0, cell.demand_score * mod)

        # ── 2. Candidate hotspot cells within rider's search radius
        nearby = self.grid.nearby_cells(rider.lat, rider.lng, search_radius_km)
        hotspot_cells = [c for c in nearby if c.is_hotspot]

        # ── 3. Rank by front-running intercept score (future time window)
        ranked = self.wave.rank_cells(rider, hotspot_cells, future_h, future_m, top_n=5)

        # ── 4. Build primary drift vector
        primary_vector = None
        ghost_penalty_applied = False
        top_band = "N/A"

        if ranked:
            top_score, top_cell = ranked[0]
            dist = haversine_km(rider.lat, rider.lng,
                                top_cell.grid_lat, top_cell.grid_lng)
            bear = bearing_deg(rider.lat, rider.lng,
                               top_cell.grid_lat, top_cell.grid_lng)
            tta  = self.wave.compute_tta(rider, top_cell.grid_lat,
                                         top_cell.grid_lng, hour, minute)
            friction_mult = self.friction.speed_multiplier(rider.lat, rider.lng,
                                                           hour, minute)
            road_label    = self.friction.road_quality_label(rider.lat, rider.lng)
            # v4.0: corporate non-riding overhead baked into yield
            corp_penalty_min = self.friction.corporate_time_penalty_min(
                top_cell.grid_lat, top_cell.grid_lng, hour, weekday)
            corp_yield_discount = (corp_penalty_min / 60.0) * 8.0  # GHS 8/hr opportunity cost
            expected_ghs  = max(0.0, top_score * 0.08 - corp_yield_discount)
            # v4.0: velocity-aware band label + Cash Cow Guard
            top_band      = self.wave.acceleration_band_label(
                top_cell.demand_score, top_cell.demand_velocity)
            ghost_penalty_applied = top_band.startswith("GHOST")
            cash_cow_active       = (top_band == "SUSTAINED_CASH_COW")

            # Event friction advisory (Action Chapel / Spintex gridlock)
            evt_friction = self.friction.event_friction_info(
                rider.lat, rider.lng, hour, minute, weekday)
            evt_note = (f" ⚡ EVENT FRICTION: {evt_friction['zone']} — "
                        f"{evt_friction['event']} gridlock ({evt_friction['penalty']*100:.0f}% "
                        f"speed loss, {evt_friction['dist_km']}km away)."
                        if evt_friction else "")
            corp_note = (f" Corp overhead baked in: {corp_penalty_min:.0f}min gate+walk+lift."
                         if corp_penalty_min > 0 else "")

            primary_vector = DriftVector(
                target_lat=top_cell.grid_lat,
                target_lng=top_cell.grid_lng,
                bearing_deg=round(bear, 1),
                distance_km=round(dist, 2),
                tta_min=round(tta, 1),
                expected_yield_ghs=round(expected_ghs, 2),
                confidence=round(min(0.99, top_score / 100.0), 2),
                action="MOVE",
                reason=(
                    f"[{top_band}] Surge wave peaking in {top_cell.checkout_eta_min:.0f}min "
                    f"at {top_cell.grid_lat:.4f},{top_cell.grid_lng:.4f}. "
                    f"Head {compass_label(bear)} — arrive in {tta:.0f}min. "
                    f"Road: {road_label}. "
                    f"Traffic friction: {(1-friction_mult)*100:.0f}% total degradation."
                    f"{evt_note}{corp_note}"
                ),
            )

        # ── 5. Hold state machine
        hold, hold_reason = self.hold_sm.evaluate(rider, primary_vector, hour)

        # ── 6. HotSpot summary objects
        hotspots_out = []
        for score, cell in ranked[:3]:
            cat_counter = defaultdict(int)
            for p in cell.places:
                cat_counter[p.get("cat", "other")] += 1
            band = self.wave.acceleration_band_label(cell.demand_score, cell.demand_velocity)
            hotspots_out.append(HotSpot(
                lat=cell.grid_lat,
                lng=cell.grid_lng,
                radius_km=0.11,
                demand_score=round(cell.demand_score, 1),
                surge_probability=round(cell.surge_probability, 2),
                checkout_eta_min=round(cell.checkout_eta_min or 0, 1),
                category_mix=dict(cat_counter),
                label=", ".join(p["name"] for p in cell.places[:2]) or "Unnamed cluster",
                acceleration_band=band,
            ))

        # ── 7. Leapfrog
        leapfrog_vector = self.leapfrog.next_zone(rider, hour, minute)

        # ── 8. Return ticket arbitrage
        arb_alert = self.arbitrage.check(rider, hour)

        # ── 9. Waybill intercept
        waybill_alert = self.waybill.check(rider, hour, minute, weekday)

        # ── 9.5. Corporate arbitrage (v4.0)
        corp_arb_alert = self.corp_arb.check(rider, hour, minute, weekday)

        # ── 10. Monsoon layer
        weather_advisory = self.monsoon.apply(rider, rain_active_zones or [], hour)

        # ── 11. Adaptive poll interval
        poll_interval = self.poller.compute(rider, hold, primary_vector)

        # ── 12. Grid stats
        active_cells   = [c for c in nearby if c.demand_score > 0]
        avg_score      = (sum(c.demand_score for c in active_cells) / len(active_cells)
                          if active_cells else 0)
        friction_here  = self.friction.speed_multiplier(rider.lat, rider.lng, hour, minute)
        road_surface   = self.friction.road_quality_label(rider.lat, rider.lng)
        shadow_active  = self.demand.active_shadow_windows(hour, minute)
        emerging_count = sum(1 for c in hotspot_cells
                             if VelocityWaveEngine.EMERGING_BAND_LOW
                             <= c.demand_score < VelocityWaveEngine.GHOST_SCORE_THRESHOLD)
        ghost_count    = sum(1 for c in hotspot_cells
                             if c.demand_score >= VelocityWaveEngine.GHOST_SCORE_THRESHOLD
                             and c.demand_velocity < VELOCITY_TREND_STABLE_THRESHOLD)
        cash_cow_count = sum(1 for c in hotspot_cells
                             if c.demand_score >= VelocityWaveEngine.GHOST_SCORE_THRESHOLD
                             and c.demand_velocity >= VELOCITY_TREND_STABLE_THRESHOLD)
        # v4.0 — megachurch event waves currently firing
        megachurch_active = self.demand._megachurch_event_boost(hour, minute, weekday)
        megachurch_names  = [s[4] for s in megachurch_active]
        event_fric = self.friction.event_friction_info(
            rider.lat, rider.lng, hour, minute, weekday)

        grid_stats = {
            "cells_scanned":              len(nearby),
            "hotspot_cells":              len(hotspot_cells),
            "avg_demand_score":           round(avg_score, 1),
            "traffic_friction_at_rider":  round(friction_here, 2),
            "effective_speed_kmh":        round(self.friction.effective_speed(rider, hour, minute), 1),
            "road_surface":               road_surface,
            "shadow_matrix_active":       shadow_active,
            "shadow_windows_firing":      len(shadow_active),
            "poll_mode":                  AdaptivePoller.label(poll_interval),
            # Front-running intelligence stats (v4.0)
            "front_running_mode":         True,
            "top_zone_band":              top_band,
            "ghost_penalty_applied":      ghost_penalty_applied,
            "cash_cow_guard_active":      cash_cow_active if ranked else False,
            "emerging_cells":             emerging_count,
            "ghost_cells_suppressed":     ghost_count,
            "cash_cow_cells":             cash_cow_count,
            # v4.0 additions
            "megachurch_waves_firing":    len(megachurch_active),
            "megachurch_events_active":   megachurch_names[:4],
            "event_friction":             event_fric,
            "weekday":                    weekday,
            # v4.1 — External Positioning Overlay / Predictive Front-Runner
            "predictive_offset_mins":     PREDICTIVE_OFFSET_MINS,
            "scored_at_future_hour":      future_h,
            "scored_at_future_min":       future_m,
            "telemetry_overrides_applied": bool(cell_weight_overrides),
        }

        return BoosterOutput(
            timestamp=ts,
            rider=asdict(rider),
            hold_recommended=hold,
            hold_reason=hold_reason,
            hotspots=[asdict(h) for h in hotspots_out],
            primary_vector=asdict(primary_vector) if primary_vector else None,
            leapfrog_vector=asdict(leapfrog_vector) if leapfrog_vector else None,
            arbitrage_alert=arb_alert,
            waybill_alert=waybill_alert,
            weather_advisory=weather_advisory,
            corporate_arbitrage=corp_arb_alert,
            grid_stats=grid_stats,
            next_poll_interval_seconds=poll_interval,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 17 — CONSOLE SIMULATION DEMO  (v4.0 — 7 scenarios)
# ══════════════════════════════════════════════════════════════════════════════

def _divider(char="═", width=72): print(char * width)
def _title(t): _divider(); print(f"  {t}"); _divider()
def _section(t): print(f"\n  ── {t} " + "─" * (65 - len(t)))


def _print_vector(label, v):
    if not v:
        print(f"    {label}: none")
        return
    print(f"    {label}:")
    print(f"      Action     : {v['action']}")
    print(f"      Target     : {v['target_lat']:.4f}, {v['target_lng']:.4f}")
    print(f"      Bearing    : {v['bearing_deg']:.1f}° ({compass_label(v['bearing_deg'])})")
    print(f"      Distance   : {v['distance_km']} km")
    print(f"      TTA        : {v['tta_min']} min")
    print(f"      Yield Est  : GHS {v['expected_yield_ghs']:.2f}")
    print(f"      Confidence : {v['confidence']:.0%}")
    print(f"      Reason     : {v['reason']}")


def _print_grid(g, poll_interval):
    print(f"    Cells scanned       : {g['cells_scanned']}")
    print(f"    Hotspot cells       : {g['hotspot_cells']}")
    print(f"    Avg demand score    : {g['avg_demand_score']}")
    print(f"    Traffic friction    : {g['traffic_friction_at_rider']:.0%} speed retained")
    print(f"    Effective speed     : {g['effective_speed_kmh']} km/h")
    print(f"    Road surface        : {g['road_surface']}")
    print(f"    Shadow windows      : {g['shadow_windows_firing']} firing")
    for sw in g['shadow_matrix_active'][:4]:
        print(f"                          • {sw}")
    print(f"    ── FRONT-RUNNING ENGINE ─────────────────────────────────")
    print(f"    Top zone band       : {g['top_zone_band']}")
    print(f"    Ghost penalty       : {'YES — competitive dead zone suppressed' if g['ghost_penalty_applied'] else 'NO — clean target'}")
    print(f"    Emerging cells      : {g['emerging_cells']}  ← pre-checkout explosion targets")
    print(f"    Ghost cells suppressed: {g['ghost_cells_suppressed']}  ← mainstream already sees these")
    print(f"    ── ADAPTIVE POLL ────────────────────────────────────────")
    print(f"    Next poll in        : {poll_interval}s")
    print(f"    Mode                : {g['poll_mode']}")


def run_simulation():
    _title("FalconFX BOOSTER v4.0 — Asymmetric Companion Weapon  |  Console Simulation")

    engine = BoosterEngine("places.json")

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 1 — Front-Running Override: Evening peak, Osu cluster
    # Demonstrates: ghost penalty suppression + emerging band targeting
    # ══════════════════════════════════════════════════════════════════════════
    print("  SCENARIO 1 — Front-Running Override: Evening Peak, Osu/Airport")
    print("  Rider: Airport Residential, 28 km/h SE. Time: 18:12 (peak dinner)")
    print("  Proves: engine ignores already-peaked ghost zones → targets EMERGING cells")
    _divider("─")

    rider1 = RiderTelemetry(
        lat=5.605, lng=-0.173, speed_kmh=28, heading_deg=135,
        has_active_delivery=False, fuel_level_pct=78,
    )
    signal_spikes = [
        (5.570, -0.170, 65),   # Osu food cluster (could be ghost)
        (5.560, -0.205, 55),   # Accra Central markets
        (5.617, -0.172, 45),   # Airport strip (emerging)
    ]
    out1 = engine.compute(
        rider=rider1, hour=18, minute=12,
        search_radius_km=5.0,
        simulate_hotspots=signal_spikes,
        rain_active_zones=[],
        weekday=0,   # Monday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider1.lat}°N, {rider1.lng}°E")
    print(f"    Speed      : {rider1.speed_kmh} km/h  |  Heading: {rider1.heading_deg}° {compass_label(rider1.heading_deg)}")
    print(f"    Fuel       : {rider1.fuel_level_pct}%")

    _section("GRID REPORT + FRONT-RUNNING INTELLIGENCE")
    _print_grid(out1.grid_stats, out1.next_poll_interval_seconds)

    _section("HOT SPOT CENTROIDS")
    for i, hs in enumerate(out1.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"eta=~{hs['checkout_eta_min']}min  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    _section("HOLD STATE MACHINE")
    status = "🛑 HOLD" if out1.hold_recommended else "✅ MOVE"
    print(f"    Recommendation: {status}")
    if out1.hold_reason:
        print(f"    Reason: {out1.hold_reason}")

    _section("PRIMARY DRIFT VECTOR")
    _print_vector("Primary", out1.primary_vector)

    _section("WAYBILL INTERCEPT")
    if out1.waybill_alert:
        print(f"    ⚡ {out1.waybill_alert['message']}")
    else:
        print("    No waybill window active.")

    _section("WEATHER ADVISORY")
    if out1.weather_advisory:
        print(f"    🌧  {out1.weather_advisory['message']}")
    else:
        print("    Clear conditions.")

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 2 — Waybill Intercept: Friday Morning, Kaneshie Terminal
    # Demonstrates: weekend_multiplier + peak stacking + STC vs first-come
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n")
    _title("SCENARIO 2 — Waybill Intercept: Friday AM, Kaneshie + Rain Displacement")
    print("  Rider: near Madina, active delivery to Adenta. Time: 07:22 Friday")
    print("  Proves: Fri multiplier on Kaneshie terminal + rain dry-edge surge")
    _divider("─")

    rider2 = RiderTelemetry(
        lat=5.680, lng=-0.168, speed_kmh=38, heading_deg=10,
        has_active_delivery=True,
        dropoff_lat=5.706, dropoff_lng=-0.163,
        fuel_level_pct=55,
    )
    out2 = engine.compute(
        rider=rider2, hour=7, minute=22,
        search_radius_km=6.0,
        simulate_hotspots=[(5.706, -0.160, 30), (5.557, -0.244, 70)],
        rain_active_zones=["Accra Central", "Kaneshie Low", "Adabraka"],
        weekday=4,   # Friday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider2.lat}°N, {rider2.lng}°E")
    print(f"    Delivering : YES → {rider2.dropoff_lat},{rider2.dropoff_lng} (Adenta)")
    print(f"    Speed      : {rider2.speed_kmh} km/h | Heading: {rider2.heading_deg}° {compass_label(rider2.heading_deg)}")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out2.grid_stats, out2.next_poll_interval_seconds)

    _section("LEAPFROG — Post Drop-off Pre-cache")
    _print_vector("Leapfrog", out2.leapfrog_vector)

    _section("RETURN TICKET ARBITRAGE")
    if out2.arbitrage_alert:
        print(f"    📦 {out2.arbitrage_alert['message']}")
    else:
        print("    No arbitrage opportunity.")

    _section("WAYBILL INTERCEPT  [FRIDAY MULTIPLIER]")
    if out2.waybill_alert:
        w = out2.waybill_alert
        print(f"    ⚡ {w['message']}")
        print(f"       Terminal type : {w['terminal_type']}")
        print(f"       Next arrival  : {w['next_arrival_min']} min")
    else:
        print("    No waybill window active.")

    _section("MONSOON DRY-EDGE ADVISORY")
    if out2.weather_advisory:
        print(f"    🌧  {out2.weather_advisory['message']}")
    else:
        print("    No rain displacement.")

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 3 — B2B Wholesale: Wednesday Makola + Kantamanto Run
    # Demonstrates: day-of-week B2B injection, AMA Clamp, pedestrian penalty
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n")
    _title("SCENARIO 3 — B2B Wholesale Wednesday: Makola + Kantamanto")
    print("  Rider: near Accra Central, 08:15 Wednesday (maximum restock day)")
    print("  Proves: B2B day_weight 1.5-1.8x, AMA Clamp Risk, pedestrian friction")
    _divider("─")

    rider3 = RiderTelemetry(
        lat=5.555, lng=-0.207, speed_kmh=18, heading_deg=45,
        has_active_delivery=False, fuel_level_pct=88,
    )
    out3 = engine.compute(
        rider=rider3, hour=8, minute=15,
        search_radius_km=3.0,
        simulate_hotspots=None,
        rain_active_zones=[],
        weekday=2,   # Wednesday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider3.lat}°N, {rider3.lng}°E  (Accra Central / Makola)")
    print(f"    Speed      : {rider3.speed_kmh} km/h")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out3.grid_stats, out3.next_poll_interval_seconds)

    _section("HOLD / MOVE")
    status3 = "🛑 HOLD" if out3.hold_recommended else "✅ MOVE"
    print(f"    Recommendation: {status3}")
    if out3.hold_reason:
        print(f"    Reason: {out3.hold_reason}")

    _section("PRIMARY DRIFT VECTOR  [B2B WHOLESALE ZONE]")
    _print_vector("Primary", out3.primary_vector)

    _section("HOT SPOT CENTROIDS  [B2B INJECTION ACTIVE]")
    for i, hs in enumerate(out3.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"band={hs['acceleration_band']}")

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 4 — Predictive HOLD: Tema outskirts, 14:30 inter-peak
    # Demonstrates: fuel cost > yield, HOLD, battery saver
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n")
    _title("SCENARIO 4 — Predictive HOLD: fuel cost > yield (Tema outskirts)")
    print("  Rider: Tema, 14:30, low inter-peak demand. Fuel 42%.")
    _divider("─")

    rider4 = RiderTelemetry(
        lat=5.673, lng=0.013, speed_kmh=5, heading_deg=270,
        has_active_delivery=False, fuel_level_pct=42,
    )
    out4 = engine.compute(
        rider=rider4, hour=14, minute=30,
        search_radius_km=4.0,
        simulate_hotspots=[],
        rain_active_zones=[],
        weekday=0,
    )

    g4 = out4.grid_stats
    _section("GRID REPORT")
    print(f"    Cells scanned     : {g4['cells_scanned']}")
    print(f"    Hotspot cells     : {g4['hotspot_cells']}")
    print(f"    Avg demand score  : {g4['avg_demand_score']}")
    print(f"    Emerging cells    : {g4['emerging_cells']} (pre-checkout targets)")
    print(f"    Ghost cells       : {g4['ghost_cells_suppressed']} (suppressed)")
    print(f"    Next poll         : {out4.next_poll_interval_seconds}s ← battery saver")
    print(f"    Mode              : {g4['poll_mode']}")

    _section("HOLD STATE MACHINE")
    status4 = "🛑 HOLD" if out4.hold_recommended else "✅ MOVE"
    print(f"    Recommendation: {status4}")
    if out4.hold_reason:
        print(f"    Reason: {out4.hold_reason}")

    if out4.primary_vector:
        _section("PRIMARY DRIFT VECTOR (low confidence — for reference)")
        _print_vector("Primary", out4.primary_vector)

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 5 — Night Market: Osu Oxford St, 21:00 (G&G + Osu Blue Gate)
    # Demonstrates: night food wave, Shadow Matrix peak 20:00-23:00
    # ══════════════════════════════════════════════════════════════════════════
    print("\n\n")
    _title("SCENARIO 5 — Osu Night Market: G&G Special + Blue Gate, 21:00")
    print("  Rider: near Labone, 21:00 Saturday. Night-market wave ACTIVE.")
    print("  Proves: Oxford St/Osu night cluster (20-23h) + Tetteh Quarshie avoided")
    _divider("─")

    rider5 = RiderTelemetry(
        lat=5.576, lng=-0.166, speed_kmh=32, heading_deg=90,
        has_active_delivery=False, fuel_level_pct=65,
    )
    out5 = engine.compute(
        rider=rider5, hour=21, minute=0,
        search_radius_km=4.0,
        simulate_hotspots=None,
        rain_active_zones=[],
        weekday=5,   # Saturday
    )

    _section("RIDER STATE")
    print(f"    Position   : {rider5.lat}°N, {rider5.lng}°E  (Labone area)")
    print(f"    Speed      : {rider5.speed_kmh} km/h | Heading: {rider5.heading_deg}° {compass_label(rider5.heading_deg)}")

    _section("GRID REPORT + FRONT-RUNNING")
    _print_grid(out5.grid_stats, out5.next_poll_interval_seconds)

    _section("NIGHT SHADOW MATRIX (active windows 21:00)")
    for sw in out5.grid_stats['shadow_matrix_active'][:8]:
        print(f"    • {sw}")

    _section("HOLD / MOVE")
    status5 = "🛑 HOLD" if out5.hold_recommended else "✅ MOVE"
    print(f"    Recommendation: {status5}")
    if out5.hold_reason:
        print(f"    Reason: {out5.hold_reason}")

    _section("PRIMARY DRIFT VECTOR  [NIGHT MARKET INTERCEPT]")
    _print_vector("Primary", out5.primary_vector)

    _section("HOT SPOT CENTROIDS  [NIGHT CLUSTER]")
    for i, hs in enumerate(out5.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"eta=~{hs['checkout_eta_min']}min  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    _section("WAYBILL")
    if out5.waybill_alert:
        print(f"    ⚡ {out5.waybill_alert['message']}")
    else:
        print("    No waybill window at 21:00.")

    # SCENARIO 6 — Mega-Church Spatial Wave: Action Chapel Sunday 2nd Dismissal
    # Rider near Spintex Rd, 10:52 Sunday (weekday=6)
    # Expected: massive demand spike injected near Action Chapel (capacity 30,000)
    #           Spintex event friction advisory fires
    #           top_zone_band reflects velocity spike from synchronized exit

    _title("SCENARIO 6 — Mega-Church Wave: Action Chapel Spintex, Sunday 10:52")

    rider6 = RiderTelemetry(
        lat=5.618, lng=-0.111,   # ~1.4km from Action Chapel Impact Arena
        speed_kmh=0.0,
        heading_deg=90.0,
        fuel_level_pct=80,
    )
    out6 = engine.compute(
        rider6, hour=10, minute=52, weekday=6,
        simulate_hotspots=None,
    )

    _section("PRIMARY VECTOR")
    if out6.primary_vector:
        pv = out6.primary_vector
        print(f"    Action  : {pv['action']}")
        print(f"    Bearing : {pv['bearing_deg']}° — {compass_label(pv['bearing_deg'])}")
        print(f"    TTA     : {pv['tta_min']}min  Dist: {pv['distance_km']}km")
        print(f"    Yield   : GHS {pv['expected_yield_ghs']}")
        print(f"    Band    : {pv['confidence']:.0%} confidence")
        print(f"    Reason  : {pv['reason'][:180]}")

    _section("GRID STATS — v4.0 Mega-Church Fields")
    g6 = out6.grid_stats
    print(f"    Top band              : {g6['top_zone_band']}")
    print(f"    Cash cow active       : {g6.get('cash_cow_guard_active')}")
    print(f"    Ghost penalty applied : {g6['ghost_penalty_applied']}")
    print(f"    Megachurch waves fire : {g6['megachurch_waves_firing']}")
    print(f"    Events active         : {g6.get('megachurch_events_active')}")
    print(f"    Event friction        : {g6.get('event_friction')}")

    _section("HOTSPOTS")
    for i, hs in enumerate(out6.hotspots, 1):
        print(f"    [{i}] {hs['lat']:.4f},{hs['lng']:.4f}  "
              f"score={hs['demand_score']:.1f}  "
              f"surge={hs['surge_probability']:.0%}  "
              f"band={hs['acceleration_band']}")
        print(f"        {hs['label']}")

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO 7 — Corporate Arbitrage: Pre-COB Crunch, Ridge, 15:45 Thursday

    _title("SCENARIO 7 — Corporate Arbitrage: Pre-COB Crunch, North Ridge, Thu 15:45")

    rider7 = RiderTelemetry(
        lat=5.576, lng=-0.193,   # inside North Ridge Corporate Enclave radius
        speed_kmh=0.0,
        heading_deg=180.0,
        fuel_level_pct=65,
    )
    out7 = engine.compute(
        rider7, hour=15, minute=45, weekday=3,  # Thursday
        simulate_hotspots=None,
    )

    _section("CORPORATE ARBITRAGE ALERT")
    if out7.corporate_arbitrage:
        ca = out7.corporate_arbitrage
        print(f"    Alert     : {ca['alert']}")
        print(f"    Window    : {ca['window_type']}")
        print(f"    Zone      : {ca['zone']}")
        print(f"    Flow      : {ca['flow']} — {ca['flow_name']}")
        print(f"    Pickup    : {ca['pickup_node']}")
        print(f"    Access    : {ca['pickup_access']}")
        print(f"    Bearing → : {ca['bearing_to_pickup']}°  ({ca['dist_to_pickup_km']}km)")
        print(f"    → Dest    : {ca['primary_destination']}")
        print(f"    Overhead  : {ca['non_riding_overhead_min']}min total")
        print(f"              : gate={ca['gate_screening_min']}min + "
              f"walk={ca['walk_distance_m']}m + lift={ca['elevator_wait_min']}min")
        print(f"    Message   : {ca['message'][:200]}")
    else:
        print("    No corporate arbitrage window active at this location/time.")
        print(f"    (rider at {rider7.lat},{rider7.lng}  hour={15}:{45}  weekday={3})")

    _section("PRIMARY VECTOR")
    if out7.primary_vector:
        pv7 = out7.primary_vector
        print(f"    Action  : {pv7['action']}")
        print(f"    Band    : {pv7['reason'][:140]}")

    _divider()
    print(f"  v4.0 Simulation complete.  Timestamp: {out1.timestamp}")
    print(f"  7 scenarios verified:")
    print(f"    1. Ghost Penalty + Acceleration Scoring (Osu/Airport evening peak)")
    print(f"    2. Waybill Intercept + Rain Displacement (Kaneshie Friday AM)")
    print(f"    3. B2B Wholesale Wednesday (Makola + Kantamanto)")
    print(f"    4. Predictive HOLD: fuel cost > yield (Tema outskirts)")
    print(f"    5. Night Market: Osu Oxford St 21:00")
    print(f"    6. ★ Mega-Church Spatial Wave: Action Chapel Spintex Sunday 10:52")
    print(f"    7. ★ Corporate Arbitrage: Pre-COB Crunch Ridge Thursday 15:45")
    print(f"  FastAPI → python3 api.py  |  POST /booster/compute")
    _divider()

    with open("booster_output_sample.json", "w") as f:
        json.dump(asdict(out1), f, indent=2, default=str)
    print(f"\n  Sample JSON → booster_output_sample.json")


if __name__ == "__main__":
    run_simulation()
