import random
import json

print("=== PACK GENERATOR START ===")

# -----------------
# 読み込み
# -----------------
with open("champions.json", encoding="utf-8") as f:
    champions = json.load(f)

# 画像キー生成
for c in champions:
    c["image"] = c["name"].replace(" ", "").replace("'", "")

# -----------------
# ティア重み
# -----------------
weights = {
    "S": 5,
    "A": 10,
    "B": 20,
    "C": 30,
    "D": 35
}

ROLES = ["TOP","JG","MID","ADC","SUP"]

# -----------------
# 重み抽選
# -----------------
def weighted_choice(candidates):
    pool = []
    for c in candidates:
        w = weights.get(c["tier"], 20)
        pool += [c] * w
    return random.choice(pool)

# -----------------
# 1パック生成（5体）
# -----------------
def generate_pack(pool):
    pack = []

    for role in ROLES:
        candidates = [c for c in pool if role in c["roles"]]

        if not candidates:
            raise Exception(f"{role}が足りない")

        chosen = weighted_choice(candidates)
        pack.append(chosen)
        pool.remove(chosen)

    return pack

# -----------------
# 6パック生成（30体）
# -----------------
def generate_all_packs():
    pool = champions.copy()
    random.shuffle(pool)

    packs = []

    for i in range(6):
        pack = generate_pack(pool)
        packs.append(pack)

    return packs

# -----------------
# テスト実行
# -----------------
if __name__ == "__main__":
    packs = generate_all_packs()

    for i, p in enumerate(packs):
        print(f"\n=== PACK {i+1} ===")
        for c in p:
            print(f"{c['name']} ({c['roles']}) [{c['tier']}]")
