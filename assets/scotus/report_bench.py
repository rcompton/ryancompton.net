"""Summarize results/bench.jsonl.

    python report_bench.py
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).parent
MIN_SHARED = 8  # minimum cases in common before comparing a model with a justice
LIBERAL = {"Stevens", "Souter", "Ginsburg", "Breyer", "Sotomayor", "Kagan", "Jackson"}
CONSERVATIVE = {"Scalia", "Thomas", "Alito", "Roberts", "Gorsuch", "Kavanaugh", "Barrett"}


def dissent_direction(case):
    """'liberal' or 'conservative' if that bloc dissented and the other mostly didn't, else None."""
    v = case["votes"]

    def share(bloc):
        members = [j for j in v if j in bloc]
        return sum(v[j] == "minority" for j in members) / len(members) if members else 0

    gap = share(LIBERAL) - share(CONSERVATIVE)
    return "liberal" if gap > 0.3 else "conservative" if gap < -0.3 else None


def table(header, body):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(map(str, r)) + " |" for r in body]
    return "\n".join(out)


def pct(k, n):
    return f"{100 * k / n:.0f}%" if n else "–"


def main():
    cases = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data/cases").glob("*.json")}
    rows = {}
    for line in (ROOT / "results/bench.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "error" not in r and r.get("answer") and r["variant"] in cases:
            rows[(r["model"], r["variant"], r["sample"])] = r
    rows = list(rows.values())
    # Unanimous cases get their own section at the end; everything else is split decisions.
    unanimous = [r for r in rows if not cases[r["variant"]]["minority_vote"]]
    rows = [r for r in rows if cases[r["variant"]]["minority_vote"]]
    order = [m["name"] for m in yaml.safe_load((ROOT / "models.yaml").read_text())["models"]]
    models = [m for m in order if any(r["model"] == m for r in rows)]

    # Each model's position per case: share of its samples siding with the dissent.
    dissent_share = defaultdict(dict)
    by_mc = defaultdict(list)
    for r in rows:
        by_mc[(r["model"], r["variant"])].append(r)
    for (m, c), rs in by_mc.items():
        dissent_share[m][c] = sum(r["answer"]["side"] == "dissent" for r in rs) / len(rs)

    covered = sorted({r["variant"] for r in rows})
    print(f"# Supreme Court benchmark\n\n{len(rows)} answers on {len(covered)} split decisions, "
          f"{len(unanimous)} on {len({r['variant'] for r in unanimous})} unanimous ones; {len(models)} models.\n"
          "Every section except the last uses split decisions only.\n")

    # 1. Go / no-go: do models ever side with the dissent?
    print("## How often each model sides with the dissent\n")
    body = []
    for m in models:
        rs = [r for r in rows if r["model"] == m]
        dis = sum(r["answer"]["side"] == "dissent" for r in rs)
        mf = [r for r in rs if r.get("order") == "majority_first"]
        df = [r for r in rs if r.get("order") == "dissent_first"]
        body.append([m, f"{pct(dis, len(rs))} ({len(rs)})",
                     pct(sum(r["answer"]["side"] == "dissent" for r in mf), len(mf)),
                     pct(sum(r["answer"]["side"] == "dissent" for r in df), len(df))])
    print("Real justices in these same cases dissent about "
          + pct(sum(v == "minority" for c in covered for v in cases[c]["votes"].values()),
                sum(len(cases[c]["votes"]) for c in covered))
          + " of the time.\n")
    print("The last two columns split by which side's opinions were shown first. "
          "A big difference means the model is swayed by order, not argument.\n")
    print(table(["model", "sides with dissent", "majority shown first", "dissent shown first"], body))

    # 2. Cases where models split.
    print("\n## Cases where models split\n")
    body = []
    for c in covered:
        shares = [dissent_share[m][c] for m in models if c in dissent_share[m]]
        if not shares:
            continue
        n_dis = sum(s >= 0.5 for s in shares)
        body.append((n_dis, [f"{cases[c]['name'][:60]} ({cases[c]['term']})",
                             f"{cases[c]['majority_vote']}-{cases[c]['minority_vote']}",
                             f"{n_dis}/{len(shares)}"]))
    body.sort(key=lambda x: -x[0])
    print("Models counted as siding with the dissent if at least half their samples did.\n")
    print(table(["case", "Court's vote", "models siding with dissent"], [b for _, b in body]))

    # 3. Which justice each model votes like.
    print("\n## Which justice each model votes like\n")
    print(f"Agreement = share of shared cases where the model's side matches the justice's vote "
          f"(cases with at least {MIN_SHARED} in common). Top 3 and bottom 1 per model.\n")
    justices = sorted({j for c in covered for j in cases[c]["votes"]})
    body = []
    for m in models:
        scores = []
        for j in justices:
            shared = [c for c in dissent_share[m] if j in cases[c]["votes"]]
            if len(shared) < MIN_SHARED:
                continue
            agree = sum(1 - abs(dissent_share[m][c] - (cases[c]["votes"][j] == "minority")) for c in shared)
            scores.append((agree / len(shared), j, len(shared)))
        scores.sort(reverse=True)
        fmt = lambda s: f"{s[1]} {100 * s[0]:.0f}% ({s[2]})"
        body.append([m, ", ".join(map(fmt, scores[:3])), fmt(scores[-1]) if scores else "–"])
    print(table(["model", "most similar", "least similar"], body))
    in_maj = {j: (sum(cases[c]["votes"][j] == "majority" for c in covered if j in cases[c]["votes"]),
                  sum(j in cases[c]["votes"] for c in covered)) for j in justices}
    print("\nCaution: a model that always sided with the Court would score "
          + ", ".join(f"{j} {pct(a, n)}" for j, (a, n) in sorted(in_maj.items(), key=lambda x: -x[1][0] / x[1][1])
                      if n >= MIN_SHARED * 5)
          + ". High similarity to the justices usually in the majority mostly means agreeing with the Court; "
          "the next section shows which way a model breaks when it doesn't.")

    # 3b. When the model breaks from the Court, who else dissented?
    print("\n## When a model breaks from the Court, who dissented with it\n")
    print("Cases where the model sided with the dissent: share of them in which each justice also dissented. Top 3.\n")
    body = []
    for m in models:
        ds = [c for c, v in dissent_share[m].items() if v >= 0.5]
        hit, seen = Counter(), Counter()
        for c in ds:
            for j, v in cases[c]["votes"].items():
                seen[j] += 1
                hit[j] += v == "minority"
        top = sorted(((hit[j] / seen[j], j) for j in seen if seen[j] >= MIN_SHARED), reverse=True)[:3]
        body.append([m, len(ds), ", ".join(f"{j} {100 * x:.0f}%" for x, j in top) or "–"])
    print(table(["model", "cases it dissents in", "justices dissenting alongside it"], body))

    # 4. Law vs outcome.
    print("\n## Law vs outcome\n")
    print("How often the model says the law requires a result it thinks is bad for the country, or the reverse.\n")
    body = []
    for m in models:
        rs = [r for r in rows if r["model"] == m and r["answer"]["outcome"]]
        maj_bad = sum(r["answer"]["side"] == "majority" and r["answer"]["outcome"] == "bad" for r in rs)
        dis_good = sum(r["answer"]["side"] == "dissent" and r["answer"]["outcome"] == "good" for r in rs)
        body.append([m, pct(maj_bad, len(rs)), pct(dis_good, len(rs)), len(rs)])
    print(table(["model", "majority right, outcome bad", "dissent right, outcome good", "n"], body))

    # 4b. Law vs policy by direction: is the model's legal vote to the left or right of the outcome it wants?
    print("\n## Legal vote vs preferred outcome, left/right\n")
    print("Cases where the liberal and conservative justices split. 'Liberal on the law' = voted with the side the "
          "liberal justices took; 'prefers liberal outcome' = said the liberal side's result is better for the "
          "country (the Court's result if it called the outcome good, the dissent's if bad). The last two columns "
          "count answers where the two disagree, in each direction.\n")
    body = []
    for m in models:
        rs = [r for r in rows if r["model"] == m and r["answer"]["outcome"]
              and dissent_direction(cases[r["variant"]])]
        law = pol = law_con_pol_lib = law_lib_pol_con = 0
        for r in rs:
            dissent_liberal = dissent_direction(cases[r["variant"]]) == "liberal"
            law_lib = (r["answer"]["side"] == "dissent") == dissent_liberal
            pol_lib = (r["answer"]["outcome"] == "bad") == dissent_liberal
            law += law_lib
            pol += pol_lib
            law_con_pol_lib += pol_lib and not law_lib
            law_lib_pol_con += law_lib and not pol_lib
        n = len(rs)
        body.append([m, pct(law, n), pct(pol, n), f"{100 * (pol - law) / n:+.0f}" if n else "–",
                     pct(law_con_pol_lib, n), pct(law_lib_pol_con, n), n])
    print(table(["model", "liberal on the law", "prefers liberal outcome", "gap (points)",
                 "law conservative, outcome liberal", "law liberal, outcome conservative", "n"], body))

    # 5. Whose opinions models pick as closest to their view.
    print("\n## Opinion closest to the model's view\n")
    body = []
    for m in models:
        picks = Counter((r["answer"]["closest_opinion"] or "?").split()[-1].strip(".,").title()
                        for r in rows if r["model"] == m)
        body.append([m, ", ".join(f"{a} {n}" for a, n in picks.most_common(5))])
    print(table(["model", "most-picked authors (count)"], body))

    # 6. Unanimous decisions: how often a model would dissent when all nine Justices agreed.
    if unanimous:
        print("\n## Unanimous decisions (baseline)\n")
        print("When every Justice agreed, the legal answer is rarely close, so a model's dissent rate here "
              "is roughly its noise floor or contrarianism. Compare with its split-decision rate.\n")
        body = []
        for m in models:
            us = [r for r in unanimous if r["model"] == m]
            ss = [r for r in rows if r["model"] == m]
            body.append([m, f"{pct(sum(r['answer']['side'] == 'dissent' for r in us), len(us))} ({len(us)})",
                         pct(sum(r["answer"]["side"] == "dissent" for r in ss), len(ss)),
                         pct(sum(r["answer"]["outcome"] == "bad" for r in us), len(us))])
        print(table(["model", "dissents from unanimous Court", "dissents in split cases", "unanimous outcome bad"], body))
        dissents = Counter(cases[r["variant"]]["name"][:60] for r in unanimous if r["answer"]["side"] == "dissent")
        if dissents:
            print("\nUnanimous cases drawing the most model dissents: "
                  + "; ".join(f"{c} ({n})" for c, n in dissents.most_common(5)))


if __name__ == "__main__":
    main()
