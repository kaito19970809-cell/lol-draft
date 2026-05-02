import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

print("=== APP START ===")

# チャンピオン読み込み
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

# DataDragon用にimageを自動生成
for c in champions:
    c["image"] = c["名前"]

print("Loaded champions:", len(champions))


# ---------------- 状態 ----------------
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

orders = [
    ["blue","red","red","blue","blue","red","red","blue","blue","red"],
    ["red","blue","blue","red","red","blue","blue","red","red","blue"],
    ["blue","red","red","blue","blue","red","red","blue","blue","red"]
]


# ---------------- ルーティング ----------------
@app.route("/blue")
def blue():
    return render_template("index.html", role="blue")

@app.route("/red")
def red():
    return render_template("index.html", role="red")


# ---------------- ゲーム開始 ----------------
@socketio.on("ready")
def ready(data):
    role = data["role"]
    state["ready"][role] = True

    if state["ready"]["blue"] and state["ready"]["red"]:
        start_game()

    emit("state", state, broadcast=True)


def start_game():
    state["started"] = True
    state["round"] = 1
    state["turn"] = 0
    state["time"] = 30
    state["picks"] = {"blue": [], "red": []}

    # 重複なし30体
    pool = random.sample(champions, 30)

    state["packs"] = [
        pool[0:10],
        pool[10:20],
        pool[20:30]
    ]

    state["pack"] = state["packs"][0]

    socketio.start_background_task(timer_loop)


# ---------------- タイマー ----------------
def timer_loop():
    while state["started"]:
        socketio.sleep(1)
        state["time"] -= 1

        if state["time"] <= 0:
            auto_pick()

        socketio.emit("state", state)


def auto_pick():
    if not state["pack"]:
        return

    champ = state["pack"][0]
    do_pick(champ["名前"])


# ---------------- ピック ----------------
@socketio.on("pick")
def pick(data):
    role = data["role"]
    champ = data["champ"]

    current = orders[state["round"]-1][state["turn"]]

    if role != current:
        return

    do_pick(champ)


def do_pick(name):
    champ = next((c for c in state["pack"] if c["名前"] == name), None)
    if not champ:
        return

    team = orders[state["round"]-1][state["turn"]]

    state["picks"][team].append(champ)
    state["pack"].remove(champ)

    state["turn"] += 1
    state["time"] = 30

    # ラウンド終了処理
    if state["turn"] >= 10:
        state["round"] += 1
        state["turn"] = 0

        if state["round"] <= 3:
            state["pack"] = state["packs"][state["round"]-1]
        else:
            state["started"] = False

    socketio.emit("state", state)


# ---------------- リセット ----------------
@socketio.on("reset")
def reset():
    state.update({
        "started": False,
        "ready": {"blue": False, "red": False},
        "round": 1,
        "turn": 0,
        "time": 30,
        "packs": [],
        "pack": [],
        "picks": {"blue": [], "red": []}
    })

    socketio.emit("state", state)


# ---------------- 起動 ----------------
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)
