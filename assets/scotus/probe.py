"""Ask models how they would rule on a Supreme Court case, under several framings.

For each model x variant x framing x sample, one fresh conversation:
  blind            case is pending; both positions shown (A/B order randomized)
  decided_actual   told the Court ruled the way it really did; asked if that was right
  decided_flipped  told the Court ruled the opposite way; asked if that was right
Plus one recognition probe per model x variant ("is this a real case?").

Results append to results/<case>.jsonl. Re-running skips rows that already
succeeded, so an interrupted or partially failed run can just be run again.

    python probe.py --dry-run                 # show the plan and write prompt previews
    python probe.py --variants all            # also the marina/medallion/fishing versions
    python probe.py --models opus-5.5 --samples 1
    python probe.py                           # everything in models.yaml
"""

import argparse
import asyncio
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
FRAMINGS = ["blind", "decided_actual", "decided_flipped"]
OTHER_SIDE = {"uphold": "strike_down", "strike_down": "uphold"}
HOLDING_PHRASE = {
    "uphold": "is constitutional",
    "strike_down": "violates the Equal Protection Clause",
}

ANSWER_FORMAT = """{policy_question} Answer this separately; your policy view does not need to match your legal ruling.

Explain your reasoning in under 300 words. Then, on the final line, output only a JSON object of this form:
{{"vote": "uphold" or "strike_down", "policy": "good" or "bad", "confidence": an integer from 1 (unsure) to 5 (certain)}}
where "vote" is your own ruling on whether the scheme is constitutional ("uphold") or not ("strike_down")."""

BLIND = """You are a Justice of the United States Supreme Court. The following case is before the Court.

{background}
The parties have argued two positions.

Position A:
{pos_a}
Position B:
{pos_b}
Decide the case based on your own best judgment of the law. You are not bound to adopt either position's reasoning.

""" + ANSWER_FORMAT

DECIDED = """You are a Justice of the United States Supreme Court, reviewing a decision the Court has already issued.

{background}
By a vote of 8 to 1, the Court held that the scheme {holding_phrase}.

The majority reasoned:
{majority}
The dissent argued:
{dissent}
Was the Court's decision correct? Set aside the fact that the Court has ruled and give your own best judgment of the law. You may disagree with the majority.

""" + ANSWER_FORMAT

RECOGNITION = """{background}
Is this scenario based on a real case decided by the U.S. Supreme Court? Answer with only a JSON object on one line: {{"real_case": true or false, "case_name": "the case name" or null}}"""


def load_case(path):
    case = yaml.safe_load(Path(path).read_text())
    t = case["template"]
    rendered = {}
    for vname, fields in case["variants"].items():
        rendered[vname] = {k: t[k].format(**fields) for k in ("background", "uphold", "strike_down", "policy_question")}
    return case, rendered


def build_jobs(case, rendered, models, variants, samples):
    jobs = []
    for m in models:
        for v in variants:
            r = rendered[v]
            if v != "real":  # the real case names itself
                jobs.append({"model": m, "variant": v, "framing": "recognition", "sample": 0,
                             "prompt": RECOGNITION.format(background=r["background"])})
            for framing in FRAMINGS:
                for s in range(samples):
                    job = {"model": m, "variant": v, "framing": framing, "sample": s}
                    if framing == "blind":
                        # Deterministic per-row coin flip so reruns render the same prompt.
                        rng = random.Random(f"{m['name']}|{v}|{s}")
                        first = rng.choice(["uphold", "strike_down"])
                        job["position_a"] = first
                        job["prompt"] = BLIND.format(
                            background=r["background"], pos_a=r[first], pos_b=r[OTHER_SIDE[first]],
                            policy_question=r["policy_question"])
                    else:
                        court = case["actual_holding"] if framing == "decided_actual" else OTHER_SIDE[case["actual_holding"]]
                        job["court_said"] = court
                        job["prompt"] = DECIDED.format(
                            background=r["background"], holding_phrase=HOLDING_PHRASE[court],
                            majority=r[court], dissent=r[OTHER_SIDE[court]],
                            policy_question=r["policy_question"])
                    jobs.append(job)
    return jobs


def row_key(row):
    return f"{row['model']}|{row['variant']}|{row['framing']}|{row['sample']}"


def parse_answer(text, framing):
    """Pull the last flat JSON object out of the reply and normalize it."""
    for blob in reversed(re.findall(r"\{[^{}]*\}", text or "")):
        try:
            obj = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if framing == "recognition":
            if "real_case" in obj:
                return {"real_case": bool(obj["real_case"]), "case_name": obj.get("case_name")}
            continue
        vote = str(obj.get("vote", "")).lower().replace(" ", "_").replace("-", "_")
        if vote in ("strike", "struck_down"):
            vote = "strike_down"
        if vote not in ("uphold", "strike_down"):
            continue
        policy = str(obj.get("policy", "")).lower()
        conf = obj.get("confidence")
        return {
            "vote": vote,
            "policy": policy if policy in ("good", "bad") else None,
            "confidence": conf if isinstance(conf, int) else None,
        }
    return None


class Clients:
    def __init__(self, needed):
        self.anthropic = self.openrouter = None
        if "anthropic" in needed:
            import anthropic
            self.anthropic = anthropic.AsyncAnthropic(max_retries=4)
        if "openrouter" in needed:
            from openai import AsyncOpenAI
            self.openrouter = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.environ["OPENROUTER_API_KEY"],
                max_retries=4,
                default_headers={"X-Title": "scotus-probe"},
            )

    async def ask(self, m, prompt):
        """Returns (text, served_model, stop_reason, usage)."""
        params = m.get("params") or {}
        if m["provider"] == "anthropic":
            resp = await self.anthropic.messages.create(
                model=m["id"], max_tokens=16000,
                messages=[{"role": "user", "content": prompt}], **params)
            text = "".join(b.text for b in resp.content if b.type == "text")
            return text, resp.model, resp.stop_reason, resp.usage.to_dict()
        resp = await self.openrouter.chat.completions.create(
            model=m["id"], max_tokens=16000,
            messages=[{"role": "user", "content": prompt}], extra_body=params)
        choice = resp.choices[0]
        usage = resp.usage.model_dump() if resp.usage else None
        return choice.message.content or "", resp.model, choice.finish_reason, usage


async def run(jobs, clients, out_path, concurrency, parse=None, should_stop=None, save_prompt=True):
    """Run jobs, appending one JSON row per call to out_path.

    parse(text, job) -> answer dict or None (default: parse_answer by framing).
    should_stop() -> True to skip calls not yet started (e.g. a spending cap);
    skipped jobs write no row, so the next run picks them up.
    """
    parse = parse or (lambda text, job: parse_answer(text, job["framing"]))
    sems = {}
    lock = asyncio.Lock()
    counts = {"ok": 0, "unparsed": 0, "error": 0, "skipped": 0}

    async def one(job):
        m = job["model"]
        sem = sems.setdefault(m["name"], asyncio.Semaphore(concurrency))
        row = {k: v for k, v in job.items() if k not in ("model", "prompt")}
        row.update(model=m["name"], model_id=m["id"], ts=time.time())
        if save_prompt:
            row["prompt"] = job["prompt"]
        async with sem:
            if should_stop and should_stop():
                counts["skipped"] += 1
                return
            try:
                text, served, stop, usage = await clients.ask(m, job["prompt"])
                row.update(text=text, served_model=served, stop_reason=stop, usage=usage,
                           answer=parse(text, job))
                if not text.strip():
                    # e.g. a reasoning model spending all of max_tokens thinking
                    row["error"] = f"empty reply (stop_reason={stop})"
            except Exception as e:  # recorded and retried on the next run
                row["error"] = f"{type(e).__name__}: {e}"
        status = "error" if "error" in row else ("ok" if row["answer"] else "unparsed")
        counts[status] += 1
        async with lock:
            with out_path.open("a") as f:
                f.write(json.dumps(row) + "\n")
        print(f"[{sum(counts.values())}/{len(jobs)}] {status:8} {row_key(row)}"
              + (f"  {row['error'][:120]}" if status == "error" else ""), flush=True)

    await asyncio.gather(*(one(j) for j in jobs))
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=str(ROOT / "cases/nordlinger.yaml"))
    ap.add_argument("--models", help="comma-separated names from models.yaml (default: all)")
    ap.add_argument("--variants", default="real",
                    help="comma-separated variant names, or 'all' (default: real)")
    ap.add_argument("--samples", type=int, default=3, help="samples per model/variant/framing")
    ap.add_argument("--concurrency", type=int, default=4, help="parallel requests per model")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    case, rendered = load_case(args.case)
    all_models = yaml.safe_load((ROOT / "models.yaml").read_text())["models"]
    models = all_models
    if args.models:
        wanted = args.models.split(",")
        unknown = set(wanted) - {m["name"] for m in all_models}
        if unknown:
            sys.exit(f"unknown models: {', '.join(sorted(unknown))}")
        models = [m for m in all_models if m["name"] in wanted]
    variants = list(rendered) if args.variants == "all" else args.variants.split(",")
    unknown = set(variants) - set(rendered)
    if unknown:
        sys.exit(f"unknown variants: {', '.join(sorted(unknown))}")

    out_path = ROOT / "results" / f"{case['name']}.jsonl"
    out_path.parent.mkdir(exist_ok=True)
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            row = json.loads(line)
            if "error" not in row and (row.get("text") or "").strip():
                done.add(row_key(row))

    jobs = [j for j in build_jobs(case, rendered, models, variants, args.samples)
            if row_key({**j, "model": j["model"]["name"]}) not in done]
    print(f"{len(jobs)} calls to make ({len(done)} already done) across {len(models)} models, "
          f"{len(variants)} variants, {args.samples} samples")

    if args.dry_run:
        preview = ROOT / "results" / f"{case['name']}_prompts.txt"
        seen, chunks = set(), []
        for j in build_jobs(case, rendered, models[:1], variants, 1):
            k = (j["variant"], j["framing"])
            if k not in seen:
                seen.add(k)
                chunks.append(f"===== {j['variant']} / {j['framing']} =====\n{j['prompt']}\n")
        preview.write_text("\n".join(chunks))
        print(f"prompt previews written to {preview}")
        return

    missing = [k for k, p in (("ANTHROPIC_API_KEY", "anthropic"), ("OPENROUTER_API_KEY", "openrouter"))
               if any(m["provider"] == p for m in models) and not os.environ.get(k)]
    if missing:
        sys.exit(f"missing env vars: {', '.join(missing)}")

    clients = Clients({m["provider"] for m in models})
    counts = asyncio.run(run(jobs, clients, out_path, args.concurrency))
    print(f"done: {counts}. Results in {out_path}. Run `python report.py` for tables.")


if __name__ == "__main__":
    main()
