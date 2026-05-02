import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------- データ ----------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

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

orders = [
    ["P1","P2","P2","P1","P1","P2","P2","P1","P1","P2"],
    ["P2","P1","P1","P2","P2","P1","P1","P2","P2","P1"],
    ["P1","P2","P1","P2","P1","P2","P1","P2","P1","P2"]
]

rooms = {}

def new_state():
    return {
        "round": 0,
        "turn": 0,
        "packs": {"P1": [], "P2": []},
        "picks": {"P1": [], "P2": []},
        "time": 30,
        "last": time.time(),
        "done": False
    }

def start_round(state):
    state["packs"]["P1"] = create_pack()
    state["packs"]["P2"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# ---------- ルート ----------
@app.route("/")
def home():
    return "Server OK"

@app.route("/lobby/<room>")
def lobby(room):
    if room not in rooms:
        rooms[room] = new_state()
    return render_template("lobby.html", room=room)

@app.route("/room/<room>")
def room(room):
    return render_template("index.html", room=room)

# ---------- 接続 ----------
@socketio.on("connect")
def connect():
    room = request.args.get("room")

    if room not in rooms:
        rooms[room] = new_state()

    join_room(room)
    state = rooms[room]

    if state["round"] == 0:
        state["round"] = 1
        start_round(state)

    emit("state", state, room=room)

# ---------- ピック ----------
@socketio.on("pick")
def pick(data):
    room = request.args.get("room")
    state = rooms[room]

    champ = data["champ"]

    current = orders[state["round"]-1][state["turn"]]
    player = current

    if champ not in state["packs"][player]:
        return

    state["packs"][player].remove(champ)
    state["picks"][player].append(champ)

    other = "P2" if player=="P1" else "P1"
    state["packs"][other].append(champ)

    state["turn"] += 1
    state["time"] = 30
    state["last"] = time.time()

    if state["turn"] >= 10:
        if state["round"] < 3:
            state["round"] += 1
            start_round(state)
        else:
            state["done"] = True

    socketio.emit("state", state, room=room)

# ---------- タイマー ----------
def timer_loop():
    while True:
        socketio.sleep(1)

        for room, state in rooms.items():
            remain = 30 - int(time.time() - state["last"])

            if remain != state["time"]:
                state["time"] = max(remain,0)

                if state["time"] <= 0:
                    state["turn"] += 1
                    state["last"] = time.time()
                    state["time"] = 30

                socketio.emit("state", state, room=room)

socketio.start_background_task(timer_loop)

if __name__ == "__main__":
    socketio.run(app)
