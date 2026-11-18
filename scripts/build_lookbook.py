#!/usr/bin/env python3
"""Render a daily outfit lookbook HTML page from a looks.json config.

Images are embedded as base64 so the HTML is a single self-contained file that
opens correctly in any preview panel.

Usage:
    python build_lookbook.py looks.json out.html [--accent #1F3FBF]

looks.json schema:
{
  "date": "2026-11-18",
  "title": "今日穿搭 · 5 套上身方案",
  "subtitle": "one-line intro",
  "analysis": {
    "heading": "你的个人风格画像",
    "paragraphs": ["...", "..."],
    "palette": [{"hex": "#F2EBDD", "name": "奶油白"}, ...],
    "note": "身材要点 ..."
  },
  "looks": [
    {
      "name": "克莱因蓝毛衣 + 奶油百褶长裙",
      "tag": "法式复古 · 通勤约会两用",
      "inspo": "灵感库「黑×奶油撞色」思路，换成蓝×奶油",
      "image": "/abs/path/look_1.jpg",
      "items": [
        {"name": "...", "note": "衣柜收藏 ¥199 · 宽松落肩",
         "keyword": "克莱因蓝 V领 毛衣 女", "source": "cart"}
      ]
    }
  ],
  "footer": "optional footer line"
}

source values: owned | cart | buy  (badge: 已有 / 衣柜收藏 / 建议补)
"""
import argparse
import base64
import html
import json
import os
import sys
import urllib.parse

TAOBAO = "https://s.taobao.com/search?q="

BADGES = {
    "owned": ("已有", "b-owned"),
    "cart": ("衣柜收藏", "b-cart"),
    "buy": ("建议补", "b-buy"),
}

CSS = """
  :root {
    --bg:#FBFAF8; --card:#fff; --ink:#17181A; --ink-2:#5A5D63; --ink-3:#8E9199;
    --line:#E8E5DF; --accent:__ACCENT__; --warm:#B4553A; --cream:#F5F1EA;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;
    line-height:1.65; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1020px; margin:0 auto; padding:48px 24px 80px; }
  header { border-bottom:1px solid var(--line); padding-bottom:26px; margin-bottom:36px; }
  .kicker { font-size:12px; letter-spacing:.18em; color:var(--ink-3);
    text-transform:uppercase; margin-bottom:10px; }
  h1 { font-size:32px; line-height:1.25; margin:0 0 12px; letter-spacing:-.02em; }
  .sub { color:var(--ink-2); font-size:15px; max-width:680px; }
  .analysis { background:var(--card); border:1px solid var(--line);
    border-radius:18px; padding:26px 28px; margin-bottom:36px; }
  .analysis h2 { font-size:18px; margin:0 0 12px; }
  .analysis p { font-size:14px; color:var(--ink-2); margin:0 0 12px; }
  .palettes { display:flex; gap:10px; flex-wrap:wrap; margin:6px 0 4px; }
  .sw { display:flex; align-items:center; gap:8px; font-size:13px; color:var(--ink-2);
    background:var(--cream); border:1px solid var(--line); border-radius:999px;
    padding:5px 14px 5px 6px; }
  .dot { width:20px; height:20px; border-radius:50%; border:1px solid rgba(0,0,0,.08); }
  .look { background:var(--card); border:1px solid var(--line); border-radius:18px;
    padding:26px; margin-bottom:24px; }
  .look-grid { display:grid; grid-template-columns:320px 1fr; gap:26px; align-items:start; }
  .img-wrap { position:relative; }
  .img-wrap img { width:100%; border-radius:14px; display:block; }
  .img-badge { position:absolute; top:12px; left:12px; background:rgba(23,24,26,.82);
    color:#fff; font-size:12px; letter-spacing:.1em; padding:4px 12px; border-radius:999px; }
  .look h3 { font-size:20px; margin:2px 0 4px; letter-spacing:-.01em; }
  .look-tag { font-size:12px; color:var(--warm); letter-spacing:.06em; margin-bottom:12px; }
  .inspo { font-size:13px; color:var(--ink-2); background:var(--cream);
    border-radius:10px; padding:10px 14px; margin-bottom:14px; }
  .inspo span { color:var(--accent); font-weight:600; margin-right:8px;
    font-size:12px; letter-spacing:.06em; }
  table.items { width:100%; border-collapse:collapse; }
  th { text-align:left; font-size:11.5px; letter-spacing:.08em; color:var(--ink-3);
    font-weight:600; padding:8px 10px; background:#FCFBF9; border-bottom:1px solid var(--line); }
  td { padding:11px 10px; border-bottom:1px solid #F5F2ED; font-size:13.5px; vertical-align:top; }
  .in { font-weight:600; white-space:nowrap; }
  .b { font-size:11px; font-weight:600; border-radius:999px; padding:1px 9px;
    margin-left:8px; vertical-align:1px; white-space:nowrap; }
  .b-owned { background:#EAF3EC; color:#2E7D4F; }
  .b-cart { background:#EEF1FE; color:var(--accent); }
  .b-buy { background:#FBF1EC; color:var(--warm); }
  .is { color:var(--ink-3); font-size:12.5px; }
  .c-link a { color:var(--accent); text-decoration:none; font-size:13px;
    border-bottom:1px solid #C9D2F5; padding-bottom:1px; white-space:nowrap; }
  .c-link a:hover { border-color:var(--accent); }
  footer { margin-top:36px; font-size:12px; color:var(--ink-3);
    border-top:1px solid var(--line); padding-top:16px; }
  @media (max-width:720px) {
    .look-grid { grid-template-columns:1fr; }
    .in { white-space:normal; }
    h1 { font-size:25px; }
  }
"""


def img_tag(path):
    if not os.path.exists(path):
        raise SystemExit(f"image not found: {path}")
    data = base64.b64encode(open(path, "rb").read()).decode()
    return f"data:image/jpeg;base64,{data}"


def rows(items):
    out = ""
    for it in items:
        label, cls = BADGES.get(it.get("source", "buy"), BADGES["buy"])
        kw = urllib.parse.quote(it["keyword"])
        out += f"""
        <tr>
          <td class="in">{html.escape(it['name'])}<span class="b {cls}">{label}</span></td>
          <td class="is">{html.escape(it.get('note', ''))}</td>
          <td class="c-link"><a href="{TAOBAO}{kw}" target="_blank">搜同款 →</a></td>
        </tr>"""
    return out


def render(cfg, accent):
    a = cfg.get("analysis") or {}
    paras = "".join(f"<p>{html.escape(p)}</p>" for p in a.get("paragraphs", []))
    swatches = "".join(
        f'<span class="sw"><i class="dot" style="background:{c["hex"]}"></i>{html.escape(c["name"])}</span>'
        for c in a.get("palette", [])
    )
    note = f'<p style="margin-top:10px">{html.escape(a["note"])}</p>' if a.get("note") else ""
    analysis = ""
    if a:
        analysis = f"""
<section class="analysis">
  <h2>{html.escape(a.get('heading', '你的个人风格画像'))}</h2>
  {paras}
  <div class="palettes">{swatches}</div>
  {note}
</section>"""

    looks_html = ""
    for i, l in enumerate(cfg["looks"], 1):
        inspo = ""
        if l.get("inspo"):
            inspo = f'<div class="inspo"><span>灵感借鉴</span>{html.escape(l["inspo"])}</div>'
        looks_html += f"""
    <article class="look">
      <div class="look-grid">
        <div class="img-wrap">
          <img src="{img_tag(l['image'])}" alt="{html.escape(l['name'])}">
          <div class="img-badge">Look {i}</div>
        </div>
        <div class="look-body">
          <h3>{html.escape(l['name'])}</h3>
          <div class="look-tag">{html.escape(l.get('tag', ''))}</div>
          {inspo}
          <table class="items">
            <thead><tr><th>单品 / 来源</th><th>版型要求</th><th>购买</th></tr></thead>
            <tbody>{rows(l['items'])}</tbody>
          </table>
        </div>
      </div>
    </article>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(cfg.get('title', '每日穿搭'))}</title>
<style>{CSS.replace('__ACCENT__', accent)}</style>
</head>
<body>
<div class="wrap">
<header>
  <div class="kicker">Daily Lookbook · {html.escape(cfg.get('date', ''))}</div>
  <h1>{html.escape(cfg.get('title', '今日穿搭 lookbook'))}</h1>
  <p class="sub">{html.escape(cfg.get('subtitle', ''))}</p>
</header>
{analysis}
{looks_html}
<footer>{html.escape(cfg.get('footer', ''))}</footer>
</div>
</body>
</html>
"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("config")
    p.add_argument("output")
    p.add_argument("--accent", default="#1F3FBF")
    args = p.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    html_str = render(cfg, args.accent)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html_str)
    print(args.output, os.path.getsize(args.output) // 1024, "KB")


if __name__ == "__main__":
    main()
