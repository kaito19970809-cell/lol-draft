from flask import Flask, render_template
import random

app = Flask(__name__)

champions = [
    "Ahri", "Yasuo", "Zed", "Lux", "Ezreal", "Jinx", "Thresh", "LeeSin",
    "Katarina", "Darius", "Garen", "Ashe", "Vayne", "Riven", "Akali",
    "Sylas", "Kaisa", "Sett", "Yone", "Blitzcrank",
    "Orianna", "Fiora", "Camille", "Draven", "Samira"
]

@app.route("/")
def home():
    selected = random.sample(champions, 20)  # 重複なしで20体
    return render_template("index.html", champions=selected)

if __name__ == "__main__":
    app.run()