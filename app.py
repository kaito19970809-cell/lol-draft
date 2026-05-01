from flask import Flask, render_template
import random
import json

app = Flask(__name__)

# champions.json 読み込み
with open("champions.json", encoding="utf-8") as f:
    all_champs = json.load(f)

# ======================
# 🔥 プレイヤーデータ（ここだけ見ればOK）
# ======================
players = [
    {"name": "A", "power": {"TOP":80,"JG":50,"MID":70,"ADC":40,"SUP":60}},
    {"name": "B", "power": {"TOP":60,"JG":80,"MID":50,"ADC":70,"SUP":40}},
    {"name": "C", "power": {"TOP":50,"JG":60,"MID":90,"ADC":40,"SUP":50}},
    {"name": "D", "power": {"TOP":40,"JG":50,"MID":60,"ADC":85,"SUP":45}},
    {"name": "E", "power": {"TOP":55,"JG":45,"MID":50,"ADC":60,"SUP":80}},
    {"name": "F", "power": {"TOP":85,"JG":40,"MID":60,"ADC":50,"SUP":45}},
    {"name": "G", "power": {"TOP":45,"JG":75,"MID":55,"ADC":50,"SUP":60}},
    {"name": "H", "power": {"TOP":50,"JG":60,"MID":88,"ADC":45,"SUP":50}},
    {"name": "I", "power": {"TOP":40,"JG":55,"MID":50,"ADC":78,"SUP":60}},
    {"name": "J", "power": {"TOP":60,"JG":50,"MID":55,"ADC":45,"SUP":85}},
]

# ======================
# 🔥 チーム分け（触らなくてOK）
# ======================
def balance_by_role(players):
    roles = ["TOP","JG","MID","ADC","SUP"]

    teamA = []
    teamB = []

    used = set()

    for role in roles:
        sorted_players = sorted(
            [p for p in players if p["name"] not in used],
            key=lambda x: x["power"][role],
            reverse=True
        )

        if len(sorted_players) >= 1:
            teamA.append({"player": sorted_players[0], "role": role})
            used.add(sorted_players[0]["name"])

        if len(sorted_players) >= 2:
            teamB.append({"player": sorted_players[1], "role": role})
            used.add(sorted_players[1]["name"])

    return teamA, teamB

# ======================
# 🔥 チャンプ生成（そのまま）
# ======================
def pick_role(role, count, selected):
    pool = [c["name"] for c in all_champs if role in c["roles"] and c["name"] not in selected]
    return random.sample(pool, count)

def pick_flex(count, selected):
    pool = [c["name"] for c in all_champs if len(c["roles"]) >= 2 and c["name"] not in selected]
    count = min(count, len(pool))
    return random.sample(pool, count)

# ======================
# 🔥 メイン
# ======================
@app.route("/")
def home():
    selected = []

    # チャンプ生成
    for role in ["TOP","JG","MID","ADC","SUP"]:
        picks = pick_role(role, 5, selected)
        selected.extend(picks)

    flex = pick_flex(5, selected)
    selected.extend(flex)

    random.shuffle(selected)

    # 🔥 チーム分け
    teamA, teamB = balance_by_role(players)

    return render_template(
        "index.html",
        champions=selected,
        teamA=teamA,
        teamB=teamB
    )

if __name__ == "__main__":
    app.run()