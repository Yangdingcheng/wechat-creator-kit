#!/usr/bin/env python3
"""
WeChat Creator Kit — one-command, low-cost AI pipeline for WeChat Official Account creators.

topics.json -> draft (any OpenAI-compatible model, ONE call per article)
            -> fixed WeChat-ready layout (HTML + Markdown)
            -> template cover (local, no image-generation cost)
            -> review-only output (never auto-publishes, never touches the draft box)

No API key? It runs in template/demo mode so anyone can try it in 10 seconds.

Usage:
  pip install -r requirements.txt
  python3 creator_kit.py --topics examples/topics.example.json --out out_demo --force-template
  # real run: set LLM_API_KEY (DeepSeek / Qwen / Kimi / OpenAI / Ollama-compatible endpoint)
  LLM_API_KEY=sk-... python3 creator_kit.py --topics topics.json --out out
"""
import argparse, hashlib, html, json, os, re, sys, urllib.request
from datetime import date

BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")
# Rough public list price for deepseek-chat output, for the cost hint only (USD / 1M tokens).
PRICE_PER_M_TOKENS = float(os.environ.get("LLM_PRICE_PER_M", "0.28"))

def load_json(p):
    with open(p, encoding="utf-8") as f: return json.load(f)

def slug(i, title):
    return f"{i+1:02d}-" + hashlib.md5(title.encode()).hexdigest()[:6]

def call_llm(topic, cfg):
    key = os.environ.get("LLM_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    if not key: return None, "no_key"
    facts = "\n".join(f"- {x}" for x in topic.get("facts", []))
    sources = "\n".join(f"- {s.get('name','')} {s.get('url','')}" for s in topic.get("sources", []))
    style = cfg.get("style", "讲清楚发生了什么、为什么重要，简洁，不编造。")
    system = (f"你是微信公众号作者。风格：{style} "
              "要求：1000-1500字；只用给定事实，不编造数字/人名/时间；争议说法写成“据报道/据称”；"
              "正文用 ## 导语、## 发生了什么、## 为什么重要、## 还不清楚、## 结尾讨论 分节。")
    user = f"标题：{topic['title']}\n钩子数字：{topic.get('hook_number','')}\n事实（只能用这些）：\n{facts}\n来源：\n{sources}"
    body = {"model": MODEL, "messages":[{"role":"system","content":system},{"role":"user","content":user}],
            "temperature":0.7, "max_tokens":1800}
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: data=json.load(r)
        usage = data.get("usage", {}).get("total_tokens", 0)
        cost = usage/1_000_000*PRICE_PER_M_TOKENS if usage else 0
        return data["choices"][0]["message"]["content"], f"{MODEL} · tokens={usage} · est.${cost:.4f}"
    except Exception as e:
        print(f"  [warn] LLM failed: {e} -> template draft", file=sys.stderr); return None, f"failed:{e}"

def template_draft(topic):
    facts = topic.get("facts") or ["（暂无事实素材，请先补事实再成稿）"]
    return "\n\n".join([
        "## 导语\n"+topic["title"],
        "## 发生了什么\n"+"\n".join(facts),
        "## 为什么重要\n这件事的后续值得继续看，涉及的数字和各方表态还在变化中。",
        "## 还不清楚\n素材里还没有最终结论的部分，先不要下结论。",
        "## 结尾讨论\n"+(topic.get("closing") or "你怎么看这件事的下一步？欢迎留言。")])

def parse_sections(text):
    sections, cur_title, cur = [], None, []
    for line in text.splitlines():
        m = re.match(r"^##\s*(.+?)\s*$", line.strip())
        if m:
            if cur_title is not None: sections.append((cur_title, cur))
            cur_title, cur = m.group(1), []
        elif line.strip(): cur.append(line.strip())
    if cur_title is not None: sections.append((cur_title, cur))
    elif text.strip(): sections.append(("正文",[text.strip()]))
    return sections

def to_html(topic, sections, model_used):
    esc = html.escape
    p = [f'<h1 style="font-size:24px;font-weight:bold;line-height:1.4;">{esc(topic["title"])}</h1>',
         f'<p style="font-size:14px;color:#888;">{esc(model_used)} · review only</p>']
    for title, paras in sections:
        if title=="结尾讨论":
            inner="".join(f'<p style="font-size:16px;line-height:1.85;margin:8px 0;">{esc(x)}</p>' for x in paras)
            p.append(f'<div style="background:#f5f5f5;padding:16px;border-radius:8px;">{inner}</div>')
        elif title in ("导语","正文"):
            p += [f'<p style="font-size:16px;line-height:1.85;">{esc(x)}</p>' for x in paras]
        else:
            p.append(f'<h2 style="font-size:18px;font-weight:bold;border-left:4px solid #d00;padding-left:10px;">{esc(title)}</h2>')
            p += [f'<p style="font-size:16px;line-height:1.85;">{esc(x)}</p>' for x in paras]
    src="".join(f'<p style="margin:2px 0;">{esc(s.get("name",""))}：{esc(s.get("url",""))}</p>' for s in topic.get("sources",[]))
    p.append(f'<div style="font-size:12px;color:#888;margin-top:24px;">来源：<br>{src or "（待补）"}</div>')
    return ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"></head>'
            '<body style="font-family:-apple-system,Microsoft YaHei,sans-serif;color:#222;max-width:720px;margin:0 auto;padding:16px;">'
            +"".join(p)+"</body></html>")

def make_cover(topic, out_path, font_path=""):
    try: from PIL import Image, ImageDraw, ImageFont
    except ImportError: print("  [skip cover] pip install pillow", file=sys.stderr); return False
    W,H=900,500; img=Image.new("RGB",(W,H),(17,17,17)); d=ImageDraw.Draw(img)
    d.rectangle([0,H-8,W,H], fill=(208,0,0))
    cands=[font_path] if font_path else []
    cands+=["C:\\Windows\\Fonts\\msyh.ttc","/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc","/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    big=small=None
    for path in cands:
        if path and os.path.exists(path):
            try: big=ImageFont.truetype(path,64); small=ImageFont.truetype(path,30); break
            except Exception: continue
    if big is None: big=small=ImageFont.load_default()
    lines,cur=[],""
    for ch in topic["title"]:
        if len(cur)>=11: lines.append(cur); cur=""
        cur+=ch
    if cur: lines.append(cur)
    y=90
    for line in lines[:3]: d.text((60,y),line,fill=(255,255,255),font=big); y+=90
    if topic.get("hook_number"): d.text((60,y+20),topic["hook_number"],fill=(255,200,0),font=small)
    img.save(out_path); return True

def main():
    ap=argparse.ArgumentParser(description="WeChat Creator Kit")
    ap.add_argument("--topics", required=True); ap.add_argument("--out", default="out")
    ap.add_argument("--max", type=int, default=8); ap.add_argument("--force-template", action="store_true")
    ap.add_argument("--force", action="store_true"); a=ap.parse_args()
    cfg={}
    if os.path.exists("config.json"): cfg=load_json("config.json")
    topics=load_json(a.topics); topics=topics.get("topics",[]) if isinstance(topics,dict) else topics
    today=date.today().isoformat(); root=os.path.join(a.out,today); os.makedirs(root,exist_ok=True)
    seen_path=os.path.join(a.out,".seen.json"); seen=load_json(seen_path) if os.path.exists(seen_path) else {}
    manifest=[]
    for i,topic in enumerate(topics[:a.max]):
        key=slug(i,topic["title"])
        if key in seen and not a.force: print(f"skip: {topic['title']}"); continue
        print(f"[{i+1}] {topic['title']}")
        if a.force_template: text,used=template_draft(topic),"template (demo, no API cost)"
        else:
            text,used=call_llm(topic,cfg)
            if text is None: text,used=template_draft(topic),"template (LLM unavailable, labelled)"
        d=os.path.join(root,key); os.makedirs(d,exist_ok=True)
        open(os.path.join(d,"index.html"),"w",encoding="utf-8").write(to_html(topic,parse_sections(text),used))
        open(os.path.join(d,"article.md"),"w",encoding="utf-8").write(f"# {topic['title']}\n\n{text}\n")
        ok=make_cover(topic,os.path.join(d,"cover.png"),cfg.get("cover_font_path",""))
        manifest.append({"title":topic["title"],"dir":key,"model":used,"cover":ok,"status":"review-only"})
        seen[key]=topic["title"]
    json.dump(seen,open(seen_path,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    json.dump(manifest,open(os.path.join(root,"manifest.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    idx="<h1>今日待审 / Review queue</h1>"+"".join(f'<p><a href="{m["dir"]}/index.html">{html.escape(m["title"])}</a> ({html.escape(m["model"])})</p>' for m in manifest)
    open(os.path.join(root,"index.html"),"w",encoding="utf-8").write(idx)
    print(f"\nDone: {len(manifest)} article(s) in {root} — review before publishing.")

if __name__=="__main__": main()
