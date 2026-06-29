"""
brightness.py
-------------
Backlight controller for the Adafruit 3.5" TFT (GPIO18 PWM via pigpio).
Falls back to sysfs /sys/class/backlight/*/brightness when pigpio is
unavailable or BL_PWM_PIN is None.

Night-mode schedule dims the screen between NIGHT_START_HOUR and
NIGHT_END_HOUR (midnight wrap handled). Launch-day ramp lerps base
brightness up to 100% within LAUNCH_RAMP_HOURS of the next launch.
set_manual() accepts a phone/slider override and holds it for hold_seconds
before resuming the schedule.
"""

import glob
import time

import config
import data


class Brightness:
    def __init__(self):
        self._current     = config.DAY_BRIGHTNESS
        self._manual_until = 0.0
        self._last_update  = 0.0
        self._pi           = None
        self._sysfs        = None
        self._init_hw()
        self._apply(self._current)

    # --- hardware init -------------------------------------------------------

    def _init_hw(self):
        if config.BL_PWM_PIN is not None:
            try:
                import pigpio
                pi = pigpio.pi()
                if pi.connected:
                    pi.set_PWM_frequency(config.BL_PWM_PIN, 1000)
                    pi.set_PWM_range(config.BL_PWM_PIN, 100)
                    self._pi = pi
                    return
                pi.stop()
            except Exception:
                pass
        # sysfs fallback
        paths = glob.glob("/sys/class/backlight/*/brightness")
        if paths:
            self._sysfs = paths[0]

    # --- internal helpers ----------------------------------------------------

    def _apply(self, pct: int):
        pct = max(0, min(100, int(pct)))
        self._current = pct
        if self._pi is not None:
            try:
                self._pi.set_PWM_dutycycle(config.BL_PWM_PIN, pct)
                return
            except Exception:
                pass
        if self._sysfs:
            try:
                max_path = self._sysfs.replace("brightness", "max_brightness")
                try:
                    with open(max_path) as f:
                        max_b = int(f.read().strip())
                except Exception:
                    max_b = 255
                with open(self._sysfs, "w") as f:
                    f.write(str(int(max_b * pct / 100)))
            except Exception:
                pass

    def _target(self) -> int:
        if config.NIGHT_MODE:
            h = time.localtime().tm_hour
            start, end = config.NIGHT_START_HOUR, config.NIGHT_END_HOUR
            if start > end:
                in_night = h >= start or h < end
            else:
                in_night = start <= h < end
            base = config.NIGHT_BRIGHTNESS if in_night else config.DAY_BRIGHTNESS
        else:
            base = config.DAY_BRIGHTNESS

        if config.LAUNCH_RAMP:
            try:
                m = data.get_next_mission()
                days, hours, mins, _ = data.time_until(m.get("net"))
                if days is not None:
                    total_hours = days * 24 + hours + mins / 60
                    if 0 <= total_hours <= config.LAUNCH_RAMP_HOURS:
                        frac = 1.0 - (total_hours / config.LAUNCH_RAMP_HOURS)
                        base = int(base + (100 - base) * frac)
            except Exception:
                pass

        return base

    # --- public API ----------------------------------------------------------

    def get_current(self) -> int:
        return self._current

    def set_manual(self, pct: int, hold_seconds: int = 1800):
        self._manual_until = time.time() + hold_seconds
        self._apply(pct)

    def update(self):
        now = time.time()
        if now - self._last_update < 1.0:
            return
        self._last_update = now
        if now >= self._manual_until:
            self._apply(self._target())

    def cleanup(self):
        if self._pi is not None:
            try:
                self._pi.stop()
            except Exception:
                pass
