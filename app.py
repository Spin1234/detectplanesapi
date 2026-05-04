from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

app = Flask(__name__)
CORS(app)

# --- Configuration ---
# Ensure these keys match the Environment Variable names in your hosting provider (e.g., Render)
OPENSKY_USERNAME = os.environ.get("spark_n") 
OPENSKY_PASSWORD = os.environ.get("Open@sky1234")

# --- Helper for Resilient Requests ---
def get_resilient_session():
    session = requests.Session()
    # Retries 3 times, waiting longer between each try (0.3s, 0.6s, 1.2s)
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

@app.route("/")
def home():
    return jsonify({"message": "Plane Tracking API is running"})

@app.route("/planes", methods=["GET"])
def get_planes():
    try:
        # Get coordinates from request
        lamin = request.args.get("lamin")
        lomin = request.args.get("lomin")
        lamax = request.args.get("lamax")
        lomax = request.args.get("lomax")

        if not all([lamin, lomin, lamax, lomax]):
            return jsonify({"error": "Missing parameters"}), 400

        url = "https://opensky-network.org/api/states/all"
        params = {
            "lamin": lamin,
            "lomin": lomin,
            "lamax": lamax,
            "lomax": lomax
        }

        session = get_resilient_session()
        
        # Determine Auth
        auth = None
        if OPENSKY_USERNAME and OPENSKY_PASSWORD:
            auth = (OPENSKY_USERNAME, OPENSKY_PASSWORD)

        # Increased timeout to 20 seconds to handle slow OpenSky responses
        response = session.get(url, params=params, auth=auth, timeout=20)

        if response.status_code != 200:
            return jsonify({
                "error": "OpenSky API error",
                "status_code": response.status_code,
                "details": response.text
            }), response.status_code

        data = response.json()
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

    except requests.exceptions.Timeout:
        return jsonify({"error": "The OpenSky server took too long to respond. Try again shortly."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
