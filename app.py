from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app)

# ---------- データ ----------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

# ---------- ティア重み ----------
TIER_WEIGHT = {"S":0.7,"A":1.0,"B":1.2,"C":1.5}

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

# ---------- パック生成 ----------
def create_pack():
    result = []
    used = set()

    tier_need = {"S":2,"A":3,"B":4,"C":1}

    for t,n in tier_need.items():
        for _ in range(n):
            cands = [c for c in champions if c["tier"]==t and c["name"] not in used]
            if cands:
                pick = weighted_choice(cands)
                result.append(pick["name"])
                used.add(pick["name"])

    return result

# ---------- ピック順 ----------
orders = [
    ["P1","P2","P2","P1","P1","P2","P2","P1","P1","P2"],
    ["P2","P1","P1","P2","P2","P1","P1","P2","P2","P1"],
    ["P1","P2","P1","P2","P1","P2","P1","P2","P1","P2"]
]

players = {"blue":"P1","red":"P2"}

# ---------- 状態 ----------
state = {
    "round": 0,
    "turn": 0,
    "packs": {"P1": [], "P2": []},
    "picks": {"P1": [], "P2": []},
    "time": 30,
    "last": time.time(),
    "done": False
}

def start_round():
    state["packs"]["P1"] = create_pack()
    state["packs"]["P2"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# ---------- ルート ----------
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
    if state["round"] == 0:
        state["round"] = 1
        start_round()
    emit("state", state)

# ---------- ピック ----------
@socketio.on("pick")
def pick(data):
    role = data["role"]
    champ = data["champ"]

    if role == "spec":
        return

    player = players[role]
    current = orders[state["round"]-1][state["turn"]]

    if player != current:
        return

    if champ not in state["packs"][player]:
        return

    state["packs"][player].remove(champ)
    state["picks"][player].append(champ)

    other = "P2" if player=="P1" else "P1"
    state["packs"][other].append(champ)

    state["turn"] += 1

    # タイマーリセット
    state["time"] = 30
    state["last"] = time.time()

    # パック終了
    if state["turn"] >= 10:
        if state["round"] < 3:
            state["round"] += 1
            start_round()
        else:
            state["done"] = True

    emit("state", state, broadcast=True)

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
    socketio.run(app)