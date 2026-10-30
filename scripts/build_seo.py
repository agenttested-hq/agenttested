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
# Per-tool model-key note, shared by llms.txt, leaderboard rows and the Quick answer.
def key_line(t):
    return "Bring your own model key (we used the free Gemini API tier)" if "api free tier" in t["test"]["model"].lower() else "No model key needed (free account or built-in free model)"
# Earlier scores for retested tools ("history" in each test), shown on leaderboard rows and in llms.txt.
def hist_txt(t):
    h = t.get("test", {}).get("history") or []
    return "; ".join(f'{x["score"]} on {x["date"]} ({x["tool_version"]})' for x in sorted(h, key=lambda x: x["date"]))
for t in lb["tools"]:
    score = t.get("score")
    sc = f"{score}/100 (tested {t['test']['date']}, {t['test']['tool_version']}, model {t['test']['model']}). {key_line(t)}. {t['test']['evidence']}" + (f" Earlier scores: {hist_txt(t)}." if hist_txt(t) else "") if score is not None else t.get("status", "Not yet tested")
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
# Retest and failed-attempt log: shown on tests.html and in llms.txt so readers see runs that produced no score.
_att = sorted(lb.get("attempts", []), key=lambda a: a["date"], reverse=True)
if _att:
    lines += ["", "## Retests and attempts with no score (scores only change after a complete, fair run)"]
    lines += [f"- {a['date']}, {a['tool']}: {a['result']}. {a['note']}" for a in _att]
lines += ["", "## Newsletter", "- [Weekly AgentTested brief](https://agenttested.beehiiv.com/subscribe): new tools, leaderboard changes and test results, once a week. Free.", "", "## Official channels", f"- Site: {BASE} (launched 2026-10-15). Newsletter: https://agenttested.beehiiv.com/subscribe. Email: agenttested.hq@gmail.com.", "- AgentTested is not affiliated with agenttested.ai or @agenttested on X.", ""]
(ROOT / "llms.txt").write_text("\n".join(lines))

e = html.escape
LBL = {"task_success": "Task", "output_quality": "Quality", "speed_effort": "Speed", "cost_free_tier": "Cost", "developer_experience": "DX"}
def score_cell(t):
    if t.get("score") is None:
        return f'<span class="mut">{e(t.get("status", "Not yet tested"))}</span>'
    x = t["test"]; b = " · ".join(f"{LBL[k]} {v}" for k, v in x["breakdown"].items())
    return (f'<b class="score">{t["score"]}</b><span class="mut">/100</span><div class="mut sm">{e(b)}</div>'
            f'<div class="sm">{e(key_line(t))}</div>'
            f'<div class="mut sm">Tested {e(x["date"])} · {e(x["tool_version"])} · model: {e(x["model"])}</div>'
            + (f'<div class="mut sm">Retested. Earlier: {e(hist_txt(t))}</div>' if hist_txt(t) else '')
            +
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
# "Quick answer" card on the leaderboard: plain-language picks generated from the data, for readers and AI assistants.
_os = [t for t in _sc if "open source" in t["pricing"].lower()]
# All open-source agents tied for the best open-source score, each with whether it needs your own model key.
_os_top = [t for t in _os if t["score"] == _os[0]["score"]] if _os else []
def _keynote(t):
    return "you bring your own model key" if "api free tier" in t["test"]["model"].lower() else "no model key needed"
_os_txt = " and ".join(f'{t["name"]} ({_keynote(t)})' for t in _os_top)
_os_lbl = "agents" if len(_os_top) > 1 else "agent"
_hi = [t for t in _sc if t["score"] == _sc[0]["score"]]
# "No model key needed" = tested on the tool's own free account or built-in free model (not a bring-your-own API key).
_nokey = [t for t in _sc if "api free tier" not in t["test"]["model"].lower()]
_nokey_txt = ", ".join(f"{e(t['name'])} {t['score']}" for t in _nokey)
quick_html = ('<b>Quick answer</b><ul class="mut">'
    + f'<li>Highest score so far: {" and ".join(e(t["name"]) for t in _hi)}, {_sc[0]["score"]}/100.</li>'
    + (f'<li>Best open-source {_os_lbl} so far: {e(_os_txt)}, {_os[0]["score"]}/100.</li>' if _os else '')
    + (f'<li>No model key needed: {_nokey_txt} ran on a free account or a built-in free model. The others are bring-your-own-key (we used the free Gemini API tier).</li>' if _nokey else '')
    + f'<li>All {len(_sc)} scored agents were tested on free tiers with no card, on the same task and rubric. Scores can\'t be bought.</li></ul>')
att_html = ('<h3>Retests and attempts with no score</h3><p class="mut">We log every run that didn\'t produce a score, so you can see what we tried. A score only changes after a complete, fair run.</p><ul class="mut">'
    + "".join(f'<li><b>{e(a["date"])}, {e(a["tool"])}:</b> {e(a["result"])}. {e(a["note"])}</li>' for a in _att) + '</ul>')
ld = {"@context": "https://schema.org", "@type": "ItemList", "name": lb["title"], "itemListElement": [
    {"@type": "ListItem", "position": i + 1, "item": {"@type": "SoftwareApplication", "name": t["name"], "url": t["url"],
     "applicationCategory": "DeveloperApplication", "description": t["description"],
     **({"review": {"@type": "Review", "author": {"@type": "Organization", "name": "AgentTested"}, "datePublished": t["test"]["date"],
        "reviewRating": {"@type": "Rating", "ratingValue": t["score"], "bestRating": 100, "worstRating": 0}, "reviewBody": t["test"]["evidence"]}} if t.get("score") is not None else {})}} for i, t in enumerate(lb["tools"])]}

_faq = [("What is the best AI coding agent right now?", f'In our tests the highest score so far is {" and ".join(t["name"] for t in _hi)} with {_sc[0]["score"]}/100, out of {len(_sc)} agents tested on the same task and rubric (data updated {upd}).')]
if _os:
    _faq.append(("What is the best open-source AI coding agent?", f'{_os_txt} scored {_os[0]["score"]}/100, the highest open-source {"score" if len(_os_top) > 1 else "agent"} in our tests.'))
if _nokey:
    _faq.append(("Which AI coding agents work without an API key?", "Of the agents we scored, " + ", ".join(f'{t["name"]} ({t["score"]})' for t in _nokey) + " ran on a free account or a built-in free model with no API key. The others need your own model key; we used the free Gemini API tier."))
faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in _faq]}

# Analytics (GoatCounter, cookieless) and Google Search Console verification.
# Values live in data/site_config.json; empty values inject nothing.
_cfg = json.loads((ROOT / "data/site_config.json").read_text()) if (ROOT / "data/site_config.json").exists() else {}
_gc = re.sub(r"[^a-z0-9-]", "", str(_cfg.get("goatcounter_code", "")).strip().lower())
_gsv = re.sub(r"[^A-Za-z0-9_-]", "", str(_cfg.get("google_site_verification", "")).strip())
_isv = re.sub(r"[^A-Za-z0-9-]", "", str(_cfg.get("impact_site_verification", "")).strip())

def add_head_extras(s, home=False):
    s = re.sub(r'<!--analytics-->.*?<!--/analytics-->', '', s, flags=re.S)
    extra = ""
    if home and _gsv:
        extra += f'<meta name="google-site-verification" content="{_gsv}">'
    if home and _isv:
        extra += f"<meta name='impact-site-verification' value='{_isv}'>"
    if _gc:
        extra += f'<script data-goatcounter="https://{_gc}.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
    return s.replace('</head>', f'<!--analytics-->{extra}<!--/analytics--></head>', 1) if extra else s

_nf = ROOT / "404.html"
if _nf.exists():
    _nf.write_text(add_head_extras(_nf.read_text()))

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
        meta += '<script type="application/ld+json">' + json.dumps(faq_ld) + '</script>'
        s = re.sub(r'<p id="lbnote">.*?</p>', f'<p id="lbnote">{e(lb["note"])}</p>', s, flags=re.S)
        s = re.sub(r'<tbody id="lb">.*?</tbody>', f'<tbody id="lb">{rows}</tbody>', s, flags=re.S)
        s = re.sub(r'<div class="card" id="quick">.*?</div>(?=\n<div class="card warn">)', lambda m: f'<div class="card" id="quick">{quick_html}</div>', s, count=1, flags=re.S)
    if p == "tests.html" and _att:
        s = re.sub(r'<div class="card" id="attempts">.*?</div>', lambda m: f'<div class="card" id="attempts">{att_html}</div>', s, count=1, flags=re.S)
    if p == "":  # pre-render New this week so crawlers and AI assistants see it without JavaScript
        s = re.sub(r'<div id="new">.*?</div>(?=\s*<div class="card"><h3>)', lambda m: f'<div id="new">{nw_html}</div>', s, count=1, flags=re.S)
    s = s.replace('</head>', meta + '<!--/seo--></head>', 1)
    s = re.sub(r'<span id="upd">.*?</span>', f'<span id="upd">{upd}</span>', s)
    s = add_head_extras(s, home=(p == ""))
    f.write_text(s)
print("ok")
