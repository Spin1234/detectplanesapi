from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# 🔐 Optional OpenSky credentials (set in Render env)
OPENSKY_USERNAME = os.environ.get("spark_n")
OPENSKY_PASSWORD = os.environ.get("Open@sky1234")

# ⚡ Cache to avoid rate limit + speed up
CACHE = {
    "data": None,
    "timestamp": 0,
    "params": None
}
CACHE_TTL = 30  # seconds


@app.route("/")
def home():
    return jsonify({"message": "Plane Tracking API Running"})


@app.route("/planes", methods=["GET"])
def get_planes():
    try:
        lamin = request.args.get("lamin")
        lomin = request.args.get("lomin")
        lamax = request.args.get("lamax")
        lomax = request.args.get("lomax")

        if not all([lamin, lomin, lamax, lomax]):
            return jsonify({"error": "Missing parameters"}), 400

        # ✅ Check cache (same params + within TTL)
        current_time = time.time()
        current_params = (lamin, lomin, lamax, lomax)

        if (
            CACHE["data"] and
            CACHE["params"] == current_params and
            (current_time - CACHE["timestamp"] < CACHE_TTL)
        ):
            return jsonify(CACHE["data"])

        # 🌐 OpenSky API URL
        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

        # 🔥 FAST + SAFE request
        try:
            response = requests.get(
                url,
                auth=(OPENSKY_USERNAME, OPENSKY_PASSWORD) if OPENSKY_USERNAME else None,
                timeout=5   # ⚡ reduced to avoid worker timeout
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            return jsonify({"error": "OpenSky timeout"}), 504

        except requests.exceptions.HTTPError as e:
            return jsonify({
                "error": "OpenSky HTTP error",
                "status": response.status_code,
                "details": str(e)
            }), response.status_code

        except requests.exceptions.RequestException:
            return jsonify({"error": "Connection failed"}), 500

        # ✅ Parse JSON safely
        try:
            data = response.json()
        except Exception:
            return jsonify({"error": "Invalid JSON from OpenSky"}), 500

        # ✅ Format response
        planes = []
        if data.get("states"):
            for plane in data["states"]:
                planes.append({
                    "icao24": plane[0],
                    "callsign": plane[1].strip() if plane[1] else "N/A",
                    "country": plane[2],
                    "longitude": plane[5],
                    "latitude": plane[6],
                    "altitude": plane[7],
                    "velocity": plane[9],
                    "heading": plane[10]
                })

        result = {
            "count": len(planes),
            "planes": planes
        }

        # ✅ Save to cache
        CACHE["data"] = result
        CACHE["timestamp"] = current_time
        CACHE["params"] = current_params

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
