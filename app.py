from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

@app.route("/planes")
def get_planes():
    lamin = request.args.get("lamin")
    lomin = request.args.get("lomin")
    lamax = request.args.get("lamax")
    lomax = request.args.get("lomax")

    url = f"https://opensky-network.org/api/states/all?lamin={lamin}&lomin={lomin}&lamax={lamax}&lomax={lomax}"

    response = requests.get(url)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True)
