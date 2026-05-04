from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# OpenSky credentials (set in Render env variables)
OPENSKY_USERNAME = os.environ.get("spark_n")
OPENSKY_PASSWORD = os.environ.get("Open@sky1234")

# Simple in-memory cache (to avoid rate limits)
CACHE = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 15  # seconds


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

        # ✅ Serve from cache if recent
        current_time = time.time()
        if CACHE["data"] and (current_time - CACHE["timestamp"] < CACHE_TTL):
            return jsonify(CACHE["data"])

        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

        # ✅ Retry logic
        for attempt in range(3):
            try:
                if OPENSKY_USERNAME and OPENSKY_PASSWORD:
                    response = requests.get(
                        url,
                        auth=(OPENSKY_USERNAME, OPENSKY_PASSWORD),
                        timeout=10
                    )
                else:
                    response = requests.get(url, timeout=10)

                # If success → break
                if response.status_code == 200:
                    break

                # If rate limit → wait and retry
                if response.status_code == 429:
                    time.sleep(5)

            except requests.exceptions.RequestException:
                time.sleep(2)

        # ❌ Still failed
        if response.status_code != 200:
            return jsonify({
                "error": "OpenSky API blocked request",
                "status_code": response.status_code,
                "message": "Try again later or use authentication"
            }), response.status_code

        # ✅ Safe JSON parse
        try:
            data = response.json()
        except Exception:
            return jsonify({
                "error": "Invalid response from OpenSky (not JSON)"
            }), 500

        # ✅ Format clean response
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

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
