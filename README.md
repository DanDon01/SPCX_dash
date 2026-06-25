# SpaceX Desk HUD

A looping, multi-page SpaceX dashboard for a Raspberry Pi with a small screen.
Webcast-style HUD aesthetic. Auto-rotates through five pages; touch + physical
buttons supported.

## Pages
1. **Trajectory** - animated single-arch launch recreation with live-style
   altitude/velocity readouts, phase callouts, mission + booster-reuse info.
2. **Schedule** - table of upcoming SpaceX launches (date, mission, vehicle, pad).
3. **Countdown** - days/hours to the next mission, with mission details.
4. **Stock** - SPCX price, day stats, and a 24h intraday chart.
5. **Settings** - real brightness control, network info, reboot/shutdown.

## File map
| File | What it does |
|------|--------------|
| `main.py` | Entry point. Page manager, rotation timer, touch/swipe/button routing. |
| `config.py` | **Edit this first.** Resolution, page duration, ticker, colours. |
| `data.py` | Launch Library 2 + yfinance fetches, caching, offline fallbacks. |
| `profile.py` | Falcon 9 flight-event timeline driving the trajectory animation. |
| `ui.py` | Shared fonts and drawing helpers. |
| `system.py` | Real Pi control: brightness, network, power. |
| `input_gpio.py` | Physical button mapping (edit pins to match your wiring). |
| `pages/` | One module per page, all sharing `pages/base.py`. |

## Install
```bash
pip install pygame yfinance
# on a Pi, also: sudo apt install python3-gpiozero
python3 main.py
```

## Configure for your screen
Open `config.py` and set:
- `RESOLUTION` - e.g. `(800, 480)` for the 7" DSI, `(1024, 600)` for HDMI IPS.
- `PAGE_DURATION` - seconds per page before auto-advance (e.g. `120` = 2 min).
- `FULLSCREEN = True` - for kiosk mode on the Pi.
- `STOCK_TICKER` - `"SPCX"` by default.

## Brightness permissions (Pi)
Writing brightness lives at `/sys/class/backlight/*/brightness` and normally
needs root. Grant your user access once with a udev rule:
```bash
# /etc/udev/rules.d/90-backlight.rules
SUBSYSTEM=="backlight", ACTION=="add", \
  RUN+="/bin/chgrp video /sys/class/backlight/%k/brightness", \
  RUN+="/bin/chmod g+w /sys/class/backlight/%k/brightness"
```
Reboot after adding it.

## Autostart on boot (systemd)
Create `/etc/systemd/system/spacex-hud.service`:
```ini
[Unit]
Description=SpaceX Desk HUD
After=graphical.target

[Service]
User=YOUR_USER
Environment=DISPLAY=:0
WorkingDirectory=/home/YOUR_USER/spacex-hud
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=graphical.target
```
Then:
```bash
sudo systemctl enable spacex-hud
sudo systemctl start spacex-hud
```

## Controls
- Auto-advances on a timer (paused on Settings).
- Tap left/right edge, or swipe, to change page. Middle taps go to the page.
- GPIO `NEXT`/`PREV` change page; `A/B/X/Y` go to the active page.
- Keyboard: arrows / space change page, Esc quits.

## Notes
- All network fetches cache locally and fall back gracefully offline.
- Launch Library 2 free tier is ~15 calls/hour; the app refreshes hourly.
- `gpiozero` is optional - touch/keyboard work without it.
