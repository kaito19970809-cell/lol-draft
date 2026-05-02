import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

print("=== START ===")

# -----------------
# データ
# -----------------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

used = set()

def create_pack():
    pack = []
    while len(pack) < 10:
        c = random.choice(champions)
        if c["name"] not in used:
            used.add(c["name"])
            pack.append(c)
    return pack

orders = [
 ["blue","red","red","blue","blue","red","red","blue","blue","red"],
 ["red","blue","blue","red","red","blue","blue","red","red","blue"],
 ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]

state = {
    "round": 1,
    "turn": 0,
    "pack": [],
    "picks": {"blue":[], "red":[]},
    "time": 30,
    "last": time.time(),
    "started": False
}

def start_round():
    state["pack"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# -----------------
# ルート
# -----------------
@app.route("/blue")
def blue():
    return render_template("index.html", role="blue")

@app.route("/red")
def red():
    return render_template("index.html", role="red")

# -----------------
# 接続
# -----------------
@socketio.on("connect")
def connect():
    emit("state", state)

# -----------------
# スタート（1人でもOK）
# -----------------
@socketio.on("start")
def start(data):
    state["started"] = True
    state["round"] = 1
    state["picks"] = {"blue":[], "red":[]}
    used.clear()
    start_round()

    socketio.emit("state", state)

# -----------------
# ピック
# -----------------
@socketio.on("pick")
def pick(data):
    if not state["started"]:
        return

    role = data["role"]
    champ = data["champ"]

    order = orders[state["round"]-1]
    current = order[state["turn"]]

    if role != current:
        return

    target = next((c for c in state["pack"] if c["name"] == champ), None)
    if not target:
        return

    state["pack"].remove(target)
    state["picks"][role].append(target)

    state["turn"] += 1
    state["time"] = 30
    state["last"] = time.time()

    # 次ラウンド
    if state["turn"] >= 10:
        if state["round"] < 3:
            state["round"] += 1
            start_round()
        else:
            state["started"] = False

    socketio.emit("state", state)

# -----------------
# リセット
# -----------------
@socketio.on("reset")
def reset():
    used.clear()
    state["round"] = 1
    state["turn"] = 0
    state["pack"] = []
    state["picks"] = {"blue":[], "red":[]}
    state["started"] = False
    socketio.emit("state", state)

# -----------------
# タイマー
# -----------------
def timer():
    while True:
        socketio.sleep(1)

        if not state["started"]:
            continue

        remain = 30 - int(time.time() - state["last"])

        if remain != state["time"]:
            state["time"] = max(remain,0)

            if state["time"] <= 0:
                state["turn"] += 1
                state["last"] = time.time()
                state["time"] = 30

            socketio.emit("state", state)

socketio.start_background_task(timer)
