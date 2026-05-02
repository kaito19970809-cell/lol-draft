import json
import random
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

print("=== APP START ===")

# =====================
# チャンピオン読み込み（完全耐性版）
# =====================
champions = []

try:
    with open("champions.json", encoding="utf-8") as f:
        data = json.load(f)

        for c in data:
            name = None

            # いろんなパターンに対応
            if isinstance(c, dict):
                name = c.get("名前") or c.get("name")

            elif isinstance(c, str):
                name = c

            if not name:
                continue

            champions.append({
                "name": name,
                "image": name  # DataDragon用
            })

    print("Loaded champions:", len(champions))

except Exception as e:
    print("ERROR loading champions:", e)


# =====================
# ゲーム状態
# =====================
state = {
    "started": False,
    "ready": {"blue": False, "red": False},
    "round": 1,
    "turn": 0,
    "time": 30,
    "packs": [],
    "pack": [],
    "picks": {"blue": [], "red": []}
}

timer_running = False


# =====================
# パック生成（重複なし30体）
# =====================
def generate_packs():
    pool = champions.copy()
    random.shuffle(pool)

    total = pool[:30]

    return [
        total[0:10],
        total[10:20],
        total[20:30]
    ]


# =====================
# タイマー
# =====================
def timer_loop():
    global timer_running

    while True:
        socketio.sleep(1)

        if not timer_running or not state["started"]:
            continue

        state["time"] -= 1

        if state["time"] <= 0:
            auto_pick()

        socketio.emit("state", state)


# =====================
# 自動ピック
# =====================
def auto_pick():
    if not state["pack"]:
        return

    champ = random.choice(state["pack"])
    do_pick(champ["name"])


# =====================
# ピック順
# =====================
orders = [
    ["blue","red","red","blue","blue","red","red","blue","blue","red"],
    ["red","blue","blue","red","red","blue","blue","red","red","blue"],
    ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]


# =====================
# ピック処理
# =====================
def do_pick(name):
    current_team = orders[state["round"]-1][state["turn"]]

    champ = next((c for c in state["pack"] if c["name"] == name), None)
    if not champ:
        return

    state["picks"][current_team].append(champ)
    state["pack"].remove(champ)

    state["turn"] += 1
    state["time"] = 30

    # ラウンド終了処理（★バグ修正済）
    if state["turn"] >= 10:
        if state["round"] >= 3:
            state["started"] = False
            global timer_running
            timer_running = False
        else:
            state["round"] += 1
            state["turn"] = 0
            state["pack"] = state["packs"][state["round"]-1]

    socketio.emit("state", state)


# =====================
# ルーティング
# =====================
@app.route("/<role>")
def index(role):
    return render_template("index.html", role=role)


# =====================
# Socket
# =====================
@socketio.on("connect")
def connect():
    emit("state", state)


@socketio.on("start")
def start(data):
    global timer_running

    role = data["role"]
    state["ready"][role] = True

    # 両方押したら開始
    if state["ready"]["blue"] and state["ready"]["red"]:
        state["packs"] = generate_packs()
        state["pack"] = state["packs"][0]

        state["started"] = True
        state["round"] = 1
        state["turn"] = 0
        state["time"] = 30
        state["picks"] = {"blue": [], "red": []}

        timer_running = True

    socketio.emit("state", state)


@socketio.on("pick")
def pick(data):
    role = data["role"]
    name = data["champ"]

    if not state["started"]:
        return

    current_team = orders[state["round"]-1][state["turn"]]

    if role != current_team:
        return

    do_pick(name)


@socketio.on("reset")
def reset():
    global timer_running

    state["started"] = False
    state["ready"] = {"blue": False, "red": False}
    state["round"] = 1
    state["turn"] = 0
    state["time"] = 30
    state["pack"] = []
    state["packs"] = []
    state["picks"] = {"blue": [], "red": []}

    timer_running = False

    socketio.emit("state", state)


# =====================
# 起動
# =====================
socketio.start_background_task(timer_loop)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
