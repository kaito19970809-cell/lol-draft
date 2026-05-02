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

# ---------- ティア確率 ----------
TIER_DISTRIBUTION = {
    "S": 0.15,
    "A": 0.35,
    "B": 0.35,
    "C": 0.15
}

# ---------- ロール目標 ----------
ROLE_TARGET = {
    "TOP": 2,
    "JG": 2,
    "MID": 2,
    "ADC": 2,
    "SUP": 2
}

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
        "used": set(),
        "time": 30,
        "last": time.time(),
        "done": False
    }

# ---------- ティア抽選 ----------
def pick_tier():
    r = random.random()
    total = 0
    for t, w in TIER_DISTRIBUTION.items():
        total += w
        if r <= total:
            return t
    return "B"

# ---------- ロールカウント ----------
def count_roles(result):
    count = {"TOP":0,"JG":0,"MID":0,"ADC":0,"SUP":0}
    for name in result:
        champ = next(c for c in champions if c["name"] == name)
        for r in champ["roles"]:
            count[r] += 1
    return count

# ---------- パック生成 ----------
def create_pack(state):
    result = []

    while len(result) < 10:
        role_count = count_roles(result)

        need_roles = [r for r in ROLE_TARGET if role_count[r] < ROLE_TARGET[r]]

        if need_roles:
            target_role = random.choice(need_roles)

            cands = [
                c for c in champions
                if target_role in c["roles"]
                and c["name"] not in state["used"]
                and c["name"] not in result
            ]
        else:
            tier = pick_tier()

            cands = [
                c for c in champions
                if c["tier"] == tier
                and c["name"] not in state["used"]
                and c["name"] not in result
            ]

        # フォールバック
        if not cands:
            cands = [
                c for c in champions
                if c["name"] not in state["used"]
                and c["name"] not in result
            ]

        if not cands:
            break

        pick = random.choice(cands)
        result.append(pick["name"])
        state["used"].add(pick["name"])

    return result

def start_round(state):
    state["packs"]["P1"] = create_pack(state)
    state["packs"]["P2"] = create_pack(state)
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# ---------- ルート ----------
@app.route("/")
def home():
    return "OK"

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
