from flask import Flask, render_template, request

app = Flask(__name__)

players = []
picks = {}  # {プレイヤー名: チャンピオン}
champions = [champions = [
    "Ahri", "Zed", "Lux", "Yasuo", "Jinx",
    "LeeSin", "Thresh", "Ezreal", "Katarina", "Darius",
    "Fiora", "Akali", "Vayne", "Riven", "Sylas",
    "Orianna", "Leona", "Draven", "Zyra", "Ekko"
]]

turn = 0

@app.route("/", methods=["GET", "POST"])
def home():
    global turn

    if request.method == "POST":

        # プレイヤー追加
        if "add_player" in request.form:
            name = request.form.get("name")
            if name:
                players.append(name)

        # ピック
        elif "pick" in request.form:
            if turn < len(players):
                champ = request.form.get("champion")
                player = players[turn]
                picks[player] = champ
                turn += 1

    return render_template(
        "index.html",
        players=players,
        picks=picks,
        champions=champions,
        turn=turn
    )

if __name__ == "__main__":
    app.run()