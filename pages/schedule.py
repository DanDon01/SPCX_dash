"""
pages/schedule.py
-----------------
Page 2: upcoming launch schedule as a table.

Visual improvements over v1:
  - Next-launch row highlighted with a panel background.
  - Vehicle-type colour coding: Falcon 9 = cyan, Heavy = orange, Starship = green.
"""

import pygame
from datetime import datetime

import config
from ui import grid, text, truncate
import data
from .base import Page


def _fmt_date(net_iso: str) -> str:
    if not net_iso:
        return "TBD"
    try:
        dt = datetime.fromisoformat(net_iso.replace("Z", "+00:00"))
        return dt.strftime("%d %b %H:%M")
    except (ValueError, AttributeError):
        return "TBD"


def _vehicle_colour(rocket_name: str):
    name = rocket_name.lower()
    if "heavy" in name:
        return config.COL_WARN
    if "starship" in name:
        return config.COL_GOOD
    return config.COL_ACCENT


class SchedulePage(Page):
    name = "SCHEDULE"

    def __init__(self, app):
        super().__init__(app)
        self.schedule = data.get_schedule()

    def on_enter(self):
        self.schedule = data.get_schedule()

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)

        text(screen, self.fonts.big,  "LAUNCH SCHEDULE", self.pad, self.pad, config.COL_TEXT)
        text(screen, self.fonts.tiny, "UPCOMING SPACEX MISSIONS",
             self.pad, self.pad + int(40 * self.s), config.COL_DIM)

        cols_x    = [self.pad,
                     int(self.w * 0.22),
                     int(self.w * 0.52),
                     int(self.w * 0.74)]
        header_y  = int(self.h * 0.22)

        for label, cx in zip(["DATE (UTC)", "MISSION", "VEHICLE", "LOCATION"], cols_x):
            text(screen, self.fonts.tiny, label, cx, header_y, config.COL_ACCENT)
        pygame.draw.line(screen, config.COL_LINE,
                         (self.pad, header_y + int(16 * self.s)),
                         (self.w - self.pad, header_y + int(16 * self.s)), 1)

        row_y   = header_y + int(26 * self.s)
        row_h   = int(34 * self.s)
        max_rows = max(1, (int(self.h * 0.94) - row_y) // row_h)

        for i, m in enumerate(self.schedule[:max_rows]):
            # Highlight the soonest launch with a subtle panel
            if i == 0:
                highlight = pygame.Rect(
                    self.pad - int(4 * self.s), row_y - int(2 * self.s),
                    self.w - self.pad * 2 + int(8 * self.s), row_h - int(2 * self.s)
                )
                pygame.draw.rect(screen, config.COL_PANEL, highlight)
                pygame.draw.rect(screen, config.COL_LINE, highlight, 1)

            date_col = config.COL_ACCENT if i == 0 else config.COL_TEXT
            vcol     = _vehicle_colour(m.get("rocket", ""))

            text(screen, self.fonts.small, _fmt_date(m.get("net")),
                 cols_x[0], row_y, date_col)
            text(screen, self.fonts.small, truncate(m.get("mission_name", ""), 22),
                 cols_x[1], row_y, config.COL_TEXT)
            text(screen, self.fonts.small, truncate(m.get("rocket", ""), 16),
                 cols_x[2], row_y, vcol)
            text(screen, self.fonts.small, truncate(m.get("pad", ""), 18),
                 cols_x[3], row_y, config.COL_DIM)
            row_y += row_h
