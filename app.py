from flask import Flask, render_template
import json, itertools, random

app = Flask(__name__)

roles = ["TOP","JG","MID","ADC","SUP"]

# プレイヤー
with open("players.json", encoding="utf-8") as f:
    players = json.load(f)

# チャンピオン
with open("champions.json", encoding="utf-8") as f:
    champs = json.load(f)

def generate_pool():
    return random.sample([c["name"] for c in champs], 30)

# ロール最適化
def best_role_assignment(team):
    best_score = -1
    best_assign = None

    for perm in itertools.permutations(roles):
        score = sum(p["power"][r] for p, r in zip(team, perm))
        assign = [{"player":p,"role":r} for p,r in zip(team,perm)]

        if score > best_score:
            best_score = score
            best_assign = assign

    return best_assign, best_score

# 最強チーム分け
def make_teams(players):
    best_diff = 999999
    bestA, bestB = None, None

    for comb in itertools.combinations(players,5):
        teamA = list(comb)
        teamB = [p for p in players if p not in teamA]

        A, scoreA = best_role_assignment(teamA)
        B, scoreB = best_role_assignment(teamB)

        diff = abs(scoreA-scoreB)

        if diff < best_diff:
            best_diff = diff
            bestA, bestB = A, B

    return bestA, bestB

@app.route("/")
def home():
    teamA, teamB = make_teams(players)
    pool = generate_pool()

    return render_template(
        "index.html",
        teamA=teamA,
        teamB=teamB,
        champions=pool
    )

if __name__ == "__main__":
    app.run(debug=True)