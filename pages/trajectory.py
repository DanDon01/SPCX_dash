"""
pages/trajectory.py
-------------------
Page 1: looping SpaceX-webcast-style trajectory recreation.

Visual improvements over v1:
  - Exhaust trail: deque of last 12 marker positions, fading from accent to dark.
  - Pulsing marker: sinusoidal outer ring.
  - Altitude reference lines at 50 / 100 / 150 km.
  - Launch-site tick mark on the ground baseline.
  - bisect-based _marker() replaces the O(n) linear scan.
"""

import bisect
import math
from collections import deque

import pygame

import config
from ui import grid, text, truncate
from profile import get_profile, interpolate
import data
from .base import Page

_TWO_PI = math.pi * 2


class TrajectoryPage(Page):
    name = "TRAJECTORY"

    def __init__(self, app):
        super().__init__(app)
        self.profile  = get_profile("f9_leo")
        self.mission  = data.get_next_mission()
        self.t        = 0.0
        self._pulse   = 0.0
        self._trail: deque = deque(maxlen=12)
        self._build_arc()
        # seed marker position so draw() is safe before the first update()
        self._mx, self._my = self._marker()

    def on_enter(self):
        self.t = 0.0
        self._trail.clear()
        self.mission  = data.get_next_mission()
        self._mx, self._my = self._marker()

    def _build_arc(self):
        events   = self.profile["events"]
        apex     = self.profile["apex_km"]
        loop_dur = self.profile["loop_duration"]
        margin_x = int(self.w * 0.08)
        left     = margin_x
        right    = self.w - margin_x
        baseline = int(self.h * 0.70)
        top      = int(self.h * 0.16)

        # Save geometry for altitude reference lines drawn in draw()
        self._baseline = baseline
        self._arc_top  = top
        self._arc_left = left
        self._arc_right = right
        self._apex_km  = apex

        self.arc_pts = []
        steps = 240
        for i in range(steps + 1):
            frac = i / steps
            t    = frac * loop_dur
            x    = left + (right - left) * frac
            y    = baseline - (baseline - top) * math.sin(frac * math.pi / 2)
            self.arc_pts.append((x, y, t))

        # Precomputed time list for O(log n) marker lookup
        self._arc_ts = [pt[2] for pt in self.arc_pts]

    def _marker(self):
        if not self.arc_pts:
            return 0.0, 0.0
        i = bisect.bisect_right(self._arc_ts, self.t) - 1
        i = max(0, min(i, len(self.arc_pts) - 2))
        x1, y1, t1 = self.arc_pts[i]
        x2, y2, t2 = self.arc_pts[i + 1]
        if t2 > t1:
            f = (self.t - t1) / (t2 - t1)
            return x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
        return x1, y1

    def update(self, dt: float):
        self.t      = (self.t + dt) % self.profile["loop_duration"]
        self._pulse = (self._pulse + dt * 4.0) % _TWO_PI
        self._mx, self._my = self._marker()
        self._trail.append((int(self._mx), int(self._my)))

    # --- drawing helpers --------------------------------------------------
    def _draw_arc(self, screen):
        baseline = self._baseline
        pygame.draw.line(screen, config.COL_DIM, (0, baseline), (self.w, baseline), 1)

        # Launch-site tick
        ls_x = int(self.arc_pts[0][0])
        pygame.draw.line(screen, config.COL_LINE,
                         (ls_x, baseline - int(6 * self.s)),
                         (ls_x, baseline + int(6 * self.s)), 1)
        text(screen, self.fonts.tiny, "SLC",
             ls_x, baseline + int(8 * self.s), config.COL_DIM, center=True)

        # Altitude reference lines
        for alt_km in (50, 100, 150):
            if alt_km >= self._apex_km:
                continue
            vis_frac = math.sin((alt_km / self._apex_km) * math.pi / 2)
            ref_y    = int(self._baseline - (self._baseline - self._arc_top) * vis_frac)
            pygame.draw.line(screen, config.COL_GRID,
                             (self._arc_left, ref_y), (self._arc_right, ref_y), 1)
            text(screen, self.fonts.tiny, f"{alt_km}km",
                 self._arc_left + int(4 * self.s), ref_y - int(12 * self.s), config.COL_DIM)

        # Arc segments: flown = bright, ahead = dim
        for i in range(len(self.arc_pts) - 1):
            x1, y1, t1 = self.arc_pts[i]
            x2, y2, t2 = self.arc_pts[i + 1]
            flown = t2 <= self.t or (t1 <= self.t <= t2)
            col   = config.COL_ACCENT_HOT if flown else config.COL_ARC
            wdt   = max(2, int(3 * self.s)) if flown else max(1, int(2 * self.s))
            pygame.draw.line(screen, col, (int(x1), int(y1)), (int(x2), int(y2)), wdt)

    def _draw_trail(self, screen):
        trail = list(self._trail)
        n = len(trail)
        if n < 2:
            return
        for i, (tx, ty) in enumerate(trail):
            frac   = i / (n - 1)   # 0 = oldest, 1 = newest
            r      = int(config.COL_EXHAUST[0] * frac)
            g      = int(config.COL_EXHAUST[1] * frac)
            b      = int(config.COL_EXHAUST[2] * frac)
            radius = max(1, int(frac * 5 * self.s))
            pygame.draw.circle(screen, (r, g, b), (tx, ty), radius)

    def _draw_marker(self, screen):
        mx, my = int(self._mx), int(self._my)
        # Pulsing outer ring
        pulse_r = int((8 + 3 * math.sin(self._pulse)) * self.s)
        pygame.draw.circle(screen, config.COL_LINE, (mx, my), pulse_r, 1)
        # Solid inner circles
        for r, c in ((int(6 * self.s), config.COL_ACCENT),
                     (int(3 * self.s), config.COL_TEXT)):
            pygame.draw.circle(screen, c, (mx, my), r)

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)

        self._draw_arc(screen)
        self._draw_trail(screen)
        self._draw_marker(screen)

        alt, vel, phase = interpolate(self.profile["events"], self.t)
        tt = int(self.t)
        text(screen, self.fonts.big,   f"T+{tt // 60:02d}:{tt % 60:02d}", self.pad, self.pad)
        text(screen, self.fonts.tiny,  "ALTITUDE", self.pad, self.pad + int(44 * self.s), config.COL_DIM)
        text(screen, self.fonts.med,   f"{alt:6.1f} km",   self.pad, self.pad + int(58 * self.s),  config.COL_ACCENT)
        text(screen, self.fonts.tiny,  "VELOCITY", self.pad, self.pad + int(92 * self.s), config.COL_DIM)
        text(screen, self.fonts.med,   f"{vel:6.0f} km/h", self.pad, self.pad + int(106 * self.s), config.COL_ACCENT)
        text(screen, self.fonts.med,   phase, self.w // 2, int(self.h * 0.05), config.COL_WARN, center=True)

        # Mission info strip
        m  = self.mission
        y  = int(self.h * 0.78)
        lh = int(18 * self.s)
        text(screen, self.fonts.small, m.get("mission_name", "UNKNOWN").upper(), self.pad, y)
        text(screen, self.fonts.tiny,  f"VEHICLE  {m.get('rocket', '')}", self.pad, y + lh,     config.COL_DIM)
        text(screen, self.fonts.tiny,  f"PAD      {m.get('pad', '')}",    self.pad, y + lh * 2, config.COL_DIM)
        text(screen, self.fonts.tiny,  f"ORBIT    {m.get('orbit', '')}",  self.pad, y + lh * 3, config.COL_DIM)

        rx   = self.w - self.pad
        bser = m.get("booster_serial", "UNKNOWN")
        bflt = m.get("booster_flights")
        text(screen, self.fonts.small, "BOOSTER", rx, y, config.COL_DIM, right=True)
        text(screen, self.fonts.med,   bser, rx, y + lh, config.COL_ACCENT, right=True)
        if bflt:
            text(screen, self.fonts.small, f"FLIGHT {bflt}",
                 rx, y + lh * 2 + int(4 * self.s), config.COL_WARN, right=True)
            reuse = f"{bflt - 1} PRIOR REUSES" if bflt > 1 else "NEW BOOSTER"
            text(screen, self.fonts.tiny, reuse,
                 rx, y + lh * 3 + int(6 * self.s), config.COL_DIM, right=True)
