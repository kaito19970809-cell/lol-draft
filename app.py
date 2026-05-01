from flask import Flask, render_template, redirect
from flask_socketio import SocketIO, emit, join_room
import random, string, json, secrets

app = Flask(__name__)
socketio = SocketIO(app)

rooms = {}

def create_room_id():
    return ''.join(random.choices(string.ascii_uppercase, k=4))

def create_key():
    return secrets.token_hex(4)

def create_state():
    return {
        "turn": 0,
        "sequence": [
            "blue-ban","red-ban","blue-ban","red-ban",
            "blue-pick","red-pick","red-pick","blue-pick",
            "blue-pick","red-pick","red-pick","blue-pick"
        ],
        "bluePicks": [],
        "redPicks": [],
        "blueBan": [],
        "redBan": []
    }

with open("champions.json", encoding="utf-8") as f:
    champs = json.load(f)

def generate_pool():
    return random.sample([c["name"] for c in champs], 30)

@app.route("/create")
def create():
    room_id = create_room_id()
    key = create_key()

    rooms[room_id] = {
        "key": key,
        "state": create_state(),
        "pool": generate_pool()
    }

    print(f"ROOM: {room_id} KEY: {key}")
    return redirect(f"/room/{room_id}?key={key}")

@app.route("/room/<room_id>")
def room(room_id):
    if room_id not in rooms:
        return "Room not found"

    return render_template("index.html",
        room_id=room_id,
        champions=rooms[room_id]["pool"]
    )

@socketio.on("join")
def on_join(data):
    room_id = data["room"]
    join_room(room_id)

    if room_id in rooms:
        emit("update", rooms[room_id]["state"])

@socketio.on("action")
def action(data):
    room_id = data["room"]
    key = data.get("key")

    room = rooms.get(room_id)
    if not room:
        return

    if key != room["key"]:
        return

    state = room["state"]

    if state["turn"] >= len(state["sequence"]):
        return

    champ = data["champ"]
    step = state["sequence"][state["turn"]]
    team = step.split("-")[0]

    if "ban" in step:
        state[team+"Ban"].append(champ)
    else:
        state[team+"Picks"].append(champ)

    state["turn"] += 1

    emit("update", state, to=room_id)

@socketio.on("undo")
def undo(data):
    room_id = data["room"]
    key = data.get("key")

    room = rooms.get(room_id)
    if key != room["key"]:
        return

    state = room["state"]

    if state["turn"] <= 0:
        return

    state["turn"] -= 1
    step = state["sequence"][state["turn"]]
    team = step.split("-")[0]

    if "ban" in step and state[team+"Ban"]:
        state[team+"Ban"].pop()
    elif state[team+"Picks"]:
        state[team+"Picks"].pop()

    emit("update", state, to=room_id)

if __name__ == "__main__":
    socketio.run(app, debug=True)