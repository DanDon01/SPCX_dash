"""
profile.py
----------
Flight-event timelines for Falcon 9. The renderer interpolates between these
keyframes to draw the arc and update altitude / velocity / phase readouts.

Each event: (t_seconds, altitude_km, velocity_kmh, label).
Values are representative for a Falcon 9 Starlink LEO mission — NOT live
telemetry. Swap PROFILES["f9_leo"] for a GTO / Heavy profile as needed.
"""

F9_LEO_EVENTS = [
    (0,    0.0,    0,     "LIFTOFF"),
    (12,   0.3,    350,   "PITCH OVER"),
    (62,   12.0,   1700,  "MAX-Q"),
    (145,  68.0,   8200,  "MECO"),
    (148,  72.0,   8250,  "STAGE SEP"),
    (155,  78.0,   8100,  "SES-1"),
    (165,  82.0,   7900,  "BOOSTBACK"),
    (320,  120.0,  9800,  "ENTRY BURN"),
    (380,  60.0,   4200,  "AERODYNAMIC"),
    (480,  0.5,    120,   "LANDING BURN"),
    (495,  0.0,    0,     "LANDED"),
    (510,  150.0,  24000, "SES-1 CUTOFF"),
    (540,  180.0,  26500, "SECO-1"),
    (3300, 280.0,  27000, "DEPLOY"),
]

PROFILES = {
    "f9_leo": {
        "name":          "FALCON 9 - LEO",
        "events":        F9_LEO_EVENTS,
        "loop_duration": 600,    # animation loop length in seconds
        "apex_km":       200.0,  # altitude used to scale the drawn arc
    },
}


def get_profile(profile_id="f9_leo"):
    return PROFILES.get(profile_id, PROFILES["f9_leo"])


def interpolate(events, t):
    """
    Return (altitude_km, velocity_kmh, phase_label) linearly interpolated
    between the two keyframes that bracket t.
    """
    if t <= events[0][0]:
        e = events[0]
        return e[1], e[2], e[3]
    if t >= events[-1][0]:
        e = events[-1]
        return e[1], e[2], e[3]

    for i in range(len(events) - 1):
        t0, alt0, vel0, label0 = events[i]
        t1, alt1, vel1, _      = events[i + 1]   # next label unused
        if t0 <= t < t1:
            frac = (t - t0) / (t1 - t0)
            return alt0 + (alt1 - alt0) * frac, vel0 + (vel1 - vel0) * frac, label0

    e = events[-1]
    return e[1], e[2], e[3]
