"""
pages/settings.py
-----------------
Page 5: brightness control, network info, uptime, reboot / shutdown.
Page rotation is paused while this page is active.
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
        self.brightness   = system.get_brightness()
        self._tap_targets = {}
        self._refresh_net()

    def on_enter(self):
        self.brightness = system.get_brightness()
        self._refresh_net()

    def _refresh_net(self):
        self.ip     = system.get_ip()
        self.host   = system.get_hostname()
        self.ssid   = system.get_ssid()
        self.uptime = system.get_uptime()

    def draw(self, screen):
        grid(screen, self.w, self.h, self.s)
        self._tap_targets = {}

        text(screen, self.fonts.big, "SETTINGS", self.pad, self.pad, config.COL_TEXT)

        # --- Brightness --------------------------------------------------
        by = int(self.h * 0.24)
        text(screen, self.fonts.small, "BRIGHTNESS", self.pad, by, config.COL_ACCENT)
        if self.brightness is None:
            text(screen, self.fonts.tiny, "NOT SUPPORTED ON THIS DISPLAY",
                 self.pad, by + int(22 * self.s), config.COL_DIM)
        else:
            minus = pygame.Rect(self.pad, by + int(22 * self.s),
                                int(44 * self.s), int(40 * self.s))
            plus  = pygame.Rect(self.w - self.pad - int(44 * self.s),
                                by + int(22 * self.s),
                                int(44 * self.s), int(40 * self.s))
            self._tap_targets["bright_minus"] = button(screen, self.fonts.med, "-", minus)
            self._tap_targets["bright_plus"]  = button(screen, self.fonts.med, "+", plus)
            bar = pygame.Rect(minus.right + int(12 * self.s), minus.top,
                              plus.left - minus.right - int(24 * self.s), minus.height)
            pygame.draw.rect(screen, config.COL_PANEL, bar)
            pygame.draw.rect(screen, config.COL_LINE, bar, 1)
            fillw = int(bar.width * (self.brightness / 255))
            pygame.draw.rect(screen, config.COL_ACCENT,
                             (bar.left, bar.top, fillw, bar.height))
            pct = int(self.brightness / 255 * 100)
            text(screen, self.fonts.small, f"{pct}%",
                 bar.centerx, bar.centery - int(8 * self.s),
                 config.COL_TEXT, center=True)

        # --- Network + Uptime -------------------------------------------
        ny = int(self.h * 0.50)
        text(screen, self.fonts.small, "NETWORK", self.pad, ny, config.COL_ACCENT)
        lh = int(20 * self.s)
        text(screen, self.fonts.tiny, f"HOST   {self.host}",   self.pad, ny + lh,     config.COL_TEXT)
        text(screen, self.fonts.tiny, f"IP     {self.ip}",     self.pad, ny + lh * 2, config.COL_TEXT)
        text(screen, self.fonts.tiny, f"WIFI   {self.ssid or 'wired / n/a'}",
             self.pad, ny + lh * 3, config.COL_TEXT)
        if self.uptime:
            d, h = self.uptime
            text(screen, self.fonts.tiny, f"UPTIME {d}d  {h}h",
                 self.pad, ny + lh * 4, config.COL_DIM)

        # --- Power -------------------------------------------------------
        py        = int(self.h * 0.80)
        reboot_btn = pygame.Rect(self.pad, py, int(140 * self.s), int(44 * self.s))
        shut_btn   = pygame.Rect(self.pad + int(152 * self.s), py,
                                 int(140 * self.s), int(44 * self.s))
        self._tap_targets["reboot"]   = button(screen, self.fonts.small, "REBOOT",   reboot_btn)
        self._tap_targets["shutdown"] = button(screen, self.fonts.small, "SHUTDOWN", shut_btn)
        text(screen, self.fonts.tiny, "PAGE rotation paused on this screen",
             self.w - self.pad, py + int(12 * self.s), config.COL_DIM, right=True)

    def _adjust_brightness(self, delta: int):
        if self.brightness is None:
            return
        self.brightness = max(0, min(255, self.brightness + delta))
        system.set_brightness(self.brightness)

    def handle_tap(self, pos) -> bool:
        for name, rect in self._tap_targets.items():
            if rect.collidepoint(pos):
                if name == "bright_minus":
                    self._adjust_brightness(-26)
                elif name == "bright_plus":
                    self._adjust_brightness(+26)
                elif name == "reboot":
                    system.reboot()
                elif name == "shutdown":
                    system.shutdown()
                return True
        return False

    def handle_button(self, name) -> bool:
        if name == "A":
            self._adjust_brightness(+26)
            return True
        if name == "B":
            self._adjust_brightness(-26)
            return True
        return False
