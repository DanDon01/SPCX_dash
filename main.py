"""
main.py
-------
Kiosk entry point. Manages page rotation, touch/swipe/GPIO input, page-fade
transitions, and the persistent HUD overlay (UTC clock + page dots).

Run:   python3 main.py
Quit:  Esc
"""

import signal
import sys
import time

import pygame

import config
import ui
from ui import Fonts
from input_gpio import Buttons

from pages.trajectory import TrajectoryPage
from pages.schedule   import SchedulePage
from pages.countdown  import CountdownPage
from pages.stock      import StockPage
from pages.settings   import SettingsPage


class Kiosk:
    def __init__(self):
        pygame.init()
        pygame.mouse.set_visible(False)
        pygame.display.set_caption("SPACEX HUD")
        flags = pygame.FULLSCREEN if config.FULLSCREEN else 0
        self.screen = pygame.display.set_mode(config.RESOLUTION, flags)
        self.w, self.h = config.RESOLUTION
        self.clock  = pygame.time.Clock()
        self.fonts  = Fonts(self.h)

        self.pages = [
            TrajectoryPage(self),
            SchedulePage(self),
            CountdownPage(self),
            StockPage(self),
            SettingsPage(self),
        ]
        self.index       = 0
        self.page_started = time.time()
        self.pages[self.index].on_enter()

        self._touch_start = None
        self.buttons      = Buttons(self._on_button)
        self._running     = True

        # Page-fade transition state
        _speed = 255.0 / (config.TRANSITION_MS / 1000.0)
        self._fade_surf   = pygame.Surface(config.RESOLUTION)
        self._fade_surf.fill((0, 0, 0))
        self._fade_alpha  = 0.0
        self._fade_speed  = _speed
        self._fade_target = None   # index to switch to at peak black

        # Handle SIGTERM (systemd stop) and SIGINT (Ctrl-C) gracefully
        try:
            signal.signal(signal.SIGTERM, self._on_signal)
            signal.signal(signal.SIGINT,  self._on_signal)
        except (OSError, ValueError):
            pass

    def _on_signal(self, signum, frame):
        self._running = False

    # --- page navigation --------------------------------------------------
    def goto(self, index: int):
        target = index % len(self.pages)
        if self._fade_target is not None:
            # Mid-transition: snap immediately without animation artefacts
            self.index = target
            self.page_started = time.time()
            self.pages[self.index].on_enter()
            self._fade_target = None
            self._fade_alpha  = 0.0
            return
        self._fade_target = target

    def next_page(self):
        self.goto(self.index + 1)

    def prev_page(self):
        self.goto(self.index - 1)

    @property
    def current(self):
        return self.pages[self.index]

    def _on_button(self, name: str):
        if name == "NEXT":
            self.next_page()
        elif name == "PREV":
            self.prev_page()
        else:
            self.current.handle_button(name)

    # --- input ------------------------------------------------------------
    def _handle_event(self, e) -> bool:
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                return False
            if e.key in (pygame.K_RIGHT, pygame.K_SPACE):
                self.next_page()
            elif e.key == pygame.K_LEFT:
                self.prev_page()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            self._touch_start = (e.pos, time.time())
        elif e.type == pygame.MOUSEBUTTONUP:
            self._handle_touch_release(e.pos)
        return True

    def _handle_touch_release(self, pos):
        if not self._touch_start:
            return
        (sx, _), _ = self._touch_start   # sy unused
        dx = pos[0] - sx
        self._touch_start = None

        if abs(dx) > self.w * 0.12:
            (self.next_page if dx < 0 else self.prev_page)()
            return

        if self.current.handle_tap(pos):
            return
        if pos[0] < self.w * 0.25:
            self.prev_page()
        elif pos[0] > self.w * 0.75:
            self.next_page()

    # --- fade transition --------------------------------------------------
    def _update_fade(self, dt: float):
        if self._fade_target is None:
            return
        if self._fade_alpha < 255.0:
            self._fade_alpha = min(255.0, self._fade_alpha + self._fade_speed * dt)
            if self._fade_alpha >= 255.0:
                # Peak black: switch the active page
                self.index = self._fade_target
                self.page_started = time.time()
                self.pages[self.index].on_enter()
        else:
            self._fade_alpha = max(0.0, self._fade_alpha - self._fade_speed * dt)
            if self._fade_alpha <= 0.0:
                self._fade_target = None

    def _draw_fade(self):
        if self._fade_alpha > 0:
            self._fade_surf.set_alpha(int(self._fade_alpha))
            self.screen.blit(self._fade_surf, (0, 0))

    # --- persistent HUD overlay ------------------------------------------
    def _draw_hud(self):
        if config.SHOW_CLOCK:
            ui.utc_clock(self.screen, self.fonts.tiny, self.w, self.fonts.s)
        self._draw_dots()

    def _draw_dots(self):
        n   = len(self.pages)
        r   = max(3, int(4 * self.fonts.s))
        gap = int(18 * self.fonts.s)
        x0  = self.w // 2 - (n - 1) * gap // 2
        y   = self.h - int(14 * self.fonts.s)
        for i in range(n):
            col = config.COL_ACCENT if i == self.index else config.COL_LINE
            pygame.draw.circle(self.screen, col, (x0 + i * gap, y), r)

    # --- main loop --------------------------------------------------------
    def run(self):
        last = time.time()
        while self._running:
            now = time.time()
            dt  = now - last
            last = now

            for e in pygame.event.get():
                if not self._handle_event(e):
                    self._running = False

            if (config.AUTO_ADVANCE
                    and self.current.name != "SETTINGS"
                    and self._fade_target is None
                    and now - self.page_started > config.PAGE_DURATION):
                self.next_page()

            self._update_fade(dt)

            page = self.current
            page.update(dt)
            page.draw(self.screen)
            self._draw_hud()
            self._draw_fade()

            pygame.display.flip()
            self.clock.tick(config.FPS)

        self.buttons.close()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Kiosk().run()
