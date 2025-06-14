from flask import Flask, request, jsonify
import requests, random, json, time, os, hashlib

app = Flask(__name__)
KEY_FILE = "keys.json"

def load_keys():
    if not os.path.exists(KEY_FILE): return []
    with open(KEY_FILE) as f:
        try: return json.load(f)
        except: return []

def save_keys(keys):
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f)

def remove_expired_keys():
    now = time.time()
    keys = load_keys()
    keys = [k for k in keys if k["expires"] > now]
    save_keys(keys)

def validate_key(api_key):
    remove_expired_keys()
    keys = load_keys()
    for k in keys:
        if k["key"] == api_key:
            return True
    return False

@app.route("/genkey")
def genkey():
    admin = request.args.get("admin", "")
    if hashlib.sha256(admin.encode()).hexdigest() != hashlib.sha256("admin123".encode()).hexdigest():
        return jsonify({"error": "unauthorized"}), 403
    raw = os.urandom(16).hex()
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    mins = int(request.args.get("expire", "30"))
    expires = time.time() + mins * 60
    keys = load_keys()
    keys.append({"key": hashed, "expires": expires})
    save_keys(keys)
    return jsonify({"raw": raw, "key": hashed, "expires_in_min": mins})

def get_random_proxy():
    try:
        r = requests.get("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", timeout=5)
        plist = r.text.strip().split("\n")
        return random.choice(plist)
    except:
        return None

def send_view(url):
    proxy = get_random_proxy()
    if not proxy: return False, None
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        r = requests.get(url, proxies=proxies, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code == 200, proxy
    except:
        return False, proxy

@app.route("/")
def views():
    url = request.args.get("url", "")
    count = request.args.get("views", "1")
    key = request.args.get("key", "")
    if not url or not key:
        return jsonify({"error": "url and key required"}), 400
    if not validate_key(key):
        return jsonify({"error": "invalid or expired api key"}), 403
    try:
        count = int(count)
    except:
        return jsonify({"error": "invalid count"}), 400
    success = 0
    proxies = []
    for _ in range(count):
        ok, proxy = send_view(url)
        if ok: success += 1
        proxies.append(proxy)
        time.sleep(1)
    return jsonify({"sent": success, "target": url, "attempted": count, "proxies": proxies[-5:]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
