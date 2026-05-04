from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # allow frontend requests

# Optional: OpenSky credentials (recommended for better limits)
OPENSKY_USERNAME = os.environ.get("spark_n")
OPENSKY_PASSWORD = os.environ.get("Open@sky1234")


@app.route("/")
def home():
    return jsonify({
        "message": "Plane Tracking API is running"
    })


@app.route("/planes", methods=["GET"])
def get_planes():
    try:
        lamin = request.args.get("lamin")
        lomin = request.args.get("lomin")
        lamax = request.args.get("lamax")
        lomax = request.args.get("lomax")

        if not all([lamin, lomin, lamax, lomax]):
            return jsonify({"error": "Missing parameters"}), 400

        url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

        # Use auth if available
        if OPENSKY_USERNAME and OPENSKY_PASSWORD:
            response = requests.get(url, auth=(OPENSKY_USERNAME, OPENSKY_PASSWORD), timeout=10)
        else:
            response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return jsonify({
                "error": "Failed to fetch data",
                "status_code": response.status_code,
                "details": response.text
            }), response.status_code

        data = response.json()

        # Clean response (important)
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

        return jsonify({
            "count": len(planes),
            "planes": planes
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Health check (Render uses this sometimes)
@app.route("/health")
def health():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
