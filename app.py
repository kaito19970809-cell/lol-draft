from flask import Flask, render_template
import random
import requests

app = Flask(__name__)

def get_roles():
    url = "https://ddragon.leagueoflegends.com/cdn/latest/data/en_US/champion.json"
    data = requests.get(url).json()["data"]

    roles = {
        "TOP": [],
        "JG": [],
        "MID": [],
        "ADC": [],
        "SUP": [],
        "FLEX": []
    }

    for champ_name, champ_data in data.items():
        tags = champ_data["tags"]

        # 簡易分類（後で精度上げれる）
        if "Fighter" in tags or "Tank" in tags:
            roles["TOP"].append(champ_name)

        if "Assassin" in tags:
            roles["JG"].append(champ_name)

        if "Mage" in tags:
            roles["MID"].append(champ_name)

        if "Marksman" in tags:
            roles["ADC"].append(champ_name)

        if "Support" in tags:
            roles["SUP"].append(champ_name)

        # FLEX（複数タグ持ちを優先）
        if len(tags) >= 2:
            roles["FLEX"].append(champ_name)

    return roles


@app.route("/")
def home():
    roles = get_roles()

    selected = []

    def pick_unique(pool, count, selected):
        result = []
        while len(result) < count:
            champ = random.choice(pool)
            if champ not in selected and champ not in result:
                result.append(champ)
        return result

    # 各ロール5体ずつ
    for role in ["TOP","JG","MID","ADC","SUP","FLEX"]:
        picks = pick_unique(roles[role], 5, selected)
        selected.extend(picks)

    random.shuffle(selected)

    return render_template("index.html", champions=selected)


if __name__ == "__main__":
    app.run()