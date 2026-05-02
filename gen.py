import requests
import json

print("開始：チャンピオン取得中...")

# ---------- 最新バージョン取得 ----------

ver = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]

# ---------- 全チャンピオン取得 ----------

champ_data = requests.get(
f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US/champion.json"
).json()["data"]

# ---------- 仮の統計データ（ここがティアの元） ----------

# ※今回はサンプル（後で差し替え可能）

stats = {
"Ahri": {"win": 51.2, "pick": 12},
"Azir": {"win": 49.5, "pick": 8},
"Jinx": {"win": 52.8, "pick": 18},
"LeeSin": {"win": 50.5, "pick": 20},
"Thresh": {"win": 50.2, "pick": 22}
}

# ---------- ロール変換 ----------

TAG_TO_ROLE = {
"Fighter": "TOP",
"Tank": "TOP",
"Mage": "MID",
"Assassin": "MID",
"Marksman": "ADC",
"Support": "SUP"
}

# ---------- ティア計算 ----------

def calc_tier(win, pick):
if win >= 52 and pick >= 10:
return "S"
elif win >= 50:
return "A"
elif win >= 48:
return "B"
else:
return "C"

champions = []

for champ in champ_data.values():
name = champ["id"]
tags = champ["tags"]

```
roles = list(set([TAG_TO_ROLE.get(t) for t in tags if TAG_TO_ROLE.get(t)]))

# 統計データ（なければ平均）
s = stats.get(name, {"win":50,"pick":5})

win = s["win"]
pick = s["pick"]

tier = calc_tier(win, pick)

champions.append({
    "name": name,
    "tier": tier,
    "roles": roles
})
```

# ---------- 保存 ----------

with open("champions.json", "w", encoding="utf-8") as f:
json.dump(champions, f, ensure_ascii=False, indent=2)

print("完了：champions.json 作成成功！")
