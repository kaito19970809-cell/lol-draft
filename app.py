from flask import Flask, render_template
import random
import requests

app = Flask(__name__)

def get_roles():
    url = "https://ddragon.leagueoflegends.com/cdn/latest/data/en_US/champion.json"

    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()["data"]
    except:
        print("API失敗 → fallback使用")
        return {
            "TOP": ["Garen","Darius","Fiora","Camille","Sett"],
            "JG": ["LeeSin","XinZhao","JarvanIV","Vi","Warwick"],
            "MID": ["Ahri","Zed","Lux","Orianna","Syndra"],
            "ADC": ["Jinx","Ezreal","KaiSa","Vayne","Ashe"],
            "SUP": ["Thresh","Blitzcrank","Leona","Nami","Lulu"],
            "FLEX": ["Yasuo","Yone","Akali","Sylas","Riven"]
        }

    roles = {r: [] for r in ["TOP","JG","MID","ADC","SUP","FLEX"]}

    for name, info in data.items():
        tags = info["tags"]

        if "Fighter" in tags or "Tank" in tags:
            roles["TOP"].append(name)

        if "Assassin" in tags or "Fighter" in tags:
            roles["JG"].append(name)

        if "Mage" in tags or "Assassin" in tags:
            roles["MID"].append(name)

        if "Marksman" in tags:
            roles["ADC"].append(name)

        if "Support" in tags or "Mage" in tags:
            roles["SUP"].append(name)

        if len(tags) >= 2:
            roles["FLEX"].append(name)

    return roles


def pick_unique(pool, count, selected):
    available = list(set(pool) - set(selected))
    if not available:
        return []
    return random.sample(available, min(count, len(available)))


@app.route("/")
def home():
    roles = get_roles()
    selected = []

    for role in ["TOP","JG","MID","ADC","SUP","FLEX"]:
        picks = pick_unique(roles[role], 5, selected)
        selected.extend(picks)

    random.shuffle(selected)

    return render_template("index.html", champions=selected)


if __name__ == "__main__":
    app.run()