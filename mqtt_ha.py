"""
mqtt_ha.py
----------
Home Assistant MQTT discovery + state publisher.
No-op when MQTT_ENABLED is False or paho-mqtt is not installed.

Publishes four sensors under MQTT_BASE_TOPIC:
  next_mission, launch_days, next_rocket, spcx_price

HA auto-discovery topics: homeassistant/sensor/spacex_hud/<uid>/config
State topics:             spacex_hud/<uid>/state
"""

import json
import threading

import config
import data

_SENSORS = [
    {
        "uid":  "next_mission",
        "name": "SpaceX Next Mission",
        "icon": "mdi:rocket-launch",
        "state_fn": lambda: (data.get_next_mission() or {}).get("mission_name", "Unknown"),
    },
    {
        "uid":  "launch_days",
        "name": "SpaceX Launch Days",
        "icon": "mdi:calendar-clock",
        "unit": "days",
        "state_fn": lambda: _launch_days(),
    },
    {
        "uid":  "next_rocket",
        "name": "SpaceX Next Rocket",
        "icon": "mdi:rocket",
        "state_fn": lambda: (data.get_next_mission() or {}).get("rocket", "Unknown"),
    },
    {
        "uid":  "spcx_price",
        "name": "SPCX Price",
        "icon": "mdi:currency-usd",
        "unit": "USD",
        "state_fn": lambda: _spcx_price(),
    },
]


def _launch_days() -> str:
    m = data.get_next_mission()
    d, *_ = data.time_until(m.get("net") if m else None)
    return str(d) if d is not None else "TBD"


def _spcx_price() -> str:
    p = (data.get_stock() or {}).get("price")
    return f"{p:.2f}" if p is not None else "N/A"


class MqttPublisher:
    def __init__(self):
        self._client = None
        self._stop   = threading.Event()

    # --- connection ----------------------------------------------------------

    def _connect(self) -> bool:
        if not config.MQTT_ENABLED or not config.MQTT_HOST:
            return False
        try:
            import paho.mqtt.client as mqtt
            try:
                from paho.mqtt.enums import CallbackAPIVersion
                client = mqtt.Client(CallbackAPIVersion.VERSION1,
                                     client_id="spacex_hud")
            except ImportError:
                client = mqtt.Client(client_id="spacex_hud")

            if config.MQTT_USER:
                client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
            client.connect(config.MQTT_HOST, config.MQTT_PORT, keepalive=60)
            client.loop_start()
            self._client = client
            return True
        except Exception:
            return False

    # --- publish helpers -----------------------------------------------------

    def _publish_discovery(self):
        if self._client is None:
            return
        base = f"homeassistant/sensor/{config.MQTT_BASE_TOPIC}"
        for s in _SENSORS:
            uid     = s["uid"]
            payload = {
                "name":        s["name"],
                "unique_id":   f"spacex_hud_{uid}",
                "state_topic": f"{config.MQTT_BASE_TOPIC}/{uid}/state",
                "icon":        s.get("icon"),
            }
            if "unit" in s:
                payload["unit_of_measurement"] = s["unit"]
            try:
                self._client.publish(
                    f"{base}/{uid}/config",
                    json.dumps(payload),
                    retain=True,
                )
            except Exception:
                pass

    def _publish_state(self):
        if self._client is None:
            return
        for s in _SENSORS:
            try:
                val = s["state_fn"]()
                self._client.publish(
                    f"{config.MQTT_BASE_TOPIC}/{s['uid']}/state",
                    str(val),
                )
            except Exception:
                pass

    # --- background thread ---------------------------------------------------

    def _run(self, interval: int):
        if not self._connect():
            return
        self._publish_discovery()
        self._publish_state()
        while not self._stop.wait(interval):
            self._publish_state()

    def start_background(self, interval: int = 300):
        if not config.MQTT_ENABLED:
            return
        t = threading.Thread(
            target=self._run, args=(interval,),
            daemon=True, name="mqtt",
        )
        t.start()

    def cleanup(self):
        self._stop.set()
        if self._client is not None:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception:
                pass
