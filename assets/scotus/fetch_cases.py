"""Build a set of split Supreme Court decisions with full opinion text.

Votes, facts and question presented come from the Oyez API; opinion text comes
from Cornell LII (one page per case, fetched at LII's requested crawl delay).

    python fetch_cases.py --n 40                  # random split decisions, terms 2005-2025
    python fetch_cases.py --n 200 --unanimous 50  # plus unanimous ones, as a baseline
    python fetch_cases.py --n 40 --seed 2 --first-term 1995

Each case is written to data/cases/<term>_<docket>.json. Cases already on disk
are kept, so rerunning with a larger --n only fetches the extra ones.
"""

import argparse
import html
import json
import random
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "data" / "cases"
CACHE = ROOT / "data" / "cache"
UA = "scotus-probe research script (+https://ryancompton.net)"
LII_DELAY = 10  # seconds; LII robots.txt Crawl-delay
OYEZ_DELAY = 1
# Skip cases whose opinions would make a very long (expensive) prompt.
MAX_OPINION_CHARS = 250_000

_last = {}


def get(url, host_delay):
    """GET with an on-disk cache and a per-host delay."""
    key = re.sub(r"[^A-Za-z0-9]+", "_", url)[-180:]
    cached = CACHE / key
    if cached.exists():
        return cached.read_text()
    host = url.split("/")[2]
    wait = _last.get(host, 0) + host_delay - time.time()
    if wait > 0:
        time.sleep(wait)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8", "replace")
    _last[host] = time.time()
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(body)
    return body


def strip_html(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s or "", flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>", "\n", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n\n", s).strip()


def lii_opinions(docket):
    """Split the LII case page into its opinions: [{kind, author, text}]."""
    page = get(f"https://www.law.cornell.edu/supremecourt/text/{docket}", LII_DELAY)
    anchors = [(m.start(), m.group(1)) for m in
               re.finditer(r'id="writing-[^"_]+_([A-Z/]+)(?:_\d+)?"', page)]
    if not anchors:
        return []
    # The case text ends where the site's sidebar/footer begins.
    end = len(page)
    for marker in ("Supreme Court Toolbox", 'id="footer"', "<footer"):
        i = page.find(marker, anchors[-1][0])
        if i != -1:
            end = min(end, page.rfind("<", 0, i))
    out = []
    for (start, kind), (stop, _) in zip(anchors, anchors[1:] + [(end, None)]):
        if kind == "SYLLABUS":
            continue
        # Each anchor's id sits inside an opening tag: start after that tag,
        # and stop before the next one opens.
        start = page.find(">", start) + 1
        if stop != end:
            stop = page.rfind("<", 0, stop)
        text = strip_html(page[start:stop])
        text = re.sub(r"^\s*(TOP\s+)?(Opinion|Concurrence|Dissent|Concur/Dissent)\s*", "", text, flags=re.I)
        # First "Justice X" in the text is the author; per curiam opinions have none.
        m = re.search(r"(Chief Justice|Justice)\s+([A-Z][A-Za-z'’-]+)", text[:3000])
        out.append({"kind": kind.lower(), "author": m.group(2) if m else "Per Curiam", "text": text})
    return out


def oyez_case(href):
    d = json.loads(get(href, OYEZ_DELAY))
    decs = d.get("decisions") or []
    if len(decs) != 1:
        return None, "not exactly one decision"
    dec = decs[0]
    maj, mino = dec.get("majority_vote") or 0, dec.get("minority_vote") or 0
    votes = {v["member"]["last_name"]: v.get("vote") for v in dec.get("votes") or []
             if v.get("member") and v.get("vote") in ("majority", "minority")}
    if len(votes) < 7:
        return None, "missing per-justice votes"
    facts, question = strip_html(d.get("facts_of_the_case")), strip_html(d.get("question"))
    if not facts or not question:
        return None, "missing facts or question"
    return {
        "name": d["name"], "term": d["term"], "docket": d["docket_number"],
        "citation": d.get("citation"), "facts": facts, "question": question,
        "majority_vote": maj, "minority_vote": mino, "votes": votes,
        "winning_party": dec.get("winning_party"), "oyez_url": href,
    }, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="how many split decisions to have on disk")
    ap.add_argument("--unanimous", type=int, default=0, help="how many unanimous decisions to have on disk")
    ap.add_argument("--first-term", type=int, default=2005)
    ap.add_argument("--last-term", type=int, default=2025)
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    on_disk = [json.loads(p.read_text()) for p in OUT.glob("*.json")]
    have = {"split": sum(c["minority_vote"] > 0 for c in on_disk)}
    have["unanimous"] = len(on_disk) - have["split"]
    want = {"split": args.n, "unanimous": args.unanimous}
    candidates = []
    for term in range(args.first_term, args.last_term + 1):
        listing = json.loads(get(f"https://api.oyez.org/cases?per_page=0&filter=term:{term}", OYEZ_DELAY))
        candidates += [c["href"] for c in listing if c.get("href")]
    random.Random(args.seed).shuffle(candidates)
    print(f"{len(candidates)} cases in terms {args.first_term}-{args.last_term}; {have} already on disk")

    skipped = {}
    for href in candidates:
        if all(have[k] >= want[k] for k in want):
            break
        term, docket = href.rstrip("/").split("/")[-2:]
        path = OUT / f"{term}_{docket}.json"
        if path.exists():
            continue
        case, why = oyez_case(href)
        if case is None:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        kind = "split" if case["minority_vote"] else "unanimous"
        if have[kind] >= want[kind]:
            skipped[f"enough {kind}"] = skipped.get(f"enough {kind}", 0) + 1
            continue
        try:
            ops = lii_opinions(case["docket"])
        except Exception as e:
            skipped[f"LII fetch failed ({type(e).__name__})"] = skipped.get(f"LII fetch failed ({type(e).__name__})", 0) + 1
            continue
        has_dissent = any("dissent" in o["kind"] for o in ops)
        if kind == "split" and not has_dissent:
            skipped["no dissent text on LII"] = skipped.get("no dissent text on LII", 0) + 1
            continue
        if kind == "unanimous" and (has_dissent or not any(o["kind"] == "opinion" for o in ops)):
            skipped["unanimous but LII text doesn't match"] = skipped.get("unanimous but LII text doesn't match", 0) + 1
            continue
        size = sum(len(o["text"]) for o in ops)
        if size > MAX_OPINION_CHARS:
            skipped["opinions too long"] = skipped.get("opinions too long", 0) + 1
            continue
        case["opinions"] = ops
        path.write_text(json.dumps(case, indent=1))
        have[kind] += 1
        print(f"[{kind} {have[kind]}/{want[kind]}] {case['term']} {case['name']} "
              f"({case['majority_vote']}-{case['minority_vote']}, {len(ops)} opinions, {size // 1000}k chars)", flush=True)
    print("skipped:", skipped)


if __name__ == "__main__":
    main()
