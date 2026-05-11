# from flask import Flask, jsonify, request
# import requests

# app = Flask(__name__)

# @app.route("/planes", methods=["GET"])
# def get_planes():
#     # 1. Get query parameters from the URL
#     lamin = request.args.get("lamin")
#     lomin = request.args.get("lomin")
#     lamax = request.args.get("lamax")
#     lomax = request.args.get("lomax")

#     # 2. Check if parameters exist
#     if not all([lamin, lomin, lamax, lomax]):
#         return jsonify({"error": "Missing coordinates (lamin, lomin, lamax, lomax)"}), 400

#     # 3. Call OpenSky API (No Auth needed for limited requests)
#     url = "https://opensky-network.org/api/states/all"
#     params = {
#         "lamin": lamin, 
#         "lomin": lomin, 
#         "lamax": lamax, 
#         "lomax": lomax
#     }
    
#     try:
#         response = requests.get(url, params=params, timeout=10)
#         data = response.json()

#         # 4. Format the results
#         planes = []
#         if data.get("states"):
#             for p in data["states"]:
#                 planes.append({
#                     "icao24": p[0],
#                     "callsign": p[1].strip() if p[1] else "N/A",
#                     "country": p[2],
#                     "longitude": p[5],
#                     "latitude": p[6],
#                     "altitude": p[7]
#                 })

#         return jsonify({"count": len(planes), "planes": planes})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)




import os
from flask import Flask, jsonify, request
from flask_cors import CORS  # <-- REQUIRED for your JS fetch to work
import requests

app = Flask(__name__)
CORS(app) # This allows your frontend to talk to this API

@app.route("/planes")
def get_planes():
    # Capture the bounding box coordinates
    params = {
        "lamin": request.args.get("lamin"),
        "lomin": request.args.get("lomin"),
        "lamax": request.args.get("lamax"),
        "lomax": request.args.get("lomax")
    }

    try:
        # Use a generic browser-like User-Agent to help avoid instant blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # OpenSky is notoriously slow on the public API
        response = requests.get(
            "https://opensky-network.org/api/states/all", 
            params=params, 
            headers=headers,
            timeout=60 
        )
        
        # Check if OpenSky returned a 429 (Too Many Requests)
        if response.status_code == 429:
            return jsonify({"error": "OpenSky rate limit hit. Try again in a minute."}), 429

        data = response.json()
        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({"error": "OpenSky took too long to respond."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render requires host 0.0.0.0 and the PORT env variable
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
