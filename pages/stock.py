"""
pages/stock.py
--------------
Page 4: SPCX stock price, day stats, and intraday chart.

Performance improvements over v1:
  - Chart polygon points cached; only recomputed when the series data changes.

Visual improvements over v1:
  - Subtle horizontal grid lines inside the chart at 25 / 50 / 75 % levels.
  - Hi / lo price labels inside the chart area.
  - `up` initialised before the price branch so the variable is always defined.
"""

import pygame

import config
from ui import grid, text, dashed_hline
import data
from .base import Page


class StockPage(Page):
    name = "STOCK"

    def __init__(self, app):
        super().__init__(app)
        self.stock         = data.get_stock()
        self._chart_cache  = None   # (series_key, pts, poly)
        self.range_24h     = True

    def on_enter(self):
        self.stock        = data.get_stock()
        self._chart_cache = None    # force rebuild on next draw

    def handle_tap(self, pos) -> bool:
        self.range_24h    = not self.range_24h
        self._chart_cache = None
        return True

    # --- chart helpers ----------------------------------------------------
    def _get_chart_pts(self, series, rect):
        """Return (pts, poly) reusing cached values when series is unchanged."""
        key = (tuple(series), rect.left, rect.right, rect.bottom, rect.height)
        if self._chart_cache and self._chart_cache[0] == key:
            return self._chart_cache[1], self._chart_cache[2]

        lo, hi = min(series), max(series)
        span   = (hi - lo) or 1.0
        n      = len(series)
        pts    = [
            (rect.left + rect.width * (i / (n - 1)),
             rect.bottom - rect.height * ((v - lo) / span))
            for i, v in enumerate(series)
        ]
        poly = pts + [(rect.right, rect.bottom), (rect.left, rect.bottom)]
        self._chart_cache = (key, pts, poly)
        return pts, poly

    def _draw_chart(self, screen, series, rect, up):
        if len(series) < 2:
            text(screen, self.fonts.small, "CHART DATA UNAVAILABLE",
                 rect.centerx, rect.centery, config.COL_DIM, center=True)
            return

        lo, hi = min(series), max(series)
        span   = (hi - lo) or 1.0
        col    = config.COL_GOOD if up else config.COL_BAD
        pts, poly = self._get_chart_pts(series, rect)

        # Subtle horizontal guide lines at 25 / 50 / 75 %
        for level in (0.25, 0.50, 0.75):
            gy = rect.bottom - int(rect.height * level)
            pygame.draw.line(screen, config.COL_GRID, (rect.left, gy), (rect.right, gy), 1)

        pygame.draw.polygon(screen, config.COL_PANEL, poly)
        pygame.draw.lines(screen, col, False, pts, max(2, int(2 * self.s)))

        # Previous close dashed line
        prev = self.stock.get("prev_close")
        if prev is not None and lo <= prev <= hi:
            py = rect.bottom - rect.height * ((prev - lo) / span)
            dashed_hline(screen, rect.left, rect.right, py, config.COL_DIM)

        # Price range labels (inside chart, top-right corner)
        text(screen, self.fonts.tiny, f"${hi:,.2f}",
             rect.right - int(4 * self.s), rect.top + int(4 * self.s),
             config.COL_DIM, right=True)
        text(screen, self.fonts.tiny, f"${lo:,.2f}",
             rect.right - int(4 * self.s), rect.bottom - int(14 * self.s),
             config.COL_DIM, right=True)

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)
        s   = self.stock
        rx  = self.w - self.pad

        text(screen, self.fonts.big,  s["ticker"], self.pad, self.pad, config.COL_TEXT)
        text(screen, self.fonts.tiny, "SPACE EXPLORATION TECH · NASDAQ",
             self.pad, self.pad + int(40 * self.s), config.COL_DIM)

        price = s.get("price")
        prev  = s.get("prev_close")
        up    = True   # sensible default when directional data is unavailable

        if price is not None:
            text(screen, self.fonts.huge, f"${price:,.2f}",
                 self.pad, int(self.h * 0.18), config.COL_TEXT)
            if prev:
                chg = price - prev
                pct = chg / prev * 100
                up  = chg >= 0
                col = config.COL_GOOD if up else config.COL_BAD
                arrow = "▲" if up else "▼"
                text(screen, self.fonts.med,
                     f"{arrow} {chg:+.2f}  ({pct:+.2f}%)",
                     self.pad, int(self.h * 0.34), col)
        else:
            text(screen, self.fonts.big, "PRICE UNAVAILABLE",
                 self.pad, int(self.h * 0.18), config.COL_DIM)

        # Day stats, right column
        ry = int(self.h * 0.18)
        lh = int(22 * self.s)
        for label, key in (("PREV CLOSE", "prev_close"),
                            ("DAY HIGH",   "day_high"),
                            ("DAY LOW",    "day_low")):
            v  = s.get(key)
            vs = f"${v:,.2f}" if isinstance(v, (int, float)) else "--"
            text(screen, self.fonts.tiny,  label, rx, ry, config.COL_DIM, right=True)
            text(screen, self.fonts.small, vs,    rx, ry + int(12 * self.s), config.COL_TEXT, right=True)
            ry += lh + int(14 * self.s)

        # Intraday chart
        chart = pygame.Rect(self.pad, int(self.h * 0.52),
                            self.w - self.pad * 2, int(self.h * 0.40))
        pygame.draw.rect(screen, config.COL_LINE, chart, 1)
        full_series  = s.get("series", [])
        series_data  = full_series[-78:] if self.range_24h else full_series
        chart_label  = "24H (tap)" if self.range_24h else "FULL (tap)"
        text(screen, self.fonts.tiny, chart_label,
             chart.left + int(6 * self.s), chart.top + int(4 * self.s), config.COL_DIM)
        self._draw_chart(screen, series_data, chart, up)

        if s.get("stale"):
            text(screen, self.fonts.tiny, "CACHED · OFFLINE",
                 rx, self.h - int(20 * self.s), config.COL_WARN, right=True)
