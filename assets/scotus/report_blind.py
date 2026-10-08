"""Compare the labeled run (results/bench.jsonl) with the blind run (results/blind.jsonl),
and report how often each model sides with the government.

    python report_blind.py
"""

import json
from collections import defaultdict
from pathlib import Path

import yaml

from report_bench import pct, table

ROOT = Path(__file__).parent


def load(path):
    rows = {}
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if "error" not in r and r.get("answer"):
                rows[(r["model"], r["variant"], r["sample"])] = r
    return list(rows.values())


def main():
    cases = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data/cases").glob("*.json")}
    gov_won = yaml.safe_load((ROOT / "data/government_side.yaml").read_text())["gov_won"]
    labeled, blind = load(ROOT / "results/bench.jsonl"), load(ROOT / "results/blind.jsonl")
    order = [m["name"] for m in yaml.safe_load((ROOT / "models.yaml").read_text())["models"]]
    blind_models = [m for m in order if any(r["model"] == m for r in blind)]
    print(f"# Blind vs labeled\n\n{len(blind)} blind answers, {len(labeled)} labeled answers.\n")

    def agree(rows, m, case_ids=None):
        rs = [r for r in rows if r["model"] == m and (case_ids is None or r["variant"] in case_ids)]
        return sum(r["answer"]["side"] == "majority" for r in rs), len(rs)

    # 1. Does removing the name, vote and labels change agreement with the Court?
    print("## Agreement with the Court's majority\n")
    print("Labeled: case name, vote count, and opinions labeled majority/dissent with authors. "
          "Blind: none of those; opinions grouped as Side A / Side B at random. "
          "Same cases in both columns (cases the model answered in both runs).\n")
    body = []
    for m in blind_models:
        both = {r["variant"] for r in blind if r["model"] == m} & {r["variant"] for r in labeled if r["model"] == m}
        a, n = agree(labeled, m, both)
        b, k = agree(blind, m, both)
        body.append([m, f"{pct(a, n)} ({n})", f"{pct(b, k)} ({k})", f"{100 * (b / k - a / n):+.0f}" if n and k else "–"])
    print(table(["model", "labeled", "blind", "change (points)"], body))

    # 2. Memory: does the model know the case and who won?
    print("\n## Does the model recognize the case?\n")
    print("From the blind run. 'Recalls winner' = the model named the side the Court actually ruled for. "
          "The last two columns split agreement with the Court by whether it recalled the winner.\n")
    body = []
    for m in blind_models:
        rs = [r for r in blind if r["model"] == m]
        rec = [r for r in rs if r["answer"].get("recognized_case")]
        right = [r for r in rs if r["answer"].get("recalled_winner") == "correct"]
        other = [r for r in rs if r["answer"].get("recalled_winner") != "correct"]
        body.append([m, pct(len(rec), len(rs)), pct(len(right), len(rs)),
                     f"{pct(sum(r['answer']['side'] == 'majority' for r in right), len(right))} ({len(right)})",
                     f"{pct(sum(r['answer']['side'] == 'majority' for r in other), len(other))} ({len(other)})"])
    print(table(["model", "names the case", "recalls winner", "agrees w/ Court | recalls", "agrees w/ Court | doesn't"], body))

    # 3. Position: Side A is always shown first.
    print("\n## Position effect (blind run)\n")
    print("Side A is always shown first; which side is the majority is random. 50% means no position bias.\n")
    body = []
    for m in blind_models:
        rs = [r for r in blind if r["model"] == m]
        picks_a = sum((r["answer"]["side"] == "majority") == (r["majority_label"] == "A") for r in rs)
        body.append([m, f"{pct(picks_a, len(rs))} ({len(rs)})"])
    print(table(["model", "picks Side A"], body))

    # 4. Government vs private party.
    print("\n## Siding with the government\n")
    print(f"{len(gov_won)} cases where a government or official faced a private party "
          f"(the Court sided with the government in {sum(gov_won.values())}). "
          "Share of answers siding with the government.\n")

    def pro_gov(rows, m):
        rs = [r for r in rows if r["model"] == m and r["variant"] in gov_won]
        k = sum((r["answer"]["side"] == "majority") == gov_won[r["variant"]] for r in rs)
        return f"{pct(k, len(rs))} ({len(rs)})" if rs else "–"

    models = [m for m in order if any(r["model"] == m for r in labeled)]
    print(table(["model", "labeled", "blind"], [[m, pro_gov(labeled, m), pro_gov(blind, m)] for m in models]))
    jus = defaultdict(lambda: [0, 0])
    for c, won in gov_won.items():
        for j, v in cases[c]["votes"].items():
            jus[j][0] += (v == "majority") == won
            jus[j][1] += 1
    print("\nReal justices, same cases: "
          + ", ".join(f"{j} {pct(k, n)}" for j, (k, n) in sorted(jus.items(), key=lambda x: -x[1][0] / x[1][1]) if n >= 8))


if __name__ == "__main__":
    main()
