from flask import Flask, request, jsonify
import hashlib, json, time, threading, requests, random

app = Flask(__name__)

# Load or initialize keys.json
try:
    with open("keys.json", "r") as f:
        api_keys = json.load(f)
except:
    api_keys = {}

def save_keys():
    with open("keys.json", "w") as f:
        json.dump(api_keys, f)

def is_valid_key(key):
    if key in api_keys:
        if time.time() < api_keys[key]["expiry"]:
            return True
        else:
            del api_keys[key]
            save_keys()
    return False

@app.route("/genkey")
def genkey():
    admin = request.args.get("admin")
    if admin != "admin123":
        return jsonify({"error": "Invalid admin password"}), 403
    expiry = int(request.args.get("expire", 60)) * 60
    raw = f"{time.time()}{random.random()}"
    key = hashlib.sha256(raw.encode()).hexdigest()
    api_keys[key] = {"created": time.time(), "expiry": time.time() + expiry}
    save_keys()
    return jsonify({"api_key": key, "valid_for_minutes": expiry // 60})

@app.route("/")
def send_views():
    url = request.args.get("url")
    views = int(request.args.get("views", 1))
    key = request.args.get("key")

    if not url or not key or not is_valid_key(key):
        return jsonify({"error": "Invalid request or API key"}), 403

    def send_view(proxy):
        try:
            session = requests.Session()
            session.proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            session.get(url, timeout=5)
        except:
            pass

    def fetch_proxies():
        try:
            r = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=all&ssl=all&anonymity=elite")
            return list(set([line.strip() for line in r.text.splitlines() if ":" in line]))
        except:
            return []

    threading.Thread(target=lambda: run_view_cycle(url, views)).start()
    return jsonify({"status": "sending", "url": url, "views": views})

def run_view_cycle(url, views):
    sent = 0
    while sent < views:
        proxy_list = fetch_proxies()
        if not proxy_list:
            time.sleep(3)
            continue
        for proxy in proxy_list:
            if sent >= views:
                break
            threading.Thread(target=send_view, args=(proxy,)).start()
            sent += 1
            time.sleep(0.7)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
