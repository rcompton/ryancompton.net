"""Draw law_vs_policy.svg: per model, how often it votes with the liberal justices on the law
versus how often it prefers the liberal side's outcome.

    python plot_gap.py
"""

import json
from pathlib import Path

from report_bench import dissent_direction

ROOT = Path(__file__).parent
NAMES = {
    "opus-5.5": "Claude Opus", "sonnet-5.5": "Claude Sonnet", "gpt-6.1-sol": "GPT-6.1",
    "gemini-3.8-flash": "Gemini", "grok-4.7": "Grok", "llama-4-maverick": "Llama", "deepseek-v4-pro": "DeepSeek",
    "qwen3.8-max": "Qwen", "kimi-k3": "Kimi", "glm-5.3": "GLM", "mistral-large-4": "Mistral",
    "command-a-plus": "Command A+", "jev-router": "Jev router",
}
LAW, POLICY = "#64748b", "#2563eb"


def main():
    cases = {p.stem: json.loads(p.read_text()) for p in (ROOT / "data/cases").glob("*.json")}
    rows = {}
    for line in (ROOT / "results/bench.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "error" in r or not r.get("answer") or not r["answer"]["outcome"]:
            continue
        direction = dissent_direction(cases[r["variant"]]) if cases[r["variant"]]["minority_vote"] else None
        if direction:
            rows[(r["model"], r["variant"], r["sample"])] = (r, direction == "liberal")
    points = []
    for m in NAMES:
        rs = [(r, dl) for (mm, _, _), (r, dl) in rows.items() if mm == m]
        law = sum((r["answer"]["side"] == "dissent") == dl for r, dl in rs) / len(rs)
        pol = sum((r["answer"]["outcome"] == "bad") == dl for r, dl in rs) / len(rs)
        points.append((NAMES[m], law, pol))
    points.sort(key=lambda p: p[1])

    W, L, R, T, row = 680, 120, 30, 50, 28
    H = T + row * len(points) + 50

    def x(v):  # 20%..100%
        return L + (W - L - R) * (v - 0.2) / 0.8

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         'font-family="-apple-system, Helvetica, Arial, sans-serif" font-size="12">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<circle cx="{L}" cy="18" r="5" fill="{LAW}"/><text x="{L + 10}" y="22" fill="#333">votes with the liberal justices on the law</text>',
         f'<circle cx="{L + 270}" cy="18" r="5" fill="{POLICY}"/><text x="{L + 280}" y="22" fill="#333">prefers the liberal outcome</text>']
    for v in (0.2, 0.4, 0.6, 0.8, 1.0):
        s.append(f'<line x1="{x(v):.1f}" y1="{T - 10}" x2="{x(v):.1f}" y2="{H - 40}" stroke="#eee"/>'
                 f'<text x="{x(v):.1f}" y="{H - 24}" text-anchor="middle" fill="#666">{int(v * 100)}%</text>')
    for i, (name, law, pol) in enumerate(points):
        cy = T + row * i + row / 2
        s.append(f'<text x="{L - 12}" y="{cy + 4:.1f}" text-anchor="end" fill="#111">{name}</text>'
                 f'<line x1="{x(law):.1f}" y1="{cy:.1f}" x2="{x(pol):.1f}" y2="{cy:.1f}" stroke="#cbd5e1" stroke-width="3"/>'
                 f'<circle cx="{x(law):.1f}" cy="{cy:.1f}" r="5.5" fill="{LAW}"/>'
                 f'<circle cx="{x(pol):.1f}" cy="{cy:.1f}" r="5.5" fill="{POLICY}"/>')
    s.append("</svg>")
    (ROOT / "law_vs_policy.svg").write_text("\n".join(s))


if __name__ == "__main__":
    main()
