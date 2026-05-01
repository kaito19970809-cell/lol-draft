from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json, random, itertools

app = Flask(__name__)
socketio = SocketIO(app)

# ---------- データ ----------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

with open("players.json", encoding="utf-8") as f:
    players_data = json.load(f)

players = [p["name"] for p in players_data]

# ---------- チーム分け（ロール最適化） ----------
def best_layout(team, roles):
    best_score = -1
    best_assign = None

    for perm in itertools.permutations(team):
        score = 0
        assign = {}

        for i, player in enumerate(perm):
            pdata = next(p for p in players_data if p["name"] == player)
            role = roles[i]
            power = pdata["roles"][role]
            score += power
            assign[role] = {"player": player, "power": power}

        if score > best_score:
            best_score = score
            best_assign = assign

    return best_score, best_assign


def balance_teams():
    roles = ["TOP","JG","MID","ADC","SUP"]
    best = None
    best_score = -1

    for comb in itertools.combinations(players, 5):
        A = list(comb)
        B = [p for p in players if p not in A]

        scoreA, layoutA = best_layout(A, roles)
        scoreB, layoutB = best_layout(B, roles)

        total = scoreA + scoreB

        if total > best_score:
            best_score = total
            best = {
                "blue": layoutA,
                "red": layoutB
            }

    return best

# ---------- フレックス制御 ----------
def flex_weight(c):
    n = len(c["roles"])
    return 1.0 if n==1 else 0.6 if n==2 else 0.3

# ---------- ロール補正 ----------
ROLE_WEIGHT = {
    "TOP":1.0,"JG":1.0,"MID":1.0,"ADC":1.6,"SUP":1.1
}

def role_weight(c):
    return max(ROLE_WEIGHT.get(r,1.0) for r in c["roles"])

# ---------- 最終重み ----------
def final_weight(c):
    tier_w = {"S":0.7,"A":1.0,"B":1.2,"C":1.5}
    return tier_w[c["tier"]] * flex_weight(c) * role_weight(c)

def weighted_choice(cands):
    ws = [final_weight(c) for c in cands]
    total = sum(ws)
    r = random.uniform(0,total)
    s = 0
    for c,w in zip(cands,ws):
        s+=w
        if s>=r:
            return c
    return random.choice(cands)

# ---------- パック生成（大会仕様） ----------
def create_packs():
    roles = ["TOP","JG","MID","ADC","SUP"]
    packs = {}

    for p in players:
        pack=[]
        used=set()

        role_need={r:2 for r in roles}
        tier_need={"S":2,"A":3,"B":4,"C":1}

        for role in roles:
            for _ in range(2):
                cands=[c for c in champions
                       if role in c["roles"]
                       and c["tier"] in tier_need
                       and tier_need[c["tier"]]>0
                       and c["name"] not in used]

                if not cands:
                    continue

                pick=weighted_choice(cands)
                pack.append(pick)
                used.add(pick["name"])
                tier_need[pick["tier"]]-=1

        # ティア補充
        for t,n in tier_need.items():
            for _ in range(n):
                cands=[c for c in champions
                       if c["tier"]==t and c["name"] not in used]
                if cands:
                    pick=weighted_choice(cands)
                    pack.append(pick)
                    used.add(pick["name"])

        packs[p]=[c["name"] for c in pack[:10]]

    return packs

# ---------- 状態 ----------
state = {
    "turn":0,
    "picks":{},
    "packs":{},
    "teams":{},
    "time":30
}

# ---------- ルート ----------
@app.route("/")
def index():
    return render_template("index.html", players=players)

# ---------- 接続 ----------
@socketio.on("connect")
def connect():
    state["teams"]=balance_teams()
    state["packs"]=create_packs()
    state["picks"]={p:[] for p in players}
    state["turn"]=0
    emit("state",state)

# ---------- ピック ----------
@socketio.on("pick")
def pick(data):
    player=data["player"]
    champ=data["champ"]

    current=players[state["turn"]%len(players)]

    if player!=current:
        return

    if champ not in state["packs"][player]:
        return

    state["packs"][player].remove(champ)
    state["picks"][player].append(champ)
    state["turn"]+=1

    emit("state",state,broadcast=True)

# ---------- 起動 ----------
if __name__=="__main__":
    socketio.run(app)