"""noteの公開記事のスキ・コメント数と、作品タグのページでの順位を毎日記録する。

公開APIだけを使う（ログインしない）。PVはログインが要るので、ここでは取らない（週1でオーナーのスクショから）。
使い方: python3 tools/snapshot.py
出力: records/stats/likes.csv（日付,記事キー,タイトル,スキ,コメント）
      records/stats/tagrank.csv（日付,タグ,記事キー,順位）… 作品タグの新着100件の中での順位
"""
import csv
import datetime
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "records" / "stats"
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def my_notes():
    notes, page = {}, 1
    while page <= 10:
        d = get(f"https://note.com/api/v2/creators/dramaclub/contents?kind=note&page={page}")["data"]
        for n in d["contents"]:
            notes[n["key"]] = n
        if d.get("isLastPage") or not d["contents"]:
            break
        page += 1
    return list(notes.values())


def append(path, header, rows):
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    notes = my_notes()
    append(OUT / "likes.csv", ["date", "key", "title", "likes", "comments"],
           [[TODAY, n["key"], n["name"], n.get("likeCount", 0), n.get("commentCount", 0)] for n in notes])
    # 作品タグ（#第N話 を除いた作品名タグ）ごとに、新着100件の中で自分の記事が何位か
    tags = {}
    for n in notes:
        for h in n.get("hashtags", []):
            name = h["hashtag"]["name"].lstrip("#")
            if "第" in name or name in ("ネタバレ", "ドラマ感想文", "テレビドラマ感想文", "ドラマ倶楽部"):
                continue
            tags.setdefault(name, set()).add(n["key"])
    rows = []
    for tag, keys in sorted(tags.items()):
        try:
            found = []
            for page in (1, 2, 3, 4, 5):
                d = get(f"https://note.com/api/v3/hashtags/{urllib.parse.quote(tag)}/notes?order=new&page={page}")
                found += [x["key"] for x in d["data"]["notes"]]
            for k in keys:
                rows.append([TODAY, tag, k, found.index(k) + 1 if k in found else ""])
        except Exception as e:  # タグが取れなくても全体は止めない
            rows.append([TODAY, tag, "", f"error:{e.__class__.__name__}"])
    append(OUT / "tagrank.csv", ["date", "tag", "key", "rank_in_new100"], rows)
    print(f"{TODAY}: {len(notes)} notes, {len(rows)} tag rows")


if __name__ == "__main__":
    main()
