import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

PACK_SIZE = 10
TOTAL_ROUNDS = 3

orders = [
 ["blue","red","red","blue","blue","red","red","blue","blue","red"],
 ["red","blue","blue","red","red","blue","blue","red","red","blue"],
 ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]

state = {}
used = set()

def reset_state():
    global state, used
    used = set()
    state = {
        "started": False,
        "ready": {"blue": False, "red": False},  # ★追加
        "round": 1,
        "turn": 0,
        "pack": [],
        "picks": {"blue": [], "red": []},
        "time": 30,
        "last": time.time()
    }

reset_state()

def create_pack():
    global used
    pool = [c for c in champions if c["name"] not in used]

    if len(pool) < PACK_SIZE:
        used = set()
        pool = champions.copy()

    pack = random.sample(pool, PACK_SIZE)

    for c in pack:
        used.add(c["name"])

    return pack

def start_round():
    state["pack"] = create_pack()
    state["turn"] = 0
    state["time"] = 30
    state["last"] = time.time()

# ---------- routes ----------
@app.route("/")
def home():
    return "OK"

@app.route("/blue")
def blue():
    return render_template("index.html", role="blue")

@app.route("/red")
def red():
    return render_template("index.html", role="red")

# ---------- socket ----------
@socketio.on("connect")
def connect():
    emit("state", state)

@socketio.on("start")
def start(data):
    role = data["role"]

    state["ready"][role] = True

    # 両方押したら開始
    if state["ready"]["blue"] and state["ready"]["red"]:
        state["started"] = True
        state["round"] = 1
        state["picks"] = {"blue": [], "red": []}
        start_round()

    emit("state", state, broadcast=True)

@socketio.on("reset")
def reset():
    reset_state()
    emit("state", state, broadcast=True)

@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if not state["started"]:
        return

    order = orders[state["round"]-1]

    # ★ 修正：>= を消す
    if state["turn"] >= len(order):
        return

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

    # ★ パックが空で判定（これが重要）
    if len(state["pack"]) == 0:
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

        if remain <= 0:
            state["turn"] += 1
            state["last"] = time.time()
            state["time"] = 30
        else:
            state["time"] = remain

        # ★ 必ず毎秒送る
        socketio.emit("state", state)

socketio.start_background_task(timer)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
