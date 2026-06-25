"""
pages/countdown.py
------------------
Page 3: countdown to the next mission.

Visual improvements over v1:
  - Live HH:MM:SS display when launch is < 1 hour away.
  - Colour shifts from cyan -> orange -> red as launch approaches.
  - Safe .get() access on mission fields guards against malformed cache.
"""

import config
from ui import grid, text, truncate
import data
from .base import Page


class CountdownPage(Page):
    name = "COUNTDOWN"

    def __init__(self, app):
        super().__init__(app)
        self.mission = data.get_next_mission()

    def on_enter(self):
        self.mission = data.get_next_mission()

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)
        m = self.mission

        text(screen, self.fonts.med, "NEXT LAUNCH IN",
             self.w // 2, int(self.h * 0.10), config.COL_DIM, center=True)

        days, hours, mins, secs = data.time_until(m.get("net"))

        if days is None:
            big       = "TBD"
            sub       = "DATE NOT SET"
            label_col = config.COL_DIM
        elif days == 0 and hours == 0:
            # Imminent: live MM:SS display
            big       = f"{mins:02d}:{secs:02d}"
            sub       = "MIN   SEC"
            label_col = config.COL_BAD
        elif days == 0:
            # Today: HH:MM display
            big       = f"{hours:02d}:{mins:02d}"
            sub       = "HRS   MIN"
            label_col = config.COL_WARN
        else:
            big       = str(days)
            sub       = f"DAYS  {hours} HRS"
            label_col = config.COL_ACCENT

        text(screen, self.fonts.huge, big,
             self.w // 2, int(self.h * 0.20), label_col, center=True)
        text(screen, self.fonts.med, sub,
             self.w // 2, int(self.h * 0.40), config.COL_WARN, center=True)

        cy      = int(self.h * 0.56)
        lh      = int(22 * self.s)
        title_h = self.fonts.big.get_height()

        text(screen, self.fonts.big,
             m.get("mission_name", "UNKNOWN MISSION").upper(),
             self.w // 2, cy, config.COL_TEXT, center=True)

        dy = cy + title_h + int(12 * self.s)
        text(screen, self.fonts.small, m.get("rocket", ""),
             self.w // 2, dy, config.COL_DIM, center=True)
        text(screen, self.fonts.small, m.get("pad", ""),
             self.w // 2, dy + lh, config.COL_DIM, center=True)
        if m.get("payload_desc"):
            text(screen, self.fonts.tiny,
                 truncate(m["payload_desc"], 64),
                 self.w // 2, dy + lh * 2, config.COL_DIM, center=True)
