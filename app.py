import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

print("=== APP START ===")

# ---------- データ ----------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

print("Loaded champions:", len(champions))

# ---------- 設定 ----------
PACK_SIZE = 10
TOTAL_ROUNDS = 3

orders = [
    ["blue","red","red","blue","blue","red","red","blue","blue","red"],
    ["red","blue","blue","red","red","blue","blue","red","red","blue"],
    ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]

# ---------- 状態 ----------
state = {
    "started": False,
    "round": 1,
    "turn": 0,
    "pack": [],
    "picks": {"blue": [], "red": []},
    "time": 30,
    "last": time.time()
}

used_global = set()  # 全パック重複防止

# ---------- パック生成 ----------
def create_pack():
    global used_global

    available = [c for c in champions if c["name"] not in used_global]

    if len(available) < PACK_SIZE:
        used_global = set()
        available = champions.copy()

    pack = random.sample(available, PACK_SIZE)

    for c in pack:
        used_global.add(c["name"])

    return pack

# ---------- ラウンド開始 ----------
def start_round():
    state["pack"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# ---------- ルート ----------
@app.route("/")
def home():
    return "LOL DRAFT RUNNING"

@app.route("/blue")
def blue():
    return render_template("index.html", role="blue")

@app.route("/red")
def red():
    return render_template("index.html", role="red")

@app.route("/spec")
def spec():
    return render_template("index.html", role="spec")

# ---------- 接続 ----------
@socketio.on("connect")
def connect():
    emit("state", state)

# ---------- スタート ----------
@socketio.on("start")
def start():
    if not state["started"]:
        state["started"] = True
        state["round"] = 1
        state["picks"] = {"blue": [], "red": []}
        start_round()
        emit("state", state, broadcast=True)

# ---------- ピック ----------
@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if not state["started"]:
        return

    order = orders[state["round"]-1]
    current = order[state["turn"]]

    if role != current:
        return

    champ = next((c for c in state["pack"] if c["name"] == name), None)
    if not champ:
        return

    state["pack"].remove(champ)
    state["picks"][role].append(champ)

    state["turn"] += 1
    state["time"] = 30
    state["last"] = time.time()

    # パック終了
    if state["turn"] >= PACK_SIZE:
        if state["round"] < TOTAL_ROUNDS:
            state["round"] += 1
            start_round()
        else:
            state["started"] = False

    emit("state", state, broadcast=True)

# ---------- タイマー ----------
def timer():
    while True:
        socketio.sleep(1)

        if not state["started"]:
            continue

        remain = 30 - int(time.time() - state["last"])

        if remain != state["time"]:
            state["time"] = max(remain, 0)

            if state["time"] <= 0:
                state["turn"] += 1
                state["last"] = time.time()
                state["time"] = 30

            socketio.emit("state", state)

socketio.start_background_task(timer)

# ---------- 起動 ----------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
