import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify
import random, json

print("=== APP START ===")

# -----------------
# Flask
# -----------------
app = Flask(__name__)

# -----------------
# チャンピオン読み込み
# -----------------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

for c in champions:
    c["image"] = c["name"].replace(" ", "").replace("'", "")

# -----------------
# 設定
# -----------------
weights = {
    "S": 5,
    "A": 10,
    "B": 20,
    "C": 30,
    "D": 35
}

ROLES = ["TOP","JG","MID","ADC","SUP"]

# -----------------
# 抽選
# -----------------
def weighted_choice(candidates):
    pool = []
    for c in candidates:
        pool += [c] * weights.get(c["tier"], 20)
    return random.choice(pool)

# -----------------
# パック生成
# -----------------
def generate_pack(pool):
    pack = []

    for role in ROLES:
        candidates = [c for c in pool if role in c["roles"]]

        if not candidates:
            raise Exception(f"{role}不足")

        chosen = weighted_choice(candidates)
        pack.append(chosen)
        pool.remove(chosen)

    return pack

def generate_all_packs():
    pool = champions.copy()
    random.shuffle(pool)

    packs = []
    for _ in range(6):
        packs.append(generate_pack(pool))

    return packs

# -----------------
# ルート
# -----------------
@app.route("/")
def home():
    return "LoL Draft Server Running"

@app.route("/packs")
def packs():
    return jsonify(generate_all_packs())

# -----------------
# 起動
# -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
