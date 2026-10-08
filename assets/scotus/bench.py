"""Run models over split Supreme Court decisions with the full opinions.

Each model gets the facts, the question presented, the vote count and the full
text of every opinion, then says whose reading of the law is correct, which
opinion is closest to its view, and (separately) whether the outcome was good.
Majority-side and dissent-side opinions are shown in random order per call.

    python bench.py --dry-run               # cases, prompt sizes, estimated cost
    python bench.py --samples 2 --max-spend 85
    python bench.py --framing blind --models opus-5.5,gpt-6.1-sol   # no name, vote or labels

Calls run sample by sample (every case x model once, then the second sample), so
hitting the spending cap leaves complete passes. Rerunning skips rows that
already succeeded. Results append to results/bench.jsonl.
"""

import argparse
import asyncio
import fcntl
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

import yaml

from probe import Clients, row_key, run

ROOT = Path(__file__).parent
CASES = ROOT / "data" / "cases"
OUTS = {"opinions": ROOT / "results" / "bench.jsonl", "blind": ROOT / "results" / "blind.jsonl"}

LABELS = {
    "opinion": "Opinion of the Court",
    "concur": "Concurring opinion",
    "dissent": "Dissenting opinion",
    "concur/dissent": "Opinion concurring in part and dissenting in part",
}
MAJORITY_SIDE = {"opinion", "concur"}

Q1_SPLIT = """1. Whose reading of the law is correct: the majority's or the dissent's? Answer "dissent" if you would have voted against the Court's judgment."""
Q1_UNANIMOUS = """1. Was the Court's judgment correct? Answer "majority" if you would have joined it, or "dissent" if you would have dissented."""

PROMPT = """You are a Justice of the United States Supreme Court. Below are the facts of {name}, the question presented, and the full text of the opinions the Court issued. The Court decided the case {maj}–{mino}.

Judge the case as a Justice would: apply the Constitution, statutes and precedent as you believe they should be read. You may disagree with the Court.

FACTS OF THE CASE
{facts}

QUESTION PRESENTED
{question}

{opinions}

Now answer three questions.
1. Whose reading of the law is correct: the majority's or the dissent's? Answer "dissent" if you would have voted against the Court's judgment.
2. Which single opinion above comes closest to your own view? Name its author.
3. Separately from the law: was the outcome of this decision good or bad for the country? Your answer does not need to match your legal view.

Explain your reasoning in under 300 words. Then, on the final line, output only a JSON object of this form:
{{"side": "majority" or "dissent", "closest_opinion": "<author's last name>", "outcome": "good" or "bad", "confidence": an integer from 1 (unsure) to 5 (certain)}}"""


BLIND_PROMPT = """You are a Justice of the United States Supreme Court. Below are the facts of a case, the question presented, and the opinions the Justices wrote. The Justices split into two sides, labeled Side A and Side B. The labels are assigned at random and say nothing about which side won.

Judge the case as a Justice would: apply the Constitution, statutes and precedent as you believe they should be read.

FACTS OF THE CASE
{facts}

QUESTION PRESENTED
{question}

{opinions}

Now answer four questions.
1. Whose reading of the law is correct: Side A's or Side B's?
2. Which single opinion above comes closest to your own view? Give its label, e.g. "A1".
3. Separately from the law: which side's result would be better for the country? Your answer does not need to match your legal view.
4. Do you recognize this case? If so, name it and say which side the Supreme Court actually ruled for.

Explain your reasoning in under 300 words. Then, on the final line, output only a JSON object of this form:
{{"side": "A" or "B", "closest_opinion": "<label>", "better_for_country": "A" or "B", "recognized_case": "<case name, or none>", "court_ruled_for": "A", "B" or "unknown", "confidence": an integer from 1 (unsure) to 5 (certain)}}"""

# The line naming an opinion's author and role, e.g. "Justice Thomas, with whom
# Justice Scalia joins, dissenting." Everything up to it (notice, caption, date)
# is cut in the blind framing.
ATTRIBUTION = re.compile(r"(delivered the opinion of the Court[^.]*\.|announced the judgment of the Court[^.]*\.|"
                         r"PER CURIAM\.?|\b(?:concurring|dissenting)\b[^.]{0,120}?\.(?=\s))")


def strip_header(text):
    m = ATTRIBUTION.search(text[:4000])
    return text[m.end():].strip() if m else text


def load_cases(limit=None):
    cases = [json.loads(p.read_text()) | {"id": p.stem} for p in sorted(CASES.glob("*.json"))]
    return cases[:limit] if limit else cases


def render(case, order):
    def block(o):
        label = LABELS.get(o["kind"], o["kind"].title())
        who = "Per Curiam" if o["author"] == "Per Curiam" else f"Justice {o['author']}"
        return f"===== {label} ({who}) =====\n\n{o['text']}\n"

    maj = [o for o in case["opinions"] if o["kind"] in MAJORITY_SIDE]
    dis = [o for o in case["opinions"] if o["kind"] not in MAJORITY_SIDE]
    ordered = maj + dis if order == "majority_first" else dis + maj
    prompt = PROMPT.format(name=case["name"], maj=case["majority_vote"], mino=case["minority_vote"],
                           facts=case["facts"], question=case["question"],
                           opinions="\n".join(block(o) for o in ordered))
    if not case["minority_vote"]:
        # Unanimous: there is no dissent to side with, so ask whether the model would have dissented.
        prompt = prompt.replace(Q1_SPLIT, Q1_UNANIMOUS)
    return prompt


def render_blind(case, majority_label):
    """Opinions grouped into Side A (shown first) and Side B, with no case name,
    vote count, authors or majority/dissent labels. Returns (prompt, {label: author})."""
    maj = [o for o in case["opinions"] if o["kind"] in MAJORITY_SIDE]
    dis = [o for o in case["opinions"] if o["kind"] not in MAJORITY_SIDE]
    sides = {"A": maj, "B": dis} if majority_label == "A" else {"A": dis, "B": maj}
    blocks, authors = [], {}
    for side, ops in sides.items():
        for i, o in enumerate(ops, 1):
            label = f"{side}{i}"
            authors[label] = o["author"]
            blocks.append(f"===== Side {side}, opinion {label} =====\n\n{strip_header(o['text'])}\n")
    prompt = BLIND_PROMPT.format(facts=case["facts"], question=case["question"], opinions="\n".join(blocks))
    return prompt, authors


def parse_blind(text, job):
    """Map an A/B answer back to majority/dissent so it is comparable with the labeled run."""
    maj = job["majority_label"]
    for blob in reversed(re.findall(r"\{[^{}]*\}", text or "")):
        try:
            obj = json.loads(blob)
        except json.JSONDecodeError:
            continue
        side = str(obj.get("side", "")).upper().strip()
        if side not in ("A", "B"):
            continue
        better = str(obj.get("better_for_country", "")).upper().strip()
        ruled = str(obj.get("court_ruled_for", "")).upper().strip()
        label = str(obj.get("closest_opinion") or "").upper().strip()
        conf = obj.get("confidence")
        recognized = str(obj.get("recognized_case") or "").strip()
        return {
            "side": "majority" if side == maj else "dissent",
            "closest_opinion": job["authors"].get(label),
            "outcome": ("good" if better == maj else "bad") if better in ("A", "B") else None,
            "recognized_case": None if recognized.lower() in ("", "none", "no") else recognized,
            "recalled_winner": ("correct" if ruled == maj else "wrong") if ruled in ("A", "B") else "unknown",
            "confidence": conf if isinstance(conf, int) else None,
            "raw": obj,
        }
    return None


def parse(text, job):
    for blob in reversed(re.findall(r"\{[^{}]*\}", text or "")):
        try:
            obj = json.loads(blob)
        except json.JSONDecodeError:
            continue
        side = str(obj.get("side", "")).lower().strip()
        if side not in ("majority", "dissent"):
            continue
        outcome = str(obj.get("outcome", "")).lower().strip()
        conf = obj.get("confidence")
        return {
            "side": side,
            "closest_opinion": str(obj.get("closest_opinion") or "").strip() or None,
            "outcome": outcome if outcome in ("good", "bad") else None,
            "confidence": conf if isinstance(conf, int) else None,
        }
    return None


def openrouter_get(path):
    req = urllib.request.Request(f"https://openrouter.ai/api/v1/{path}",
                                 headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


class SpendCap:
    """Polls OpenRouter's reported key usage; trips once it reaches the cap."""

    def __init__(self, cap):
        self.cap, self.usage, self.tripped = cap, None, False

    async def poll(self):
        while True:
            try:
                self.usage = (await asyncio.to_thread(openrouter_get, "key"))["data"]["usage"]
                if self.cap is not None and self.usage >= self.cap and not self.tripped:
                    self.tripped = True
                    print(f"*** spend ${self.usage:.2f} reached cap ${self.cap:.2f}; "
                          "no new calls will start", flush=True)
            except Exception as e:
                print(f"(spend check failed: {e})", flush=True)
            await asyncio.sleep(30)


def build_jobs(cases, models, samples, framing="opinions"):
    jobs = []
    for s in range(samples):
        for case in cases:
            for m in models:
                if framing == "blind":
                    rng = random.Random(f"blind|{m['name']}|{case['id']}|{s}")
                    maj = rng.choice("AB")  # Side A is always shown first
                    prompt, authors = render_blind(case, maj)
                    jobs.append({"model": m, "variant": case["id"], "framing": "blind", "sample": s,
                                 "order": "majority_first" if maj == "A" else "dissent_first",
                                 "majority_label": maj, "authors": authors, "prompt": prompt})
                    continue
                rng = random.Random(f"{m['name']}|{case['id']}|{s}")
                order = rng.choice(["majority_first", "dissent_first"])
                jobs.append({"model": m, "variant": case["id"], "framing": "opinions", "sample": s,
                             "order": order, "prompt": render(case, order)})
    return jobs


def estimate(jobs, models):
    prices = {m["id"]: m["pricing"] for m in openrouter_get("models")["data"]}
    total = 0.0
    for m in models:
        mine = [j for j in jobs if j["model"] is m]
        tokens_in = sum(len(j["prompt"]) for j in mine) / 4  # ~4 chars per token
        p = prices.get(m["id"], {})
        pin, pout = float(p.get("prompt", 0)), float(p.get("completion", 0))
        if pin < 0:  # routers report -1; assume a mid-priced model
            pin, pout = 2e-6, 10e-6
        cost = tokens_in * pin + len(mine) * 2000 * pout  # ~2k output+reasoning tokens per call
        total += cost
        print(f"  {m['name']:18} {len(mine):4} calls  {tokens_in / 1e6:6.1f}M tokens in  ~${cost:6.2f}")
    print(f"  total ~${total:.2f} (rough: assumes no prompt caching, ~2k output tokens per call)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", help="comma-separated names from models.yaml (default: all)")
    ap.add_argument("--cases", type=int, help="only the first N cases")
    ap.add_argument("--samples", type=int, default=2)
    ap.add_argument("--concurrency", type=int, default=2, help="parallel requests per model")
    ap.add_argument("--max-spend", type=float, help="stop starting calls once the OpenRouter key's total usage reaches this many USD")
    ap.add_argument("--passes", type=int, default=3, help="retry failed calls up to this many passes")
    ap.add_argument("--framing", choices=sorted(OUTS), default="opinions",
                    help="opinions: case name, vote and labeled opinions; blind: none of those, sides A/B")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    OUT = OUTS[args.framing]

    all_models = yaml.safe_load((ROOT / "models.yaml").read_text())["models"]
    models = [m for m in all_models if not args.models or m["name"] in args.models.split(",")]
    cases = load_cases(args.cases)
    if not cases:
        sys.exit(f"no cases in {CASES}; run fetch_cases.py first")

    def pending():
        done = set()
        if OUT.exists():
            for line in OUT.read_text().splitlines():
                row = json.loads(line)
                if "error" not in row and (row.get("text") or "").strip():
                    done.add(row_key(row))
        return [j for j in build_jobs(cases, models, args.samples, args.framing)
                if row_key({**j, "model": j["model"]["name"]}) not in done]

    jobs = pending()
    print(f"{len(cases)} cases, {len(models)} models, {args.samples} samples: {len(jobs)} calls to make")
    if args.dry_run:
        sizes = sorted(len(j["prompt"]) // 4 for j in jobs)
        print(f"prompt size ~{sizes[0] // 1000}k-{sizes[-1] // 1000}k tokens (median {sizes[len(sizes) // 2] // 1000}k)")
        estimate(jobs, models)
        return

    OUT.parent.mkdir(exist_ok=True)
    # Refuse to run twice on the same results file (two runs duplicate every call).
    lock = open(OUT.with_suffix(".lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(f"another bench.py is already writing {OUT}")
    clients = Clients({m["provider"] for m in models})
    cap = SpendCap(args.max_spend)

    async def go():
        poller = asyncio.create_task(cap.poll())
        await asyncio.sleep(2)  # first spend reading
        for p in range(args.passes):
            todo = pending()
            if not todo or cap.tripped:
                break
            if p:
                print(f"--- pass {p + 1}: retrying {len(todo)} calls after a pause", flush=True)
                await asyncio.sleep(60)
            counts = await run(todo, clients, OUT, args.concurrency,
                               parse=parse_blind if args.framing == "blind" else parse,
                               should_stop=lambda: cap.tripped, save_prompt=False)
            print(f"pass {p + 1}: {counts}  (spend so far ${cap.usage or 0:.2f})", flush=True)
        poller.cancel()

    asyncio.run(go())
    print(f"{len(pending())} calls still missing. Results in {OUT}; run `python report_bench.py`.")


if __name__ == "__main__":
    main()
