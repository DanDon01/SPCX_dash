"""
system.py
---------
Raspberry Pi control for the settings page: backlight brightness, network info,
uptime, and power actions. Every function degrades safely when not on a Pi so
nothing crashes during development on a desktop.
"""

import glob
import os
import socket
import subprocess


# ---- Brightness ---------------------------------------------------------
def _backlight_path():
    candidates = glob.glob("/sys/class/backlight/*/brightness")
    return candidates[0] if candidates else None


def get_brightness():
    path = _backlight_path()
    if not path:
        return None
    try:
        with open(path) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None


def set_brightness(value):
    """Set brightness 0-255. Returns True on success."""
    path = _backlight_path()
    if not path:
        return False
    value = max(0, min(255, int(value)))
    try:
        with open(path, "w") as f:
            f.write(str(value))
        return True
    except PermissionError:
        try:
            subprocess.run(
                ["sudo", "tee", path],
                input=str(value).encode(),
                stdout=subprocess.DEVNULL,
                timeout=5,      # never block the render thread indefinitely
                check=True,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    except OSError:
        return False


# ---- Network ------------------------------------------------------------
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "0.0.0.0"


def get_hostname():
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def get_ssid():
    try:
        out = subprocess.run(
            ["iwgetid", "-r"], capture_output=True, text=True, timeout=3
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


# ---- Uptime -------------------------------------------------------------
def get_uptime():
    """Return (days, hours) of system uptime, or None on non-Linux."""
    try:
        with open("/proc/uptime") as f:
            uptime_s = float(f.read().split()[0])
        return int(uptime_s // 86400), int((uptime_s % 86400) // 3600)
    except (OSError, ValueError):
        return None


# ---- Power --------------------------------------------------------------
def reboot():
    try:
        subprocess.run(["sudo", "reboot"], check=False)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass


def shutdown():
    try:
        subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass


def is_on_pi():
    try:
        with open("/proc/device-tree/model") as f:
            return "raspberry pi" in f.read().lower()
    except OSError:
        return False
