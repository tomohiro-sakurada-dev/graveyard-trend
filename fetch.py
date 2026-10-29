import json, os, datetime, urllib.request, urllib.parse

def req(url, data=None, token=None):
    h = {"Accept": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    if data is not None:
        data = json.dumps(data).encode(); h["Content-Type"] = "application/json"
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h)) as f:
        return json.load(f)

token = req("https://osu.ppy.sh/oauth/token", {
    "client_id": int(os.environ["OSU_CLIENT_ID"]),
    "client_secret": os.environ["OSU_CLIENT_SECRET"],
    "grant_type": "client_credentials", "scope": "public"})["access_token"]

maps, cursor = {}, None
for _ in range(20):  # 50件×20ページ＝上位1000件
    q = {"s": "graveyard", "sort": "plays_desc", "m": "0"}
    if cursor: q["cursor_string"] = cursor
    res = req("https://osu.ppy.sh/api/v2/beatmapsets/search?" + urllib.parse.urlencode(q), token=token)
    for s in res["beatmapsets"]:
        maps[str(s["id"])] = {"t": f'{s["artist"]} - {s["title"]}'.replace("|", "/"),
                              "c": s["creator"], "p": s["play_count"]}
    cursor = res.get("cursor_string")
    if not cursor: break

today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
os.makedirs("data", exist_ok=True)
json.dump(maps, open(f"data/{today}.json", "w"), ensure_ascii=False)

files = sorted(os.listdir("data"))
out = [f"# Graveyard 伸びてるランキング（{today}）\n"]
if len(files) >= 2:
    old = json.load(open("data/" + files[-2]))
    diff = sorted(((m["p"] - old[i]["p"], i, m) for i, m in maps.items() if i in old), reverse=True)[:50]
    out.append("| 順位 | +プレイ | マップ | mapper |\n|---|---|---|---|")
    for n, (d, i, m) in enumerate(diff, 1):
        out.append(f'| {n} | +{d} | [{m["t"]}](https://osu.ppy.sh/beatmapsets/{i}) | {m["c"]} |')
else:
    out.append("明日から差分が出ます。")
open("README.md", "w").write("\n".join(out))
