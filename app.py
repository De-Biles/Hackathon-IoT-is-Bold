from sense_hat import SenseHat
from flask import Flask, jsonify, request
from flask_cors import CORS
from filelock import FileLock

import json
import requests
import time
import os
import math

LOCK = FileLock("userData/history.lock")
app = Flask(__name__)
CORS(app)

sense = SenseHat()
sense.low_light = True

HISTORY_FILE = "userData/history.json"
MAX_HISTORY = 500   # points to keep in memory

lat = 53.2707
lon = -9.0568

url = (
    "https://api.open-meteo.com/v1/forecast?"
    f"latitude={lat}&longitude={lon}"
    "&current=temperature_2m,relative_humidity_2m"
)

def update_url():
    global url
    with open("userData/coords.json", "r") as f:
        data = json.load(f)
        lat = data.get("lat")
        lon = data.get("lon")

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m"
    )

cache = {
    "data": None,
    "ts": 0
}

CACHE_TTL = 300

def get_weather():
    now = time.time()

    if cache["data"] and now - cache["ts"] < CACHE_TTL:
        return cache["data"]

    update_url()

    try:
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        cache["data"] = data
        cache["ts"] = now

        return data

    except requests.exceptions.RequestException as e:
        print("WEATHER ERROR:", e)

        if cache["data"]:
            return cache["data"]

        return {
            "current": {
                "temperature_2m": 10,
                "relative_humidity_2m": 85
            }
        }

def send_ntfy(message, topic="mytopic"):
    try:
        requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print("NTFY ERROR:", e)

def load_history():
    with LOCK:
        if not os.path.exists(HISTORY_FILE):
            return []

        with open(HISTORY_FILE) as f:
            return json.load(f)


def save_history(history):
    with LOCK:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f)


def add_history_point(value):
    history = load_history()

    history.append({
        "t": int(time.time()),
        "rh": value
    })

    history = history[-MAX_HISTORY:]

    save_history(history)

@app.route("/set_state", methods=["POST"])
def set_state():
    data = request.json
    state = data.get("state")

    if state == "high":
        color = [100, 0, 0]
    elif state == "recommended":
        color = [0, 100, 0]
    else:
        color = [0, 0, 100]

    sense.clear(color)

    return {"status": "ok"}

@app.route("/notify", methods=["POST"])
def notify():
    data = request.json

    if not data or "message" not in data:
        return {"error": "message is required"}, 400

    message = str(data["message"])
    topic = data.get("topic", "mytopic")

    send_ntfy(message, topic)

    return {"status": "sent", "message": message}

@app.route("/metrics")
def metrics():
    data = get_weather()

    temp_o = data["current"]["temperature_2m"]
    rh_o = data["current"]["relative_humidity_2m"]

    temp_i = sense.get_temperature_from_humidity()
    humidity_i = sense.get_humidity()

    if humidity_i is None or math.isnan(humidity_i):
        humidity_i = None


    add_history_point(humidity_i)

    return jsonify({
        "i_temperature": temp_i,
        "i_humidity": humidity_i,
        "o_temperature": temp_o,
        "o_humidity": rh_o
    })


@app.route("/history")
def history():
    return jsonify(load_history())


SETTINGS_FILE = "userData/settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "maxRH": 70,
            "minTemp": 15,
            "mode": 2,
            "notify": ""
        }
    try:
        with open(SETTINGS_FILE) as f:
            return json.load(f)
    except Exception as e:
        print("LOAD SETTINGS ERROR:", e)
        return {
            "maxRH": 70,
            "minTemp": 15,
            "mode": 2,
            "notify": ""
        }

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("SAVE SETTINGS ERROR:", e)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return jsonify(load_settings())

    data = request.json
    if not data:
        return {"error": "No data provided"}, 400

    settings_to_save = {
        "maxRH": data.get("maxRH", 70),
        "minTemp": data.get("minTemp", 15),
        "mode": data.get("mode", 2),
        "notify": data.get("notify", "")
    }

    save_settings(settings_to_save)
    return {"status": "ok", "settings": settings_to_save}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


