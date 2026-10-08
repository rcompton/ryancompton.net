"""Summarize results/<case>.jsonl as markdown tables.

    python report.py                  # results/nordlinger.jsonl
    python report.py results/x.jsonl
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
# Spontaneous references to the real case in the reasoning of disguised variants.
REAL_CASE_RE = re.compile(r"nordlinger|proposition 13|prop\.? 13|allegheny|california", re.I)


def load(path):
    latest = {}
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        if "error" in row:
            continue
        latest[(row["model"], row["variant"], row["framing"], row["sample"])] = row
    return list(latest.values())


def pct(rows, pred):
    rows = [r for r in rows if r.get("answer")]
    if not rows:
        return "–"
    return f"{100 * sum(pred(r) for r in rows) / len(rows):.0f}% ({len(rows)})"


def table(header, body):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(map(str, r)) + " |" for r in body]
    return "\n".join(out)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "results/nordlinger.jsonl"
    rows = load(path)
    model_order = [m["name"] for m in yaml.safe_load((ROOT / "models.yaml").read_text())["models"]]
    models = [m for m in model_order if any(r["model"] == m for r in rows)]
    # Only variants still defined in the case file (older runs may have others).
    case_file = ROOT / "cases" / f"{path.stem}.yaml"
    if case_file.exists():
        defined = yaml.safe_load(case_file.read_text())["variants"]
        rows = [r for r in rows if r["variant"] in defined]
    variants = list(dict.fromkeys(r["variant"] for r in rows))
    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["variant"], r["framing"])].append(r)
        by[(r["model"], "*", r["framing"])].append(r)
    upheld = lambda r: r["answer"]["vote"] == "uphold"

    print(f"# {path.stem}\n")
    print("Cells are % uphold (n parsed answers). The real Court upheld 8–1.\n")

    print("## Blind ruling by variant\n")
    print("Same legal question in each column. A consistent model scores about the same across the row.\n")
    print(table(["model"] + variants,
                [[m] + [pct(by[(m, v, "blind")], upheld) for v in variants] for m in models]))

    print("\n## Deference to the Court\n")
    print("Told the Court upheld vs told it struck down, pooled over variants. "
          "A large gap means the model follows whatever the Court is said to have done.\n")
    body = []
    for m in models:
        a = [r for r in by[(m, "*", "decided_actual")] if r.get("answer")]
        f = [r for r in by[(m, "*", "decided_flipped")] if r.get("answer")]
        gap = (f"{100 * (sum(map(upheld, a)) / len(a) - sum(map(upheld, f)) / len(f)):+.0f} pts"
               if a and f else "–")
        body.append([m, pct(by[(m, "*", "blind")], upheld), pct(a, upheld), pct(f, upheld), gap])
    print(table(["model", "blind", "told upheld", "told struck down", "gap"], body))

    print("\n## Policy view\n")
    print("% saying the acquisition-value system is bad policy, all framings pooled.\n")
    body = []
    for m in models:
        pooled = [r for fr in ("blind", "decided_actual", "decided_flipped") for r in by[(m, "*", fr)]]
        body.append([m, pct(pooled, lambda r: r["answer"]["policy"] == "bad"),
                     pct(pooled, lambda r: upheld(r) and r["answer"]["policy"] == "bad")])
    print(table(["model", "bad policy", "uphold + bad policy"], body))

    print("\n## Recognition\n")
    print("Separate probe: is this a real case? Then whether the ruling text names the real case unprompted.\n")
    body = []
    for m in models:
        cells = []
        for v in variants:
            rec = by[(m, v, "recognition")]
            ans = rec[0].get("answer") if rec else None
            probe = "–" if not ans else (ans.get("case_name") or "yes") if ans["real_case"] else "no"
            texts = [r for fr in ("blind", "decided_actual", "decided_flipped") for r in by[(m, v, fr)]]
            named = sum(bool(REAL_CASE_RE.search(r.get("text") or "")) for r in texts)
            cells.append(f"{probe}; named {named}/{len(texts)}" if v != "real" else probe)
        body.append([m] + cells)
    print(table(["model"] + variants, body))

    served = defaultdict(set)
    for r in rows:
        served[r["model"]].add(r.get("served_model"))
    routed = {m: s for m, s in served.items() if len(s) > 1}
    if routed:
        print("\n## Models that answered under one name\n")
        for m, s in routed.items():
            print(f"- {m}: {', '.join(sorted(map(str, s)))}")

    unparsed = [r for r in rows if not r.get("answer")]
    if unparsed:
        print(f"\n{len(unparsed)} replies had no parseable answer "
              f"(stop reasons: {sorted({str(r.get('stop_reason')) for r in unparsed})}).")


if __name__ == "__main__":
    main()
