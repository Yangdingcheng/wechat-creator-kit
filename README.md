# WeChat Creator Kit

**一条命令，把选题变成公众号待审稿 —— 低成本 AI 写稿 + 固定排版 + 模板封面，不烧生图钱，不烧编程 Agent 额度。**

**One command turns topics into review-ready WeChat articles: one low-cost LLM call per article, fixed layout, local template covers. No image-generation cost. No auto-publishing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Cost](https://img.shields.io/badge/cost-1%20LLM%20call%20%2F%20article-green)

## 为什么做这个？ / Why

很多公众号作者现在用通用 AI Agent 写稿：一跑就是几十次调用、还要 AI 生封面，一天下来额度见底。
这个工具反着来，把成本写死在程序里：

- **每篇只调 1 次模型**，`max_tokens=1800`，不用深度思考模型
- **封面本地生成**（模板叠字），0 生图费用，中文不会画错
- **只喂你给的事实**，不把 10 篇原文全塞进上下文；没给的事实不编
- **只出待审稿**，不自动进草稿箱、不自动发布 —— 最后一步永远是人审

实测场景：一个日更 7-8 篇的国际新闻号，用这套流程替代通用 Agent 写稿。

## 10 秒试用（不用任何 API Key）/ Quick demo — no key needed

```bash
git clone https://github.com/Yangdingcheng/wechat-creator-kit.git
cd wechat-creator-kit
pip install -r requirements.txt
python3 creator_kit.py --topics examples/topics.example.json --out out_demo --force-template
# 打开 out_demo/<日期>/index.html 就是待审稿列表
```

## 正式使用 / Real run

支持任何 OpenAI 兼容接口：DeepSeek、通义千问、Kimi、OpenAI、本地 Ollama 等。

```bash
export LLM_API_KEY="sk-..."          # 你的 key，只放环境变量，不要写进代码、不要发给任何人
export LLM_BASE_URL="https://api.deepseek.com/v1"   # 默认 DeepSeek，可换
export LLM_MODEL="deepseek-chat"                    # 默认，可换
# 把你的选题按 examples/topics.example.json 的格式写进 topics.json
python3 creator_kit.py --topics topics.json --out out
```

输出：每篇一个文件夹，含 `index.html`（微信风格排版预览）、`article.md`、`cover.png`，外加当日 `manifest.json` 和成本提示（token 数 + 估算费用）。

## topics.json 格式

```json
[{
  "title": "文章标题",
  "hook_number": "51.8%",
  "facts": ["只能用这些事实写稿", "事实2"],
  "sources": [{"name": "新华社", "url": "https://..."}],
  "closing": "结尾讨论的一句话（可选）"
}]
```

## 排版（固定，不用每次调）

标题 24px 加粗 · 正文 16px / 行高 1.85 · 小标题 18px 加粗 + 红色左线 · 结尾讨论浅灰卡片 · 来源文末小字

## 和同类工具的区别

|  | 本项目 | 通用 AI Agent 写稿 | 纯排版工具 |
|---|---|---|---|
| 写稿成本 | 1 次调用/篇 | 多轮调用，易失控 | 不写稿 |
| 封面 | 本地模板，0 费用 | AI 生图，按张收费 | 无 |
| 事实控制 | 只用给定事实 | 容易自行发挥 | — |
| 发布 | 只出待审稿，人审后发布 | 有的自动发布，风险高 | 推草稿箱 |

## Roadmap

- [ ] Markdown 文件直接导入成稿
- [ ] 多套封面模板（新闻 / 知识 / 情感）
- [ ] 可选：人审通过后对接草稿箱（保持默认关闭）
- [ ] 小红书图文卡片输出

## Contributing

欢迎提 Issue / PR：新封面模板、模型适配、排版主题都是好方向。请勿提交任何 API Key。

## License

MIT
