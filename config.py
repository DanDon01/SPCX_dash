"""
config.py
---------
Central settings and the shared colour theme. Edit this file to retune the
whole kiosk: screen resolution, page duration, stock ticker, and the
webcast-HUD palette every page draws from.
"""

# --- Display -------------------------------------------------------------
RESOLUTION = (480, 320)     # Adafruit 3.5" TFT (HX8357) in landscape
FPS = 30
FULLSCREEN = True           # kiosk mode; set False for windowed dev

# --- Page rotation -------------------------------------------------------
PAGE_DURATION = 30          # seconds per page before auto-advance
AUTO_ADVANCE  = True

# --- UI behaviour --------------------------------------------------------
TRANSITION_MS = 180         # page-change black-fade duration in milliseconds
SHOW_CLOCK    = True        # persistent UTC clock in the top-right corner

# --- Data ----------------------------------------------------------------
STOCK_TICKER         = "SPCX"   # SpaceX since the June 2026 IPO
LL2_AGENCY_ID        = 121      # SpaceX on Launch Library 2
FETCH_REFRESH_SECONDS = 3600

# --- Theme (SpaceX webcast palette) -------------------------------------
COL_BG         = (8,   10,  14)
COL_PANEL      = (14,  18,  24)
COL_TEXT       = (220, 230, 240)
COL_DIM        = (110, 125, 140)
COL_ACCENT     = (0,   200, 255)
COL_ACCENT_HOT = (90,  200, 255)
COL_ARC        = (40,  70,  110)
COL_WARN       = (255, 180, 40)
COL_GOOD       = (60,  220, 130)
COL_BAD        = (255, 80,  90)
COL_GRID       = (22,  28,  36)
COL_LINE       = (40,  70,  110)
COL_EXHAUST    = (60,  140, 200)  # rocket exhaust trail on trajectory page

# --- Backlight (Pi only) ------------------------------------------------
BL_PWM_PIN        = 18     # BCM GPIO18; set None to use sysfs fallback
NIGHT_MODE        = True
NIGHT_START_HOUR  = 22     # 10 PM local
NIGHT_END_HOUR    = 7      # 7 AM local
DAY_BRIGHTNESS    = 100    # percent 0-100
NIGHT_BRIGHTNESS  = 15
LAUNCH_RAMP       = True   # ramp to 100% as launch approaches
LAUNCH_RAMP_HOURS = 6      # hours before launch to start ramping

# --- MQTT / Home Assistant -----------------------------------------------
MQTT_ENABLED     = False   # set True after filling in MQTT_HOST/USER/PASS
MQTT_HOST        = ""
MQTT_PORT        = 1883
MQTT_USER        = ""
MQTT_PASS        = ""
MQTT_BASE_TOPIC  = "spacex_hud"
MQTT_DISCOVERY   = True

# --- Web companion -------------------------------------------------------
WEB_ENABLED = True
WEB_PORT    = 8080
