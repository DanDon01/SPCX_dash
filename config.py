"""
config.py
---------
Central settings and the shared colour theme. Edit this file to retune the
whole kiosk: screen resolution, page duration, stock ticker, and the
webcast-HUD palette every page draws from.
"""

# --- Display -------------------------------------------------------------
RESOLUTION = (800, 480)     # change to match your screen, e.g. (1024, 600)
FPS = 30
FULLSCREEN = False          # set True for kiosk mode on the Pi

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
