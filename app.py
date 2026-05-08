from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route("/planes", methods=["GET"])
def get_planes():
    # 1. Get query parameters from the URL
    lamin = request.args.get("lamin")
    lomin = request.args.get("lomin")
    lamax = request.args.get("lamax")
    lomax = request.args.get("lomax")

    # 2. Check if parameters exist
    if not all([lamin, lomin, lamax, lomax]):
        return jsonify({"error": "Missing coordinates (lamin, lomin, lamax, lomax)"}), 400

    # 3. Call OpenSky API (No Auth needed for limited requests)
    url = "https://opensky-network.org/api/states/all"
    params = {
        "lamin": lamin, 
        "lomin": lomin, 
        "lamax": lamax, 
        "lomax": lomax
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        # 4. Format the results
        planes = []
        if data.get("states"):
            for p in data["states"]:
                planes.append({
                    "icao24": p[0],
                    "callsign": p[1].strip() if p[1] else "N/A",
                    "country": p[2],
                    "longitude": p[5],
                    "latitude": p[6],
                    "altitude": p[7]
                })

        return jsonify({"count": len(planes), "planes": planes})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
