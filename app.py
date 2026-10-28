import os
import re
import time
from flask import Flask, jsonify, request, send_from_directory
import requests

app = Flask(__name__, static_folder=None)
COINDCX = "https://public.coindcx.com"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "ExplosiveMoveScanner/1.0", "Accept": "application/json"})
PAIR_RE = re.compile(r"^B-[A-Z0-9]+_USDT$")

@app.get("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "service": "Explosive Move Scanner proxy"})

@app.get("/api/prices")
def prices():
    try:
        r = SESSION.get(f"{COINDCX}/market_data/v3/current_prices/futures/rt", timeout=15)
        r.raise_for_status()
        return jsonify(r.json()), 200
    except requests.RequestException as e:
        return jsonify({"error": "CoinDCX current prices request failed", "detail": str(e)}), 502
    except ValueError:
        return jsonify({"error": "CoinDCX returned invalid JSON for current prices"}), 502

@app.get("/api/candles")
def candles():
    pair = request.args.get("pair", "")
    resolution = request.args.get("resolution", "5")
    if not PAIR_RE.fullmatch(pair):
        return jsonify({"error": "Invalid pair format"}), 400
    if resolution not in {"1", "5", "60", "1D"}:
        return jsonify({"error": "Unsupported candle resolution"}), 400
    now = int(time.time())
    params = {"pair": pair, "from": now - 60 * 60 * 48, "to": now, "resolution": resolution, "pcode": "f"}
    try:
        r = SESSION.get(f"{COINDCX}/market_data/candlesticks", params=params, timeout=15)
        r.raise_for_status()
        return jsonify(r.json()), 200
    except requests.RequestException as e:
        return jsonify({"error": "CoinDCX candles request failed", "detail": str(e)}), 502
    except ValueError:
        return jsonify({"error": "CoinDCX returned invalid JSON for candles"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
