"""
pages/base.py
-------------
Interface every page implements. The page manager calls these methods so each
page only worries about its own content.
"""


class Page:
    name = "PAGE"

    def __init__(self, app):
        self.app   = app
        self.fonts = app.fonts
        self.w     = app.w
        self.h     = app.h
        self.s     = app.fonts.s
        self.pad   = int(16 * self.s)   # standard edge padding, shared by all pages

    def on_enter(self):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        raise NotImplementedError

    def handle_tap(self, pos) -> bool:
        return False

    def handle_button(self, name) -> bool:
        return False
