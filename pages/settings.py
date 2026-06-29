"""
pages/settings.py
-----------------
Page 5: brightness control, network info, uptime, reboot / shutdown.
Page rotation is paused while this page is active.

Brightness is controlled via a full-width drag slider that calls
app.brightness.set_manual() — no direct system calls needed here.
"""

import pygame

import config
from ui import grid, text, button
import system
from .base import Page


class SettingsPage(Page):
    name = "SETTINGS"

    def __init__(self, app):
        super().__init__(app)
        self._tap_targets = {}
        self._slider_rect = None
        self._refresh_net()

    def on_enter(self):
        self._refresh_net()

    def _refresh_net(self):
        self.ip     = system.get_ip()
        self.host   = system.get_hostname()
        self.ssid   = system.get_ssid()
        self.uptime = system.get_uptime()

    def _pos_to_pct(self, x: int) -> int:
        if self._slider_rect is None:
            return 50
        return max(0, min(100, int(
            (x - self._slider_rect.left) / self._slider_rect.width * 100
        )))

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)
        self._tap_targets = {}

        text(screen, self.fonts.big, "SETTINGS", self.pad, self.pad, config.COL_TEXT)

        # --- Brightness slider -------------------------------------------
        by = int(self.h * 0.24)
        text(screen, self.fonts.small, "BRIGHTNESS", self.pad, by, config.COL_ACCENT)

        pct = self.app.brightness.get_current()
        bar = pygame.Rect(self.pad, by + int(22 * self.s),
                          self.w - self.pad * 2, int(36 * self.s))
        self._slider_rect = bar
        pygame.draw.rect(screen, config.COL_PANEL, bar)
        pygame.draw.rect(screen, config.COL_LINE, bar, 1)
        if pct > 0:
            fill_w = int(bar.width * (pct / 100))
            pygame.draw.rect(screen, config.COL_ACCENT,
                             (bar.left, bar.top, fill_w, bar.height))
        text(screen, self.fonts.small, f"{pct}%",
             bar.centerx, bar.centery - int(8 * self.s),
             config.COL_TEXT, center=True)
        text(screen, self.fonts.tiny, "drag to adjust",
             bar.centerx, bar.bottom + int(4 * self.s),
             config.COL_DIM, center=True)

        # --- Network + Uptime -------------------------------------------
        ny = int(self.h * 0.50)
        text(screen, self.fonts.small, "NETWORK", self.pad, ny, config.COL_ACCENT)
        lh = int(20 * self.s)
        text(screen, self.fonts.tiny, f"HOST   {self.host}",
             self.pad, ny + lh, config.COL_TEXT)
        text(screen, self.fonts.tiny, f"IP     {self.ip}",
             self.pad, ny + lh * 2, config.COL_TEXT)
        text(screen, self.fonts.tiny, f"WIFI   {self.ssid or 'wired / n/a'}",
             self.pad, ny + lh * 3, config.COL_TEXT)
        if self.uptime:
            d, h = self.uptime
            text(screen, self.fonts.tiny, f"UPTIME {d}d  {h}h",
                 self.pad, ny + lh * 4, config.COL_DIM)
        text(screen, self.fonts.tiny,
             f"WEB    http://{self.ip}:{config.WEB_PORT}",
             self.pad, ny + lh * 5, config.COL_ACCENT)

        # --- Power -------------------------------------------------------
        py         = int(self.h * 0.80)
        reboot_btn = pygame.Rect(self.pad, py,
                                 int(140 * self.s), int(44 * self.s))
        shut_btn   = pygame.Rect(self.pad + int(152 * self.s), py,
                                 int(140 * self.s), int(44 * self.s))
        self._tap_targets["reboot"]   = button(screen, self.fonts.small,
                                               "REBOOT",   reboot_btn)
        self._tap_targets["shutdown"] = button(screen, self.fonts.small,
                                               "SHUTDOWN", shut_btn)
        text(screen, self.fonts.tiny, "PAGE rotation paused on this screen",
             self.w - self.pad, py + int(12 * self.s), config.COL_DIM, right=True)

    def handle_tap(self, pos) -> bool:
        if self._slider_rect and self._slider_rect.collidepoint(pos):
            self.app.brightness.set_manual(self._pos_to_pct(pos[0]))
            return True
        for name, rect in self._tap_targets.items():
            if rect.collidepoint(pos):
                if name == "reboot":
                    system.reboot()
                elif name == "shutdown":
                    system.shutdown()
                return True
        return False

    def handle_drag(self, pos) -> bool:
        if self._slider_rect and self._slider_rect.collidepoint(pos):
            self.app.brightness.set_manual(self._pos_to_pct(pos[0]))
            return True
        return False

    def handle_button(self, name) -> bool:
        cur = self.app.brightness.get_current()
        if name == "A":
            self.app.brightness.set_manual(min(100, cur + 10))
            return True
        if name == "B":
            self.app.brightness.set_manual(max(0, cur - 10))
            return True
        return False
