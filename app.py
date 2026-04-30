from flask import Flask, render_template
import random
import requests

app = Flask(__name__)

# Riot Data Dragonから全チャンピオン取得
def get_all_champions():
    url = "https://ddragon.leagueoflegends.com/cdn/13.1.1/data/en_US/champion.json"
    data = requests.get(url).json()
    
    champs = list(data["data"].keys())
    return champs

@app.route("/")
def home():
    all_champs = get_all_champions()
    
    # ランダムで20体
    selected = random.sample(all_champs, 20)

    return render_template("index.html", champions=selected)

if __name__ == "__main__":
    app.run()