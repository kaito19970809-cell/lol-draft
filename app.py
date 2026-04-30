from flask import Flask, render_template, request, redirect

app = Flask(__name__)

players = []

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        if name:
            players.append(name)
    return render_template("index.html", players=players)

if __name__ == "__main__":
    app.run()