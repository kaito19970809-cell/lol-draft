import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------- データ ----------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

TIER_WEIGHT = {"S":0.7,"A":1.0,"B":1.2,"C":1.5}

# 🔥 全体で重複禁止
used_global = set()

def weighted_choice(cands):
    ws = [TIER_WEIGHT[c["tier"]] for c in cands]
    total = sum(ws)
    r = random.uniform(0,total)
    s = 0
    for c,w in zip(cands,ws):
        s += w
        if s >= r:
            return c
    return random.choice(cands)

def create_pack():
    result = []
    tier_need = {"S":2,"A":3,"B":4,"C":1}

    for t,n in tier_need.items():
        for _ in range(n):
            cands = [
                c for c in champions
                if c["tier"] == t and c["name"] not in used_global
            ]
            if cands:
                pick = weighted_choice(cands)
                result.append(pick["name"])
                used_global.add(pick["name"])

    return result

# ---------- ピック順 ----------
orders = [
 ["blue","red","red","blue","blue","red","red","blue","blue","red"],
 ["red","blue","blue","red","red","blue","blue","red","red","blue"],
 ["blue","red","blue","red","blue","red","blue","red","blue","red"]
]

# ---------- 状態 ----------
state = {
    "round": 0,
    "turn": 0,
    "pack": [],
    "picks": {"blue": [], "red": []},
    "time": 30,
    "last": time.time(),
    "done": False
}

def start_round():
    state["pack"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

def reset_game():
    global used_global
    used_global = set()

    state["round"] = 1
    state["turn"] = 0
    state["picks"] = {"blue": [], "red": []}
    state["done"] = False

    start_round()

# ---------- ルート ----------
@app.route("/<role>")
def index(role):
    return render_template("index.html", role=role)

@app.route("/reset")
def reset():
    reset_game()
    socketio.emit("state", state)
    return "ok"

# ---------- 接続 ----------
@socketio.on("connect")
def connect():
    if state["round"] == 0:
        reset_game()
    emit("state", state)

# ---------- ピック ----------
@socketio.on("pick")
def pick(data):
    role = data["role"]
    champ = data["champ"]

    if role not in ["blue","red"]:
        return

    current = orders[state["round"]-1][state["turn"]]

    if role != current:
        return

    if champ not in state["pack"]:
        return

    state["pack"].remove(champ)
    state["picks"][role].append(champ)

    state["turn"] += 1
    state["time"] = 30
    state["last"] = time.time()

    # パック終了
    if len(state["pack"]) == 0:
        if state["round"] < 3:
            state["round"] += 1
            start_round()
        else:
            state["done"] = True

    socketio.emit("state", state)

# ---------- タイマー ----------
def timer_loop():
    while True:
        socketio.sleep(1)
        remain = 30 - int(time.time() - state["last"])

        if remain != state["time"]:
            state["time"] = max(remain,0)

            if state["time"] <= 0:
                state["turn"] += 1
                state["last"] = time.time()
                state["time"] = 30

            socketio.emit("state", state)

socketio.start_background_task(timer_loop)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
