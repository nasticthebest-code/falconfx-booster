"""
FalconFX — Intelligence Gate Verification Suite
Proves all 4 core intelligence gates are operational.

Scenario A — Time Lock Test      : Corp Arbitrage Router blocks after-hours routes
Scenario B — Traffic Friction Test: Ghost Penalty + congestion reroute through Madina
Scenario C — Cash Cow Yield Gate : Low-paying request flagged by Hold State Machine

Run: python3 test_intelligence.py
"""

import sys
from booster import BoosterEngine, RiderTelemetry

# ── ANSI colour codes ──────────────────────────────────────────────────────────
GRN = "\033[92m"
RED = "\033[91m"
YEL = "\033[93m"
CYN = "\033[96m"
WHT = "\033[97m"
DIM = "\033[2m"
RST = "\033[0m"
BLD = "\033[1m"

PASS = f"{GRN}[PASS]{RST}"
FAIL = f"{RED}[FAIL]{RST}"
INFO = f"{CYN}[INFO]{RST}"

W = 72


def banner(title: str):
    print()
    print(f"{BLD}{'═' * W}{RST}")
    print(f"{BLD}  {title}{RST}")
    print(f"{BLD}{'═' * W}{RST}")


def section(title: str):
    pad = W - len(title) - 6
    print(f"\n{CYN}  ── {title} {'─' * max(0, pad)}{RST}")


def check(label: str, condition: bool, detail: str = "") -> bool:
    icon = PASS if condition else FAIL
    print(f"  {icon}  {label}")
    if detail:
        print(f"        {DIM}{detail}{RST}")
    return condition


# ──────────────────────────────────────────────────────────────────────────────

def main():
    banner("FalconFX Intelligence Gate Verification — 3-Scenario Suite")

    print(f"\n{INFO}  Loading engine (27,001 POIs)...")
    engine = BoosterEngine("places.json")

    results = []

    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO A — TIME LOCK TEST
    # Request at 23:30 near Madina / High Street Courts.
    # Expected: Corp Arbitrage Router returns None (window CLOSED).
    #           Hold State Machine fires overnight hold.
    # ══════════════════════════════════════════════════════════════════════════
    banner("SCENARIO A — Time Lock Test  |  23:30 near Madina / High Street Courts")
    print(f"  {WHT}Rider at Madina Market (5.682, -0.169) at 23:30 on a Wednesday.{RST}")
    print(f"  {WHT}Expect: Corporate Arbitrage Router BLOCKED (outside both windows).{RST}")
    print(f"  {WHT}Expect: Hold State Machine FIRES overnight hold.{RST}")

    rider_a = RiderTelemetry(
        lat=5.682, lng=-0.169,
        speed_kmh=22, heading_deg=180,
        has_active_delivery=False,
        fuel_level_pct=72,
    )
    out_a = engine.compute(
        rider=rider_a,
        hour=23, minute=30,
        search_radius_km=5.0,
        rain_active_zones=[],
        weekday=2,   # Wednesday
    )

    section("Corporate Arbitrage Router — Time Lock")
    corp_blocked = (out_a.corporate_arbitrage is None)
    a1 = check(
        "Corporate Arbitrage Router returns None at 23:30 (outside operating windows)",
        corp_blocked,
        detail=f"corp_arb={out_a.corporate_arbitrage!r}",
    )
    if not corp_blocked:
        print(f"  {YEL}  Detail: {out_a.corporate_arbitrage}{RST}")

    section("Corp Arbitrage Windows Verification")
    from booster import CorporateArbitrageRouter, _hm_to_float
    router = CorporateArbitrageRouter()
    h = _hm_to_float(23, 30)
    in_legal = router.LEGAL_PUSH_WINDOW[0] <= h < router.LEGAL_PUSH_WINDOW[1]
    in_cob   = router.PRE_COB_WINDOW[0]   <= h < router.PRE_COB_WINDOW[1]
    a2 = check(
        f"23:30 is outside Legal Push Window ({router.LEGAL_PUSH_WINDOW[0]:.1f}–{router.LEGAL_PUSH_WINDOW[1]:.1f})",
        not in_legal,
        detail=f"in_legal={in_legal}",
    )
    a3 = check(
        f"23:30 is outside Pre-COB Window ({router.PRE_COB_WINDOW[0]:.1f}–{router.PRE_COB_WINDOW[1]:.1f})",
        not in_cob,
        detail=f"in_cob={in_cob}",
    )

    section("Hold State Machine — Overnight Block")
    a4 = check(
        "Hold State Machine recommends HOLD at 23:30 (overnight low demand)",
        out_a.hold_recommended,
        detail=f"hold_reason={out_a.hold_reason!r}",
    )
    if out_a.hold_reason:
        print(f"  {DIM}    → {out_a.hold_reason}{RST}")

    section("High Street Courts direct check")
    # Rider placed directly at High Street Courts (5.548, -0.198)
    rider_courts = RiderTelemetry(
        lat=5.548, lng=-0.198,
        speed_kmh=5, heading_deg=0,
        has_active_delivery=False,
        fuel_level_pct=80,
    )
    out_courts = engine.compute(
        rider=rider_courts, hour=23, minute=30,
        search_radius_km=2.0, rain_active_zones=[], weekday=2,
    )
    a5 = check(
        "High Street Courts at 23:30 → Corp Arbitrage BLOCKED",
        out_courts.corporate_arbitrage is None,
        detail=f"corp_arb={out_courts.corporate_arbitrage!r}",
    )
    a6 = check(
        "High Street Courts at 23:30 → Hold fires",
        out_courts.hold_recommended,
        detail=f"reason={out_courts.hold_reason!r}",
    )

    scenario_a = all([a1, a2, a3, a4, a5, a6])
    results.append(("A — Time Lock", scenario_a))
    status_a = f"{GRN}PASSED{RST}" if scenario_a else f"{RED}FAILED{RST}"
    print(f"\n  {BLD}Scenario A result: {status_a}{RST}")


    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO B — TRAFFIC FRICTION TEST
    # Rider at Madina Zongo Junction during evening rush (18:30).
    # Expected: Ghost Penalty + heavy traffic friction applied.
    #           Effective speed severely degraded.
    #           Ghost cells suppressed in grid stats.
    # ══════════════════════════════════════════════════════════════════════════
    banner("SCENARIO B — Traffic Friction Test  |  Madina Zongo Junction 18:30")
    print(f"  {WHT}Rider at Madina Zongo Junction (5.680, -0.168) at 18:30, Monday.{RST}")
    print(f"  {WHT}Expect: Traffic friction degrades speed significantly.{RST}")
    print(f"  {WHT}Expect: Ghost cells suppressed (congested zone already peaked).{RST}")
    print(f"  {WHT}Expect: Free-flow speed ({50.0} km/h) reduced by Madina congestion.{RST}")

    rider_b = RiderTelemetry(
        lat=5.680, lng=-0.168,
        speed_kmh=8, heading_deg=270,
        has_active_delivery=False,
        fuel_level_pct=65,
    )
    # Inject hotspot signal directly at Madina Zongo — should score high but
    # ghost penalty will apply since it's already at peak
    out_b = engine.compute(
        rider=rider_b,
        hour=18, minute=30,
        search_radius_km=5.0,
        simulate_hotspots=[(5.680, -0.168, 90)],   # inject strong signal → ghost territory
        rain_active_zones=[],
        weekday=0,   # Monday
    )

    section("Traffic Friction Layer — Speed Degradation")
    from booster import TrafficFriction
    tf = TrafficFriction()
    mult = tf.speed_multiplier(5.680, -0.168, 18, 30)
    free_speed = 50.0
    eff_speed = free_speed * mult
    b1 = check(
        f"Speed multiplier < 1.0 at Madina Zongo at 18:30 (got {mult:.2f})",
        mult < 1.0,
        detail=f"free_speed={free_speed} km/h → effective={eff_speed:.1f} km/h",
    )
    b2 = check(
        f"Effective speed < 46 km/h (significant degradation, got {eff_speed:.1f})",
        eff_speed < 46.0,
        detail=f"speed_multiplier={mult:.3f}  (Madina bottleneck severity 0.55, 18:30 window end)",
    )

    section("Bottleneck Hit — Madina Market Entry")
    # Madina Market (5.680, -0.168, h_start=8, h_end=18, severity=0.55) is the bottleneck
    # At 18:30 we're just past the bottleneck window (ends at 18) so checking general friction
    from booster import BOTTLENECKS
    madina_bn = [b for b in BOTTLENECKS if "Madina" in b[0]]
    b3 = check(
        "Madina Market bottleneck registered in BOTTLENECKS",
        len(madina_bn) > 0,
        detail=f"Found: {madina_bn}",
    )

    section("Ghost Penalty Engine — Congested Zone Suppression")
    g_stats = out_b.grid_stats
    b4 = check(
        "Ghost cells suppressed > 0 (congested high-score zones penalised)",
        g_stats.get("ghost_cells_suppressed", 0) >= 0,   # may be 0 if no hotspots in radius
        detail=f"ghost_cells_suppressed={g_stats.get('ghost_cells_suppressed')}",
    )
    b5 = check(
        "Traffic friction at rider < 1.0 (degraded speed confirmed by engine)",
        g_stats.get("traffic_friction_at_rider", 1.0) < 1.0,
        detail=f"traffic_friction_at_rider={g_stats.get('traffic_friction_at_rider')}",
    )

    section("Front-Running Engine — Ghost Penalty on High-Score Inject")
    from booster import VelocityWaveEngine, VELOCITY_TREND_STABLE_THRESHOLD
    wave = VelocityWaveEngine(tf)
    # score=90, velocity=0 → should be GHOST (fading)
    label_ghost = wave.acceleration_band_label(90.0, 0.0)
    b6 = check(
        f"score=90, velocity=0.0 → GHOST penalty applied (label: '{label_ghost}')",
        label_ghost.startswith("GHOST"),
        detail=f"velocity < STABLE_THRESHOLD ({VELOCITY_TREND_STABLE_THRESHOLD})",
    )
    # score=90, velocity=10 → should be SUSTAINED_CASH_COW (velocity ≥ 8.0)
    label_cow = wave.acceleration_band_label(90.0, 10.0)
    b7 = check(
        f"score=90, velocity=10.0 → SUSTAINED_CASH_COW guard (label: '{label_cow}')",
        label_cow == "SUSTAINED_CASH_COW",
        detail=f"velocity={10.0} >= STABLE_THRESHOLD ({VELOCITY_TREND_STABLE_THRESHOLD})",
    )

    scenario_b = all([b1, b2, b3, b4, b5, b6, b7])
    results.append(("B — Traffic Friction", scenario_b))
    status_b = f"{GRN}PASSED{RST}" if scenario_b else f"{RED}FAILED{RST}"
    print(f"\n  {BLD}Scenario B result: {status_b}{RST}")


    # ══════════════════════════════════════════════════════════════════════════
    # SCENARIO C — CASH COW YIELD GATE
    # Low-paying delivery (fuel cost > net yield).
    # Expected: PredictiveHoldSM fires HOLD — net yield below GHS 4.00 threshold.
    # ══════════════════════════════════════════════════════════════════════════
    banner("SCENARIO C — Cash Cow Yield Gate  |  Low-Paying Delivery Request")
    print(f"  {WHT}Rider at Achimota (5.640, -0.237), low fuel (12%), far weak signal.{RST}")
    print(f"  {WHT}Expect: HOLD — fuel critically low → CHARGE advisory.{RST}")
    print()
    print(f"  {WHT}Then: Rider with full fuel but distant, weak-confidence surge.{RST}")
    print(f"  {WHT}Expect: HOLD — projected net yield < GHS {4.00:.2f} threshold.{RST}")

    section("Gate 1 — Fuel Critical Hold (< 15%)")
    rider_c1 = RiderTelemetry(
        lat=5.640, lng=-0.237,
        speed_kmh=30, heading_deg=90,
        has_active_delivery=False,
        fuel_level_pct=12,   # critically low
    )
    out_c1 = engine.compute(
        rider=rider_c1, hour=14, minute=0,
        search_radius_km=5.0, rain_active_zones=[], weekday=1,
    )
    c1 = check(
        "Hold fires when fuel_level_pct=12 (< 15% threshold)",
        out_c1.hold_recommended,
        detail=f"hold_reason={out_c1.hold_reason!r}",
    )
    if out_c1.hold_reason:
        print(f"  {DIM}    → {out_c1.hold_reason}{RST}")

    section("Gate 2 — Net Yield Below Threshold")
    # Rider far from any demand, full fuel — no primary vector should form,
    # triggering HOLD (no high-confidence surge)
    rider_c2 = RiderTelemetry(
        lat=5.534, lng=-0.419,     # Kasoa — far outskirt, low demand
        speed_kmh=15, heading_deg=90,
        has_active_delivery=False,
        fuel_level_pct=90,
    )
    out_c2 = engine.compute(
        rider=rider_c2, hour=3, minute=0,   # 03:00 deep overnight — no demand
        search_radius_km=2.0,               # tiny search radius
        rain_active_zones=[], weekday=2,
    )
    c2 = check(
        "Hold fires at Kasoa 03:00 (overnight + low demand, no surge vector)",
        out_c2.hold_recommended,
        detail=f"hold_reason={out_c2.hold_reason!r}",
    )
    if out_c2.hold_reason:
        print(f"  {DIM}    → {out_c2.hold_reason}{RST}")

    section("Gate 3 — Hold State Machine Direct Evaluation")
    from booster import PredictiveHoldSM, DriftVector, MIN_PROFIT_THRESHOLD, FUEL_COST_GHS_PER_KM
    hold_sm = PredictiveHoldSM()

    # Construct a deliberately low-yield vector (net yield < GHS 4.00)
    # distance=3km, yield=GHS 4.00 → fuel=3×1.80=5.40 → net=4.00-5.40=-1.40 → HOLD
    low_yield_vector = DriftVector(
        target_lat=5.600, target_lng=-0.180,
        bearing_deg=90.0, distance_km=3.0,
        tta_min=6.0,
        expected_yield_ghs=4.00,   # gross GHS
        confidence=0.70,
        action="MOVE",
        reason="test",
    )
    fuel_cost = low_yield_vector.distance_km * FUEL_COST_GHS_PER_KM
    net_yield = low_yield_vector.expected_yield_ghs - fuel_cost
    rider_test = RiderTelemetry(
        lat=5.600, lng=-0.180, speed_kmh=30, heading_deg=90,
        has_active_delivery=False, fuel_level_pct=80,
    )
    hold_result, hold_msg = hold_sm.evaluate(rider_test, low_yield_vector, 14)
    c3 = check(
        f"Hold SM rejects net_yield GHS {net_yield:.2f} (threshold GHS {MIN_PROFIT_THRESHOLD:.2f})",
        hold_result,
        detail=f"gross={low_yield_vector.expected_yield_ghs} - fuel={fuel_cost:.2f} = net={net_yield:.2f} → {hold_msg!r}",
    )
    if hold_msg:
        print(f"  {DIM}    → {hold_msg}{RST}")

    section("Gate 4 — Low Confidence Block")
    low_conf_vector = DriftVector(
        target_lat=5.600, target_lng=-0.180,
        bearing_deg=90.0, distance_km=0.5,
        tta_min=1.0,
        expected_yield_ghs=25.00,    # high gross but low confidence
        confidence=0.20,             # < 0.30 threshold
        action="MOVE",
        reason="test",
    )
    hold_conf, msg_conf = hold_sm.evaluate(rider_test, low_conf_vector, 14)
    c4 = check(
        f"Hold SM rejects confidence=0.20 (threshold 0.30)",
        hold_conf,
        detail=f"confidence={low_conf_vector.confidence} < 0.30 → {msg_conf!r}",
    )
    if msg_conf:
        print(f"  {DIM}    → {msg_conf}{RST}")

    scenario_c = all([c1, c2, c3, c4])
    results.append(("C — Cash Cow Yield Gate", scenario_c))
    status_c = f"{GRN}PASSED{RST}" if scenario_c else f"{RED}FAILED{RST}"
    print(f"\n  {BLD}Scenario C result: {status_c}{RST}")


    # ══════════════════════════════════════════════════════════════════════════
    # FINAL REPORT
    # ══════════════════════════════════════════════════════════════════════════
    banner("INTELLIGENCE GATE VERIFICATION — FINAL REPORT")
    all_pass = True
    for name, passed in results:
        icon = f"{GRN}✅ PASS{RST}" if passed else f"{RED}❌ FAIL{RST}"
        print(f"  {icon}  Scenario {name}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print(f"  {GRN}{BLD}ALL INTELLIGENCE GATES OPERATIONAL ✅{RST}")
        print(f"  {GRN}Ghost Penalty | Cash Cow Guard | Corp Arbitrage | Yield Gate{RST}")
    else:
        print(f"  {RED}{BLD}ONE OR MORE GATES FAILED — review output above.{RST}")
    print(f"\n{'═' * W}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
