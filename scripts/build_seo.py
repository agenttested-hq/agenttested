#!/usr/bin/env python3
"""Regenerate SEO/LLM-visibility files from data/tools.json.
Run after editing data: python3 scripts/build_seo.py"""
import json, html, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://agenttested-hq.github.io/agenttested/"
d = json.loads((ROOT / "data/tools.json").read_text())
upd = d["updated"]
lb = d["leaderboards"][0]
pages = {"": "AgentTested: AI tools, actually tested", "leaderboard.html": "Best AI coding agents", "tests.html": "Round 1 test write-up", "about.html": "Methodology"}
DESC = "AI tools ranked by agents that actually test them, for builders, vibe coders and game devs."
_sc = [t for t in lb["tools"] if t.get("score") is not None]
_top = ", ".join(f'{t["name"]} {t["score"]}' for t in _sc[:4])
PDESC = {  # per-page meta descriptions, regenerated from data so scores stay current
    "": f"AI tools ranked by agents that actually test them, for builders, vibe coders and game devs. {len(_sc)} AI coding agents scored so far: {_top} and more.",
    "leaderboard.html": f"{len(_sc)} AI coding agents tested on the same task, all on free tiers: {_top} and more. Scores, pricing and free tiers, updated {upd}.",
    "tests.html": f"How we tested {len(_sc)} AI coding agents: one standard prompt, 10 automated browser checks and a 100-point rubric, with per-tool deductions.",
    "about.html": "How AgentTested scores AI tools: a 100-point rubric (task success, quality, speed, cost, developer experience). Rankings can't be bought.",
}

(ROOT / "robots.txt").write_text(
    "# All crawlers, including AI assistants (GPTBot, ClaudeBot, PerplexityBot, Google-Extended), are welcome.\n"
    "User-agent: *\nAllow: /\n\nSitemap: " + BASE + "sitemap.xml\n")

(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <url><loc>{BASE}{p}</loc><lastmod>{upd}</lastmod></url>\n" for p in pages)
    + "</urlset>\n")

lines = [f"# AgentTested", "", f"> {DESC} Rankings can't be bought; sponsored placements are labeled and kept separate.", "",
         f"Data last updated {upd}. Machine-readable data: {BASE}data/tools.json", "",
         "## Pages", f"- [Best AI coding agents]({BASE}leaderboard.html): {lb['status']}", f"- [Round 1 test write-up]({BASE}tests.html): standard task, checks and per-tool results", f"- [Methodology]({BASE}about.html): 100-point scoring rubric and no-pay-to-rank policy", "",
         f"## {lb['title']} ({lb['status']})", lb["note"], ""]
for t in lb["tools"]:
    score = t.get("score")
    sc = f"{score}/100 (tested {t['test']['date']}, {t['test']['tool_version']}, model {t['test']['model']}). {t['test']['evidence']}" if score is not None else t.get("status", "Not yet tested")
    lines.append(f"- [{t['name']}]({t['url']}): {t['description']} Free tier: {t['free_tier']}. Pricing: {t['pricing']}. Test score: {sc}")
# "New this week" = finds from the 7 days up to the data date (updated and the 6 days before it).
# Older finds stay in data/tools.json as an archive but are no longer shown or listed.
import datetime as _dt
NW_DAYS = 7
_nw_cut = (_dt.date.fromisoformat(upd) - _dt.timedelta(days=NW_DAYS - 1)).isoformat()
_nw = sorted((t for t in d.get("new_this_week", []) if str(t.get("found", "")) >= _nw_cut), key=lambda t: str(t.get("found", "")), reverse=True)
if _nw:
    lines += ["", f"## New this week (found by our discovery agents {_nw_cut} to {upd}; listed, not yet tested or scored)"]
    lines += [f"- [{t['name']}]({t['url']}): {t['description']} Found {t.get('found', 'n/a')}." for t in _nw]
lines += ["", "## Newsletter", "- [Weekly AgentTested brief](https://agenttested.beehiiv.com/subscribe): new tools, leaderboard changes and test results, once a week. Free.", "", "## Official channels", f"- Site: {BASE} (launched 2026-10-15). Newsletter: https://agenttested.beehiiv.com/subscribe. Email: agenttested.hq@gmail.com.", "- AgentTested is not affiliated with agenttested.ai or @agenttested on X.", ""]
(ROOT / "llms.txt").write_text("\n".join(lines))

e = html.escape
LBL = {"task_success": "Task", "output_quality": "Quality", "speed_effort": "Speed", "cost_free_tier": "Cost", "developer_experience": "DX"}
def score_cell(t):
    if t.get("score") is None:
        return f'<span class="mut">{e(t.get("status", "Not yet tested"))}</span>'
    x = t["test"]; b = " · ".join(f"{LBL[k]} {v}" for k, v in x["breakdown"].items())
    return (f'<b class="score">{t["score"]}</b><span class="mut">/100</span><div class="mut sm">{e(b)}</div>'
            f'<div class="mut sm">Tested {e(x["date"])} · {e(x["tool_version"])} · model: {e(x["model"])}</div>'
            f'<div class="mut sm">{e(x["evidence"])} <a href="tests.html">Details</a></div>')
def ref_cell(t):
    if not t.get("referral_url"):
        return ""
    return (f'<div class="sm"><a href="{e(t["referral_url"])}" rel="sponsored noopener" target="_blank">Try {e(t["name"])} (referral)</a></div>'
            f'<div class="mut sm">{e(t.get("referral_note", "Referral link: we may earn a commission; it never affects scores or rankings."))}</div>')
rows = "".join(
    f'<tr><td><a href="{e(t["url"])}" rel="noopener" target="_blank"><b>{e(t["name"])}</b></a><div class="mut">{e(t["description"])}</div>{ref_cell(t)}</td>'
    f'<td class="{"yes" if t["free_tier"]=="Yes" else "no"}">{e(t["free_tier"])}</td><td class="hide-sm mut">{e(t["pricing"])}</td>'
    f'<td>{score_cell(t)}</td></tr>' for t in lb["tools"])
def nw_card(t):
    found = f'<div class="mut sm">Found {e(t["found"])}</div>' if t.get("found") else ""
    return f'<div class="card"><a href="{e(t["url"])}" rel="noopener" target="_blank"><b>{e(t["name"])}</b></a><div class="mut">{e(t["description"])}</div>{found}</div>'
nw_html = "".join(nw_card(t) for t in _nw)
ld = {"@context": "https://schema.org", "@type": "ItemList", "name": lb["title"], "itemListElement": [
    {"@type": "ListItem", "position": i + 1, "item": {"@type": "SoftwareApplication", "name": t["name"], "url": t["url"],
     "applicationCategory": "DeveloperApplication", "description": t["description"],
     **({"review": {"@type": "Review", "author": {"@type": "Organization", "name": "AgentTested"}, "datePublished": t["test"]["date"],
        "reviewRating": {"@type": "Rating", "ratingValue": t["score"], "bestRating": 100, "worstRating": 0}, "reviewBody": t["test"]["evidence"]}} if t.get("score") is not None else {})}} for i, t in enumerate(lb["tools"])]}

for p, title in pages.items():
    f = ROOT / (p or "index.html")
    s = f.read_text()
    s = re.sub(r'<!--seo-->.*?<!--/seo-->', '', s, flags=re.S)
    pd = PDESC.get(p, DESC)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(pd)}">', s, count=1)
    meta = (f'<!--seo--><link rel="canonical" href="{BASE}{p}"><meta property="og:type" content="website">'
            f'<meta property="og:site_name" content="AgentTested"><meta property="og:title" content="{e(title)}">'
            f'<meta property="og:description" content="{e(pd)}"><meta property="og:url" content="{BASE}{p}">'
            f'<meta name="twitter:card" content="summary">')
    if p == "leaderboard.html":
        meta += '<script type="application/ld+json">' + json.dumps(ld) + '</script>'
        s = re.sub(r'<p id="lbnote">.*?</p>', f'<p id="lbnote">{e(lb["note"])}</p>', s, flags=re.S)
        s = re.sub(r'<tbody id="lb">.*?</tbody>', f'<tbody id="lb">{rows}</tbody>', s, flags=re.S)
    if p == "":  # pre-render New this week so crawlers and AI assistants see it without JavaScript
        s = re.sub(r'<div id="new">.*?</div>(?=\s*<div class="card"><h3>)', lambda m: f'<div id="new">{nw_html}</div>', s, count=1, flags=re.S)
    s = s.replace('</head>', meta + '<!--/seo--></head>', 1)
    s = re.sub(r'<span id="upd">.*?</span>', f'<span id="upd">{upd}</span>', s)
    f.write_text(s)
print("ok")
