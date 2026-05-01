import requests
import json

URL = "https://ddragon.leagueoflegends.com/cdn/latest/data/en_US/champion.json"

data = requests.get(URL).json()["data"]

champions = []

def get_roles(tags):
    roles = []

    if "Marksman" in tags:
        roles.append("ADC")
    if "Support" in tags:
        roles.append("SUP")
    if "Mage" in tags:
        roles.append("MID")
    if "Assassin" in tags:
        roles.append("JG")
    if "Fighter" in tags or "Tank" in tags:
        roles.append("TOP")

    # 何も入らない保険
    if not roles:
        roles.append("FLEX")

    return list(set(roles))


for champ_name, champ_data in data.items():
    tags = champ_data["tags"]

    champ = {
        "name": champ_name,
        "roles": get_roles(tags),
        "tags": tags,
        "image": champ_name + ".png",
        "difficulty": 2,  # 仮
        "range": "ranged" if "Marksman" in tags or "Mage" in tags else "melee"
    }

    champions.append(champ)

# 保存
with open("champions.json", "w", encoding="utf-8") as f:
    json.dump(champions, f, indent=2, ensure_ascii=False)

print("champions.json 作成完了！")