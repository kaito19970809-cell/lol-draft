import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# -------------------------
# チャンピオン読み込み
# -------------------------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

for c in champions:
    c["image"] = c["name"]

# -------------------------
# 状態
# -------------------------
state = {
    "phase": "WAITING",
    "turn": 0,
    "packs": {"blue": [], "red": []},
    "picks": {"blue": [], "red": []}
}

# -------------------------
# パック生成
# -------------------------
def create_packs():
    pool = random.sample(champions, 30)
    packs = [pool[i:i+5] for i in range(0, 30, 5)]

    return {
        "blue": packs[:3],
        "red": packs[3:]
    }

# -------------------------
# 現在プレイヤー
# -------------------------
def current_player():
    return "blue" if state["turn"] % 2 == 0 else "red"

# -------------------------
# ルート
# -------------------------
@app.route("/<role>")
def index(role):
    return render_template("index.html", role=role)

@app.route("/")
def root():
    return "OK"

# -------------------------
# Socket
# -------------------------
@socketio.on("connect")
def connect():
    emit("state", state)

@socketio.on("start")
def start():
    state["phase"] = "DRAFT"
    state["turn"] = 0
    state["packs"] = create_packs()
    state["picks"] = {"blue": [], "red": []}

    socketio.emit("state", state)

@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if state["phase"] != "DRAFT":
        return

    if role != current_player():
        return

    if not state["packs"][role]:
        return

    pack = state["packs"][role][0]

    champ = next((c for c in pack if c["name"] == name), None)
    if not champ:
        return

    # ピック
    state["picks"][role].append(champ)
    pack.remove(champ)

    # パス処理
    other = "red" if role == "blue" else "blue"

    if len(pack) > 0:
        state["packs"][other].append(pack)

    state["packs"][role].pop(0)

    state["turn"] += 1

    # 終了
    if state["turn"] >= 30:
        state["phase"] = "END"

    socketio.emit("state", state)

@socketio.on("reset")
def reset():
    state["phase"] = "WAITING"
    state["turn"] = 0
    state["packs"] = {"blue": [], "red": []}
    state["picks"] = {"blue": [], "red": []}

    socketio.emit("state", state)

# -------------------------
# 起動
# -------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
