"""
ui.py
-----
Shared drawing helpers. The grid surface is cached on first render and blitted
cheaply every frame instead of redrawing dozens of individual lines.
"""

from datetime import datetime, timezone

import pygame
import config

_grid_cache: dict = {}   # (w, h, step) -> Surface


class Fonts:
    """Resolution-scaled monospace fonts. Built once, reused everywhere."""
    def __init__(self, screen_h: int):
        s = screen_h / 480.0
        self.s = s

        def mono(px):
            return pygame.font.SysFont(
                "dejavusansmono,consolas,monospace", int(px * s)
            )
        self.huge  = mono(48)
        self.big   = mono(34)
        self.med   = mono(20)
        self.small = mono(15)
        self.tiny  = mono(12)


def text(screen, font, s, x, y, col=config.COL_TEXT,
         center=False, right=False, midbottom=False):
    """Render string s and return its Rect (useful for tap hit-testing)."""
    img  = font.render(s, True, col)
    rect = img.get_rect()
    if center:
        rect.midtop = (x, y)
    elif right:
        rect.topright = (x, y)
    elif midbottom:
        rect.midbottom = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)
    return rect


def grid(screen, w, h, s):
    """Fill the background and overlay the technical grid in one cached blit.

    The Surface is built once per (w, h, scale) combination and then reused,
    turning ~45 draw.line calls per frame into a single blit.
    """
    step = int(40 * s)
    key  = (w, h, step)
    if key not in _grid_cache:
        surf = pygame.Surface((w, h))
        surf.fill(config.COL_BG)
        for x in range(0, w, step):
            pygame.draw.line(surf, config.COL_GRID, (x, 0), (x, h))
        for y in range(0, h, step):
            pygame.draw.line(surf, config.COL_GRID, (0, y), (w, y))
        _grid_cache[key] = surf
    screen.blit(_grid_cache[key], (0, 0))


def panel(screen, rect, fill=None):
    """Bordered panel box."""
    fill = fill or config.COL_PANEL
    pygame.draw.rect(screen, fill, rect)
    pygame.draw.rect(screen, config.COL_LINE, rect, 1)


def button(screen, font, label, rect, active=False):
    """Tappable button; returns Rect for hit-testing."""
    col = config.COL_ACCENT if active else config.COL_LINE
    pygame.draw.rect(screen, config.COL_PANEL, rect)
    pygame.draw.rect(screen, col, rect, 2)
    img = font.render(label, True, config.COL_TEXT)
    screen.blit(img, img.get_rect(center=rect.center))
    return rect


def truncate(s: str, n: int) -> str:
    """Clip s to at most n characters, appending an ellipsis when trimmed."""
    return s if len(s) <= n else s[: n - 1] + "…"


def dashed_hline(screen, x1, x2, y, col, dash: int = 6):
    """Horizontal dashed line from x1 to x2 at pixel row y."""
    x = x1
    while x < x2:
        pygame.draw.line(screen, col, (x, y), (min(x + dash, x2), y), 1)
        x += dash * 2


def utc_clock(screen, font, w: int, s: float):
    """Draw a tiny UTC timestamp in the top-right corner."""
    now = datetime.now(timezone.utc).strftime("%H:%M  UTC")
    text(screen, font, now, w - int(16 * s), int(6 * s), config.COL_DIM, right=True)
