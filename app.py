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
import requests

app = Flask(__name__)

@app.route("/planes")
def get_planes():
    # Get coords from URL
    params = {
        "lamin": request.args.get("lamin"),
        "lomin": request.args.get("lomin"),
        "lamax": request.args.get("lamax"),
        "lomax": request.args.get("lomax")
    }

    # OpenSky Credentials (Optional: set these in Render Environment Variables)
    user = os.environ.get("spark_n")
    pwd = os.environ.get("Open@sky1234")
    auth = (user, pwd) if user and pwd else None

    try:
        # We add a 'User-Agent' header so OpenSky doesn't think we are a bot
        headers = {'User-Agent': 'Python-Flask-Tracker-App'}
        
        response = requests.get(
            "https://opensky-network.org/api/states/all", 
            params=params, 
            auth=auth,
            headers=headers,
            timeout=25  # Increased timeout
        )
        
        data = response.json()
        return jsonify(data)

    except requests.exceptions.Timeout:
        return jsonify({"error": "OpenSky timed out. They might be busy."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
