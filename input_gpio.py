"""
input_gpio.py
-------------
Reads physical buttons. On a Pi it uses gpiozero; off-Pi (or if gpiozero/pins
aren't available) it silently does nothing, so the kiosk runs anywhere on
touch + keyboard alone.

Button mapping (edit BUTTON_PINS to match your wiring/HAT). The names are passed
straight to pages' handle_button(). NEXT/PREV drive page rotation; A/B/X/Y are
page-specific extras.

'BCM' numbering = Broadcom GPIO pin numbers (the GPIOxx labels), as opposed to
physical header position numbering. gpiozero uses BCM by default.
"""

# Map a logical name -> BCM GPIO pin number. Adjust to your hardware.
BUTTON_PINS = {
    "NEXT": 5,
    "PREV": 6,
    "A": 16,
    "B": 20,
    "X": 19,
    "Y": 26,
}


class Buttons:
    def __init__(self, on_press):
        """on_press: a callback taking the button name string."""
        self.on_press = on_press
        self._buttons = []
        self.available = False
        try:
            from gpiozero import Button as GPIOButton
            for name, pin in BUTTON_PINS.items():
                b = GPIOButton(pin, pull_up=True, bounce_time=0.05)
                # default-arg trick captures the current name per loop iteration
                b.when_pressed = lambda n=name: self.on_press(n)
                self._buttons.append(b)
            self.available = True
        except Exception as e:
            # not on a Pi, gpiozero missing, or pins busy - that's fine
            print(f"[gpio] buttons disabled ({e})")

    def close(self):
        for b in self._buttons:
            try:
                b.close()
            except Exception:
                pass
