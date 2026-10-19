"""noteの見出し画像（1280×670）を作る。

使い方:
  python3 design/make_header.py <作品キー> "<帯の文字>" <出力先.png> [--mark 21]

作品ごとの色と放送枠は design/shows.json に書く。
感想の画像は --mark で話数の透かし（#N）を入れる（このとき斜めの帯は入れない）。
96px・211px に縮めたプレビューも同じフォルダに書き出す。
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
W, H = 1280, 670
SANS = HERE / "fonts" / "NotoSansJP.ttf"
SERIF = HERE / "fonts" / "NotoSerifJP.ttf"
# 作品名の書体（shows.json の "font"）。axes は可変フォントの軸の値
TITLE_FONTS = {
    "serif": (SERIF, [900]),
    "sans": (SANS, [900]),
    "rounded": (HERE / "fonts" / "MPLUSRounded1c-Black.ttf", None),
    "archivo": (HERE / "fonts" / "Archivo.ttf", [900, 125]),  # 太さ900・幅125
}


def font(path, size, weight=None, axes=None):
    f = ImageFont.truetype(str(path), size)
    if axes or weight:
        f.set_variation_by_axes(axes or [weight])
    return f


def title_font(kind, size):
    path, axes = TITLE_FONTS[kind]
    return font(path, size, axes=axes)


def contrast(a, b):
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    l1, l2 = sorted([lum(a), lum(b)], reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def make(show, label, out, mark=None):
    s = json.loads((HERE / "shows.json").read_text(encoding="utf-8"))[show]
    im = Image.new("RGB", (W, H), s["bg"])
    d = ImageDraw.Draw(im)

    # 大きな色面は1つだけ：感想（話数あり）は話数の透かし、それ以外は斜めの帯
    if mark:
        f = font(SANS, 560, 900)
        text = f"#{mark}"
        # 2桁は左端320から右へはみ出す。1桁は右端が1215にそろう（これまでの画像と同じ位置）
        x = max(320, 1215 - d.textlength(text, font=f))
        d.text((x, 300), text, font=f, fill=s.get("mark", s.get("diagonal")), anchor="lt")
    elif s.get("diagonal"):
        d.polygon([(665, 0), (W, 0), (W, H), (385, H)], fill=s["diagonal"])

    small = font(SANS, 36, 700)
    d.text((70, 82), "ドラマ倶楽部", font=small, fill=s["sub"], anchor="lm")
    d.text((1215, 82), s["slot"], font=small, fill=s["sub"], anchor="rm")

    # 作品名：最大150px。改行（\n）で2行にできる。横幅1140pxに収まるまで小さくする
    title = s["title"]
    kind = s.get("font", "serif")
    size = s.get("title_size", 150)
    while True:
        tf = title_font(kind, size)
        if max(d.textlength(line, font=tf) for line in title.split("\n")) <= 1140 or size <= 60:
            break
        size -= 4
    d.multiline_text((W // 2, 335), title, font=tf, fill=s["fg"], anchor="mm", align="center", spacing=size * 0.12)

    bf = font(SANS, 46, 700)
    tw = d.textlength(label, font=bf)
    bw, bh = tw + 110, 82
    x0, y0 = (W - bw) / 2, 570 - bh / 2
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=bh / 2, fill=s["accent"])
    d.text((W // 2, 570), label, font=bf, fill=s["on_accent"], anchor="mm")

    out = Path(out)
    im.save(out)
    for w in (96, 211):
        im.resize((w, round(H * w / W)), Image.LANCZOS).save(out.with_name(f"{out.stem}_{w}px.png"))
    print(f"{out}  主役の文字のコントラスト比 {contrast(s['fg'], s['bg']):.1f}:1")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("show")
    p.add_argument("label")
    p.add_argument("out")
    p.add_argument("--mark")
    a = p.parse_args()
    make(a.show, a.label, a.out, a.mark)
