"""
data.py
-------
All external data for the kiosk, with caching, offline fallbacks, and
background refresh so network fetches never block the render loop.

Two sources:
  - Launch Library 2 (ll.thespacedevs.com) for the SpaceX launch schedule.
  - yfinance (Yahoo Finance) for the SPCX stock price + intraday chart.

Caching strategy: get_*() always returns immediately from cache (or the
built-in fallback). If the cache is stale, a daemon thread is spawned to
refresh it; the next call picks up the fresh data.
"""

import json
import os
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

import config

HERE           = os.path.dirname(__file__)
SCHEDULE_CACHE = os.path.join(HERE, "cache_schedule.json")
STOCK_CACHE    = os.path.join(HERE, "cache_stock.json")

LL2_URL = (
    "https://ll.thespacedevs.com/2.2.0/launch/upcoming/"
    f"?lsp__id={config.LL2_AGENCY_ID}&limit=8&mode=detailed"
)

# ---- Fallbacks (shown only if we have never fetched and are offline) ----
FALLBACK_SCHEDULE = [
    {
        "mission_name":   "STARLINK GROUP 12-5",
        "rocket":         "Falcon 9 Block 5",
        "pad":            "SLC-40, Cape Canaveral",
        "orbit":          "Low Earth Orbit",
        "payload_desc":   "23 Starlink v2 Mini satellites",
        "booster_serial": "B1067",
        "booster_flights": 22,
        "net":            "2026-06-27T14:30:00Z",
    },
    {
        "mission_name":   "USSF-44",
        "rocket":         "Falcon Heavy",
        "pad":            "LC-39A, Kennedy",
        "orbit":          "Geostationary",
        "payload_desc":   "USSF classified payload",
        "booster_serial": "B1080",
        "booster_flights": 5,
        "net":            "2026-07-02T09:00:00Z",
    },
]

FALLBACK_STOCK = {
    "ticker":     "SPCX",
    "price":      154.54,
    "prev_close": 156.11,
    "day_high":   159.86,
    "day_low":    150.72,
    "series":     [],
    "stale":      True,
}


# ---- Background fetch management ----------------------------------------
_pending: set = set()
_lock = threading.Lock()


def _bg_fetch(name: str, fn) -> None:
    """Spawn fn() in a daemon thread; no-op if one is already running."""
    with _lock:
        if name in _pending:
            return
        _pending.add(name)

    def _run():
        try:
            fn()
        finally:
            with _lock:
                _pending.discard(name)

    threading.Thread(target=_run, daemon=True).start()


# ---- Generic cache helpers ----------------------------------------------
def _cache_fresh(path: str) -> bool:
    if not os.path.exists(path):
        return False
    return (time.time() - os.path.getmtime(path)) < config.FETCH_REFRESH_SECONDS


def _read_cache(path: str, fallback):
    """Return parsed JSON from path, or a deep copy of fallback.

    A deep copy is critical: callers must never mutate a module-level
    constant, even accidentally through the returned reference.
    """
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return json.loads(json.dumps(fallback))


def _write_cache(path: str, obj) -> None:
    try:
        with open(path, "w") as f:
            json.dump(obj, f, indent=2)
    except OSError:
        pass


# ---- Launch schedule (LL2) ----------------------------------------------
def _parse_launch(result: dict) -> dict:
    rocket  = result.get("rocket", {})
    config_ = rocket.get("configuration", {})
    mission = result.get("mission") or {}
    pad     = result.get("pad", {})

    booster_serial, booster_flights = "UNKNOWN", None
    try:
        stage          = rocket["launcher_stage"][0]
        booster_serial = stage["launcher"]["serial_number"] or "UNKNOWN"
        booster_flights = stage.get("launcher_flight_number")
    except (KeyError, IndexError, TypeError):
        pass

    return {
        "mission_name":   result.get("name", "UNKNOWN MISSION"),
        "rocket":         config_.get("full_name") or config_.get("name", "Falcon 9"),
        "pad":            pad.get("name", "UNKNOWN PAD"),
        "orbit":          (mission.get("orbit") or {}).get("name", "N/A"),
        "payload_desc":   (mission.get("description") or "")[:140],
        "booster_serial": booster_serial,
        "booster_flights": booster_flights,
        "net":            result.get("net", ""),
    }


def _fetch_schedule() -> None:
    """Network fetch; runs in a background thread."""
    try:
        req = urllib.request.Request(LL2_URL, headers={"User-Agent": "falcon-hud/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = json.loads(resp.read().decode())
        launches = [_parse_launch(r) for r in raw.get("results", [])]
        if launches:
            _write_cache(SCHEDULE_CACHE, launches)
        else:
            print("[data] schedule: API returned no upcoming launches")
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"[data] schedule fetch failed: {e}")


def get_schedule(force: bool = False) -> list:
    """Return cached launch list immediately; refresh in background if stale."""
    if force or not _cache_fresh(SCHEDULE_CACHE):
        _bg_fetch("schedule", _fetch_schedule)
    return _read_cache(SCHEDULE_CACHE, FALLBACK_SCHEDULE)


def get_next_mission(force: bool = False) -> dict:
    sched = get_schedule(force=force)
    return sched[0] if sched else json.loads(json.dumps(FALLBACK_SCHEDULE[0]))


# ---- Time helpers -------------------------------------------------------
def time_until(net_iso: str):
    """Return (days, hours, minutes, seconds) until net_iso, or all None."""
    if not net_iso:
        return None, None, None, None
    try:
        net     = datetime.fromisoformat(net_iso.replace("Z", "+00:00"))
        total_s = (net - datetime.now(timezone.utc)).total_seconds()
        if total_s < 0:
            return 0, 0, 0, 0
        d = int(total_s // 86400)
        h = int((total_s % 86400) // 3600)
        m = int((total_s % 3600) // 60)
        s = int(total_s % 60)
        return d, h, m, s
    except (ValueError, AttributeError):
        return None, None, None, None


def days_until(net_iso: str):
    """Compat shim — returns (days, hours)."""
    d, h, _, _ = time_until(net_iso)
    return d, h


# ---- Stock (yfinance) ---------------------------------------------------
def _fetch_stock() -> None:
    """Network fetch; runs in a background thread."""
    try:
        import yfinance as yf
        t    = yf.Ticker(config.STOCK_TICKER)
        hist = t.history(period="1d", interval="5m")
        series = [round(float(c), 2) for c in hist["Close"].tolist()] if len(hist) else []

        fi    = getattr(t, "fast_info", {}) or {}
        # Use explicit None checks — a price / stat of 0.0 is valid data.
        last  = fi.get("lastPrice")
        price = last if last is not None else (series[-1] if series else None)

        def _safe_round(val):
            return round(float(val), 2) if val is not None else None

        snap = {
            "ticker":     config.STOCK_TICKER,
            "price":      _safe_round(price),
            "prev_close": _safe_round(fi.get("previousClose")),
            "day_high":   _safe_round(fi.get("dayHigh")),
            "day_low":    _safe_round(fi.get("dayLow")),
            "series":     series,
            "stale":      False,
        }
        if snap["price"] is not None:   # explicit check — $0.00 is valid
            _write_cache(STOCK_CACHE, snap)
    except ImportError:
        print("[data] yfinance not installed — stock page will show fallback")
    except Exception as e:              # yfinance raises many error types
        print(f"[data] stock fetch failed: {e}")


def get_stock(force: bool = False) -> dict:
    """Return cached stock data immediately; refresh in background if stale."""
    fresh  = _cache_fresh(STOCK_CACHE)
    if force or not fresh:
        _bg_fetch("stock", _fetch_stock)
    cached = _read_cache(STOCK_CACHE, FALLBACK_STOCK)
    cached["stale"] = not fresh
    return cached
