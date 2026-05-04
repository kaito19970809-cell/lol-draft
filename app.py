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
    "started": False,
    "turn": 0,
    "pool": [],
    "picks": {"blue": [], "red": []}
}

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
# プール生成（30枚・被りなし）
# -------------------------
def create_pool():
    return random.sample(champions, min(30, len(champions)))

# -------------------------
# ターン取得（青赤交互）
# -------------------------
def current_turn():
    return "blue" if state["turn"] % 2 == 0 else "red"

# -------------------------
# Socket
# -------------------------
@socketio.on("connect")
def connect():
    emit("state", state)

@socketio.on("start")
def start():
    state["started"] = True
    state["turn"] = 0
    state["picks"] = {"blue": [], "red": []}
    state["pool"] = create_pool()
    socketio.emit("state", state)

@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if not state["started"]:
        return

    if role != current_turn():
        return

    champ = next((c for c in state["pool"] if c["name"] == name), None)
    if not champ:
        return

    state["picks"][role].append(champ)
    state["pool"].remove(champ)
    state["turn"] += 1

    socketio.emit("state", state)

@socketio.on("reset")
def reset():
    state["started"] = False
    state["turn"] = 0
    state["pool"] = []
    state["picks"] = {"blue": [], "red": []}
    socketio.emit("state", state)

# -------------------------
# 起動
# -------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
