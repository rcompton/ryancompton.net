"""Draw positions.svg: models and justices by left/right lean and agreement with the Court.

    python plot_positions.py    # reads results/positions.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
W, H, L, R, T, B = 720, 470, 70, 30, 30, 60

NAMES = {
    "opus-5.5": "Opus", "sonnet-5.5": "Sonnet", "gpt-6.1-sol": "GPT-6.1", "gemini-3.8-flash": "Gemini",
    "grok-4.7": "Grok", "llama-4-maverick": "Llama", "deepseek-v4-pro": "DeepSeek", "qwen3.8-max": "Qwen",
    "kimi-k3": "Kimi", "glm-5.3": "GLM", "mistral-large-4": "Mistral", "command-a-plus": "Command A+",
    "jev-router": "Jev",
}
# Label placement (dx, dy, text-anchor), hand-tuned so labels don't collide.
OFFSETS = {
    "Opus": (-8, -6, "end"), "Sonnet": (8, -6, "start"), "Gemini": (8, 10, "start"), "Jev": (8, -6, "start"),
    "Qwen": (-8, 4, "end"), "Kimi": (-6, 18, "end"), "Command A+": (8, -4, "start"), "GPT-6.1": (8, 18, "start"),
    "GLM": (-8, 4, "end"), "Grok": (-8, 4, "end"), "Llama": (8, 14, "start"), "DeepSeek": (8, 4, "start"),
    "Mistral": (-8, 4, "end"), "Kavanaugh": (8, 4, "start"), "Barrett": (-8, 12, "end"),
    "Roberts": (-8, -4, "end"), "Gorsuch": (-8, 4, "end"), "Alito": (-8, 4, "end"), "Scalia": (-8, 12, "end"),
    "Thomas": (-8, 4, "end"), "Kagan": (0, -10, "middle"), "Breyer": (-4, 20, "middle"),
    "Ginsburg": (-8, -6, "end"), "Sotomayor": (-8, 10, "end"), "Jackson": (8, 4, "start"),
}


def x(conservative_share):
    return L + (W - L - R) * conservative_share


def y(with_court):
    return T + (H - T - B) * (1 - (with_court - 0.30) / (0.95 - 0.30))


def main():
    pos = json.loads((ROOT / "results/positions.json").read_text())
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         'font-family="-apple-system, Helvetica, Arial, sans-serif" font-size="12">',
         f'<rect width="{W}" height="{H}" fill="white"/>']
    for v in (0, .25, .5, .75, 1):
        s.append(f'<line x1="{x(v)}" y1="{T}" x2="{x(v)}" y2="{H - B}" stroke="#eee"/>'
                 f'<text x="{x(v)}" y="{H - B + 16}" text-anchor="middle" fill="#666">{int(v * 100)}%</text>')
    for v in (.3, .4, .5, .6, .7, .8, .9):
        s.append(f'<line x1="{L}" y1="{y(v):.1f}" x2="{W - R}" y2="{y(v):.1f}" stroke="#eee"/>'
                 f'<text x="{L - 8}" y="{y(v) + 4:.1f}" text-anchor="end" fill="#666">{int(v * 100)}%</text>')
    s.append(f'<text x="{(L + W - R) / 2}" y="{H - 14}" text-anchor="middle" fill="#333">'
             '← liberal · share of votes with the conservative side · conservative →</text>')
    s.append(f'<text transform="translate(18,{(T + H - B) / 2}) rotate(-90)" text-anchor="middle" '
             'fill="#333">sides with the Court\'s majority</text>')
    for key, v in pos.items():
        cx, cy = x(1 - v["lib"]), y(v["court"])
        label = NAMES.get(key, key)
        dx, dy, anchor = OFFSETS.get(label, (8, 4, "start"))
        if v["kind"] == "justice":
            s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="none" stroke="#888" stroke-width="1.5"/>'
                     f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" text-anchor="{anchor}" fill="#777" '
                     f'font-style="italic">{label}</text>')
        else:
            s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5.5" fill="#2563eb"/>'
                     f'<text x="{cx + dx:.1f}" y="{cy + dy:.1f}" text-anchor="{anchor}" fill="#111">{label}</text>')
    s.append("</svg>")
    (ROOT / "positions.svg").write_text("\n".join(s))


if __name__ == "__main__":
    main()
