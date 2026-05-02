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

used_global = set()  # ★全体重複防止

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

    while len(result) < 10:
        cands = [c for c in champions if c["name"] not in used_global]
        pick = weighted_choice(cands)
        result.append({
            "name": pick["name"],
            "image": pick["image"]
        })
        used_global.add(pick["name"])

    return result

orders = [
    ["blue","red","red","blue","blue","red","red","blue","blue","red"],
    ["red","blue","blue","red","red","blue","blue","red","red","blue"],
    ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]

state = {
    "round": 1,
    "turn": 0,
    "pack": [],
    "picks": {"blue": [], "red": []},
    "time": 30,
    "last": time.time(),
    "started": False,
    "done": False
}

# ---------- 制御 ----------
def start_game():
    state["started"] = True
    state["round"] = 1
    state["turn"] = 0
    state["picks"] = {"blue": [], "red": []}
    state["pack"] = create_pack()
    state["last"] = time.time()
    state["time"] = 30

# ---------- ルート ----------
@app.route("/")
def home():
    return "OK"

@app.route("/blue")
def blue():
    return render_template("index.html", role="blue")

@app.route("/red")
def red():
    return render_template("index.html", role="red")

@app.route("/spec")
def spec():
    return render_template("index.html", role="spec")

# ---------- socket ----------
@socketio.on("connect")
def connect():
    emit("state", state)

@socketio.on("start")
def start():
    global used_global
    used_global = set()
    start_game()
    emit("state", state, broadcast=True)

@socketio.on("pick")
def pick(data):
    if not state["started"] or state["done"]:
        return

    role = data["role"]
    champ = data["champ"]

    current = orders[state["round"]-1][state["turn"]]
    if role != current:
        return

    obj = next((c for c in state["pack"] if c["name"] == champ), None)
    if not obj:
        return

    state["pack"].remove(obj)
    state["picks"][role].append(obj)

    state["turn"] += 1
    state["last"] = time.time()
    state["time"] = 30

    # パック終了
    if state["turn"] >= 10:
        if state["round"] < 3:
            state["round"] += 1
            state["turn"] = 0
            state["pack"] = create_pack()
        else:
            state["done"] = True

    emit("state", state, broadcast=True)

# ---------- タイマー ----------
def timer_loop():
    while True:
        socketio.sleep(1)

        if not state["started"] or state["done"]:
            continue

        remain = 30 - int(time.time() - state["last"])
        state["time"] = max(remain, 0)

        if state["time"] <= 0:
            state["turn"] += 1
            state["last"] = time.time()
            state["time"] = 30

        socketio.emit("state", state)

socketio.start_background_task(timer_loop)

if __name__ == "__main__":
    socketio.run(app)
