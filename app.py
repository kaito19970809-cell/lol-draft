from flask import Flask, render_template
import random
import json

app = Flask(__name__)

# champions.json 読み込み
with open("champions.json", encoding="utf-8") as f:
    all_champs = json.load(f)

# ロールごとにピック
def pick_role(role, count, selected):
    pool = []

    for c in all_champs:
        if role in c["roles"] and c["name"] not in selected:
            pool.append(c["name"])

    return random.sample(pool, count)

# FLEXピック（2ロール以上）
def pick_flex(count, selected):
    pool = []

    for c in all_champs:
        if len(c["roles"]) >= 2 and c["name"] not in selected:
            pool.append(c["name"])

    # エラー防止
    count = min(count, len(pool))

    return random.sample(pool, count)

@app.route("/")
def home():
    selected = []

    # 各ロール5体ずつ
    for role in ["TOP","JG","MID","ADC","SUP"]:
        picks = pick_role(role, 5, selected)
        selected.extend(picks)

    # FLEX 5体
    flex = pick_flex(5, selected)
    selected.extend(flex)

    # シャッフル
    random.shuffle(selected)

    return render_template("index.html", champions=selected)

if __name__ == "__main__":
    app.run()