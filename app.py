import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random

print("=== APP START ===")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# -------------------------
# チャンピオン読み込み（安全版）
# -------------------------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

# キー統一（ここが重要）
for c in champions:
    if "名前" in c:
        c["name"] = c["名前"]
    elif "name" in c:
        c["名前"] = c["name"]
    else:
        raise Exception("champions.jsonに名前キーがない")

    c["image"] = c["name"].replace(" ", "").replace("'", "")

# -------------------------
# 状態
# -------------------------
state = {
    "started": False,
    "ready": {"blue": False, "red": False},
    "turn": 0,
    "round": 1,
    "pack": [],
    "picks": {"blue": [], "red": []},
    "time": 30
}

# ピック順
orders = [
    ["blue","red","red","blue","blue","red","red","blue","blue","red"],
    ["red","blue","blue","red","red","blue","blue","red","red","blue"],
    ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]

# -------------------------
# ルーティング
# -------------------------
@app.route("/")
def root():
    return "Server Running"

@app.route("/<role>")
def index(role):
    return render_template("index.html", role=role)

# -------------------------
# パック生成
# -------------------------
def new_pack():
    return random.sample(champions, 10)

# -------------------------
# タイマー
# -------------------------
def start_timer():
    def run():
        while state["started"]:
            socketio.sleep(1)
            state["time"] -= 1

            if state["time"] <= 0:
                auto_pick()

            socketio.emit("state", state)

    socketio.start_background_task(run)

# -------------------------
# 自動ピック
# -------------------------
def auto_pick():
    if not state["pack"]:
        return

    champ = state["pack"][0]
    current = orders[state["round"]-1][state["turn"]]

    state["picks"][current].append(champ)
    next_turn()

# -------------------------
# 次のターン
# -------------------------
def next_turn():
    state["turn"] += 1
    state["time"] = 30

    if state["turn"] >= len(orders[state["round"]-1]):
        state["round"] += 1
        state["turn"] = 0

        if state["round"] > 3:
            state["started"] = False
            socketio.emit("state", state)
            return

    # 新パック生成（ここ重要）
    state["pack"] = new_pack()

# -------------------------
# Socket
# -------------------------
@socketio.on("connect")
def connect():
    emit("state", state)

@socketio.on("ready")
def ready(data):
    role = data["role"]
    state["ready"][role] = True

    # 両方準備でスタート
    if state["ready"]["blue"] and state["ready"]["red"]:
        state["started"] = True
        state["round"] = 1
        state["turn"] = 0
        state["picks"] = {"blue": [], "red": []}
        state["pack"] = new_pack()
        state["time"] = 30

        start_timer()

    socketio.emit("state", state)

@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if not state["started"]:
        return

    current = orders[state["round"]-1][state["turn"]]
    if role != current:
        return

    champ = next((c for c in state["pack"] if c["name"] == name), None)
    if not champ:
        return

    state["picks"][role].append(champ)
    state["pack"].remove(champ)

    next_turn()

    socketio.emit("state", state)

@socketio.on("reset")
def reset():
    state["started"] = False
    state["ready"] = {"blue": False, "red": False}
    state["turn"] = 0
    state["round"] = 1
    state["pack"] = []
    state["picks"] = {"blue": [], "red": []}
    state["time"] = 30

    socketio.emit("state", state)

# -------------------------
# 起動
# -------------------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
