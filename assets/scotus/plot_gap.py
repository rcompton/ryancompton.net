"""Draw law_vs_policy.svg: every answer from every model on the split cases, as a 2x2 table of
its legal vote (liberal or conservative side) against the result it prefers.

    python plot_gap.py
"""

import json
from collections import Counter
from pathlib import Path

from report_bench import dissent_direction

ROOT = Path(__file__).parent


def main():
    cases = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data/cases").glob("*.json")}
    rows = {}
    for line in (ROOT / "results/bench.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "error" in r or not r.get("answer") or not r["answer"]["outcome"] or r["variant"] not in cases:
            continue
        case = cases[r["variant"]]
        direction = dissent_direction(case) if case["minority_vote"] else None
        if direction:
            rows[(r["model"], r["variant"], r["sample"])] = (r, direction == "liberal")
    t = Counter()
    for r, dissent_liberal in rows.values():
        law = "liberal" if (r["answer"]["side"] == "dissent") == dissent_liberal else "conservative"
        pol = "liberal" if (r["answer"]["outcome"] == "bad") == dissent_liberal else "conservative"
        t[law, pol] += 1

    W, H, L, T, cw, ch = 560, 250, 200, 70, 170, 80
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         'font-family="-apple-system, Helvetica, Arial, sans-serif" font-size="14">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<text x="{L + cw}" y="22" text-anchor="middle" fill="#333" font-weight="bold">Preferred result</text>']
    for j, pol in enumerate(("liberal", "conservative")):
        s.append(f'<text x="{L + cw * j + cw / 2}" y="{T - 14}" text-anchor="middle" fill="#333">{pol}</text>')
    s.append(f'<text x="24" y="{T + ch}" fill="#333" font-weight="bold">Reading of</text>'
             f'<text x="24" y="{T + ch + 18}" fill="#333" font-weight="bold">the law</text>')
    for i, law in enumerate(("liberal", "conservative")):
        y = T + ch * i
        s.append(f'<text x="{L - 14}" y="{y + ch / 2 + 5}" text-anchor="end" fill="#333">{law}</text>')
        for j, pol in enumerate(("liberal", "conservative")):
            x = L + cw * j
            n = t[law, pol]
            if law == pol:
                fill, color, weight = "#f1f5f9", "#64748b", "normal"
            elif law == "conservative":
                fill, color, weight = "#2563eb", "white", "bold"
            else:
                fill, color, weight = "#dbeafe", "#1e3a8a", "bold"
            s.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{fill}" stroke="white" stroke-width="3"/>'
                     f'<text x="{x + cw / 2}" y="{y + ch / 2 + 9}" text-anchor="middle" fill="{color}" '
                     f'font-size="26" font-weight="{weight}">{n:,}</text>')
    s.append("</svg>")
    (ROOT / "law_vs_policy.svg").write_text("\n".join(s))


if __name__ == "__main__":
    main()
