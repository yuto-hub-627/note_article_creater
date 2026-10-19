"""その日の入稿キット（HTML）を作る。

使い方: python3 tools/build_kit.py articles/2026-10-19

articles/<日付>/*.md（先頭に --- で囲んだ公開情報）と x/<日付>.md を読み、
コピーボタン付きのページを articles/<日付>/kit.html に書き出す。
"""
import base64
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse(md):
    _, meta, body = md.split("---", 2)
    info = {}
    for line in meta.strip().splitlines():
        k, v = line.split(":", 1)
        info[k.strip()] = v.strip().strip('"')
    return info, body.strip()


def inline(s):
    s = html.escape(s)
    return re.sub(r"(https?://\S+)", r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)


def to_html(body):
    out, items = [], []
    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()
    for line in body.splitlines():
        line = line.rstrip()
        if line.startswith("- "):
            items.append(line[2:]); continue
        flush()
        if not line:
            continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>")
        else:
            out.append(f"<p>{inline(line)}</p>")
    flush()
    return "\n".join(out)


def x_posts(path):
    if not path.exists():
        return []
    t = path.read_text(encoding="utf-8")
    return re.findall(r"^## (.+?)\n+```\n(.*?)```", t, re.S | re.M)


def main(day_dir):
    day = Path(day_dir)
    date = day.name
    arts = []
    for p in sorted(day.glob("*.md")):
        info, body = parse(p.read_text(encoding="utf-8"))
        img = day / info.get("見出し画像", "")
        data = base64.b64encode(img.read_bytes()).decode() if img.is_file() else ""
        arts.append((info, body, data))
    arts.sort(key=lambda a: a[0].get("公開", ""))
    # 仮の文が残ったままのキットは作らない（10/19 LOST10 で仮の文がそのまま公開された）
    for info, body, _ in arts:
        hit = re.search(r"公開後に入れる|\[[^\]]*URL\]|TODO", body)
        if hit:
            sys.exit(f"仮の文が残ってる：{info.get('タイトル')} … {hit.group(0)}")
    posts = x_posts(ROOT / "x" / f"{date}.md")

    cards = []
    for n, (info, body, data) in enumerate(arts):
        when = info.get("公開", "")
        cards.append(f"""
<section class="art" id="a{n}">
  <header class="art-head">
    <p class="when"><span class="time">{html.escape(when[-5:])}</span> 公開 <span class="date">{html.escape(when[:10])}</span></p>
    <h2 class="art-title">{html.escape(info.get('タイトル',''))}</h2>
  </header>
  <div class="grid">
    <figure class="eyecatch">{f'<img src="data:image/png;base64,{data}" alt="見出し画像">' if data else ''}
      <figcaption>見出し画像：{html.escape(info.get('見出し画像',''))}</figcaption></figure>
    <dl class="fields">
      <div><dt>タイトル</dt><dd><span class="val" id="t{n}">{html.escape(info.get('タイトル',''))}</span><button type="button" data-copy="t{n}">コピー</button></dd></div>
      <div><dt>タグ</dt><dd><span class="val" id="g{n}">{html.escape(info.get('タグ',''))}</span><button type="button" data-copy="g{n}">コピー</button></dd></div>
      <div><dt>マガジン</dt><dd><span class="val">{html.escape(info.get('マガジン',''))}</span></dd></div>
    </dl>
  </div>
  <div class="body-bar"><span>本文</span><button type="button" class="primary" data-rich="b{n}">本文をコピー</button></div>
  <article class="body" id="b{n}">{to_html(body)}</article>
</section>""")

    xs = "".join(f"""
<div class="post"><div class="post-head"><span>{html.escape(h)}</span><button type="button" data-copy="x{i}">コピー</button></div>
<pre class="val" id="x{i}">{html.escape(t.strip())}</pre></div>""" for i, (h, t) in enumerate(posts))

    page = TEMPLATE.replace("{{DATE}}", date).replace("{{CARDS}}", "\n".join(cards)).replace("{{XS}}", xs)
    out = day / "kit.html"
    out.write_text(page, encoding="utf-8")
    print(out)


TEMPLATE = r"""<title>ドラマ倶楽部 入稿キット</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Noto+Serif+JP:wght@700;900&display=swap">
<style>
/* 入稿伝票：記事ごとに1枚の伝票。上に公開時刻、左に見出し画像、右にコピー欄、下に本文 */
:root{
  --paper:#F6EEDF; --ink:#1F2F4A; --muted:#5D6678; --line:#D9CDB6; --card:#FFFBF3; --mustard:#E2A93B; --on-mustard:#1F2F4A;
  --serif:"Noto Serif JP","Hiragino Mincho ProN",serif; --sans:"Noto Sans JP","Hiragino Sans",system-ui,sans-serif;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--paper:#151C29;--ink:#EDE5D4;--muted:#A3AABA;--line:#2E3A50;--card:#1C2536;--mustard:#E8B651;--on-mustard:#151C29;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#151C29;--ink:#EDE5D4;--muted:#A3AABA;--line:#2E3A50;--card:#1C2536;--mustard:#E8B651;--on-mustard:#151C29;color-scheme:dark}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.7}
.wrap{max-width:980px;margin:0 auto;padding-block:28px 64px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:flex;flex-direction:column;gap:28px}
.top h1{font-family:var(--serif);font-weight:900;font-size:clamp(24px,4vw,34px);margin:0;text-wrap:balance}
.top p{margin:4px 0 0;color:var(--muted)}
.art{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:20px;display:flex;flex-direction:column;gap:16px;min-width:0}
.when{margin:0;color:var(--muted);font-size:13px;letter-spacing:.04em}
.time{font-family:var(--serif);font-weight:900;font-size:26px;color:var(--ink);font-variant-numeric:tabular-nums;margin-right:4px}
.art-title{font-family:var(--serif);font-size:clamp(18px,2.6vw,22px);margin:2px 0 0;text-wrap:balance}
.grid{display:grid;grid-template-columns:minmax(0,320px) minmax(0,1fr);gap:20px}
@media (max-width:680px){.grid{grid-template-columns:minmax(0,1fr)}}
.eyecatch{margin:0}.eyecatch img{display:block;width:100%;border:1px solid var(--line)}
figcaption{font-size:12px;color:var(--muted);margin-top:6px}
.fields{margin:0;display:flex;flex-direction:column;gap:12px;min-width:0}
.fields dt{font-size:12px;color:var(--muted);letter-spacing:.08em}
.fields dd{margin:2px 0 0;display:flex;gap:10px;align-items:flex-start}
.val{flex:1;min-width:0;overflow-wrap:anywhere}
button{font:inherit;font-size:13px;font-weight:700;color:var(--ink);background:transparent;border:1px solid var(--ink);border-radius:4px;padding:3px 12px;cursor:pointer;white-space:nowrap}
button.primary{background:var(--mustard);color:var(--on-mustard);border-color:var(--mustard);padding:6px 16px}
button:focus-visible{outline:2px solid var(--mustard);outline-offset:2px}
button.done{border-style:dashed}
.body-bar{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--line);padding-top:14px;font-size:12px;color:var(--muted);letter-spacing:.08em}
.body{max-width:40em;font-size:15px;min-width:0;overflow-wrap:anywhere}
.body h2{font-size:19px;margin:28px 0 8px;font-family:var(--serif)}
.body h3{font-size:16px;margin:20px 0 6px}
.body p{margin:0 0 10px}.body ul{margin:0 0 12px;padding-left:1.3em}
.body a{color:inherit}
.xs h2{font-family:var(--serif);font-size:20px;margin:0 0 10px}
.xs{display:flex;flex-direction:column;gap:12px}
.post{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px 16px}
.post-head{display:flex;justify-content:space-between;align-items:center;gap:10px;font-weight:700}
.post pre{white-space:pre-wrap;font-family:var(--sans);margin:8px 0 0}
.note{font-size:13px;color:var(--muted)}
</style>
<div class="wrap">
  <div class="top"><h1>入稿キット {{DATE}}</h1>
  <p>noteには「本文をコピー」で貼る。URLだけの行は、貼ったあとその行の末尾でEnterを押すとリンクカードになる。</p></div>
  {{CARDS}}
  <section class="xs"><h2>X 投稿</h2><p class="note">[URL] の部分は、noteを公開したらそのURLに差し替える。</p>{{XS}}</section>
</div>
<script>
function mark(b,ok){const t=b.textContent;b.textContent=ok?'コピーした':'選択した（Ctrl+C）';b.classList.add('done');setTimeout(()=>{b.textContent=t;b.classList.remove('done')},1600)}
function selectEl(el){const r=document.createRange();r.selectNodeContents(el);const s=getSelection();s.removeAllRanges();s.addRange(r)}
document.addEventListener('click',async e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.copy){const el=document.getElementById(b.dataset.copy);
    try{await navigator.clipboard.writeText(el.innerText);mark(b,true)}catch(_){selectEl(el);mark(b,false)}}
  if(b.dataset.rich){const el=document.getElementById(b.dataset.rich);
    try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([el.innerHTML],{type:'text/html'}),'text/plain':new Blob([el.innerText],{type:'text/plain'})})]);mark(b,true)}
    catch(_){selectEl(el);let ok=false;try{ok=document.execCommand('copy')}catch(__){}mark(b,ok)}}
});
</script>
"""

if __name__ == "__main__":
    main(sys.argv[1])
