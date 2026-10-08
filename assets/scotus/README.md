# scotus-probe

How do language models vote on real Supreme Court cases when they read the full opinions and are free to disagree with the Court? Write-up: [Which Supreme Court Justice is your chatbot?](https://ryancompton.net/2026/10/08/ai-supreme-court.html)

## Setup

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export OPENROUTER_API_KEY=...   # every model in models.yaml goes through OpenRouter, Claude included
```

Models are listed in `models.yaml`. `jev-router` is a router, so `served_model` in each result row records which model actually answered.

## The benchmark (`bench.py`)

```sh
.venv/bin/python fetch_cases.py --n 200 --unanimous 50   # random cases, terms 2005-2025
.venv/bin/python bench.py --dry-run                      # prompt sizes and estimated cost
.venv/bin/python bench.py --samples 1 --max-spend 200
.venv/bin/python report_bench.py > results/bench_report.md
```

`fetch_cases.py` takes votes, facts and the question presented from the [Oyez API](https://api.oyez.org), and the opinion text from [Cornell LII](https://www.law.cornell.edu/supremecourt/text) at LII's 10-second crawl delay. Cases are saved to `data/cases/`. Older pages (before about 2010) don't mark dissents in a way the parser finds, so in practice the cases are from 2010–2025.

Each model gets the case name, the vote count, the facts, the question presented, and every opinion in full. Whether the majority's or the dissent's opinions come first is random. It answers three things:
1. whose reading of the law is correct, the majority's or the dissent's
2. which opinion is closest to its view
3. whether the outcome was good or bad for the country, separately from the law

Results go to `results/bench.jsonl`. A rerun skips calls that already succeeded, and `--max-spend` stops new calls once the OpenRouter key's total usage reaches that amount. Only one run can write to a results file at a time.

`report_bench.py` produces:
- each model's dissent rate, split by which side was shown first
- per-case splits
- which justices each model votes like, plus which justices dissent alongside it when it breaks from the Court
- law-vs-outcome splits
- a baseline from the unanimous cases

`report_blind.py` compares this with `--framing blind`, which removes the case name, vote and labels. That framing turned out not to blind anything: every model still named each case and who won. It also reports how often each model sides with the government, using the hand labels in `data/government_side.yaml`.

## Nordlinger v. Hahn (`probe.py`)

The first experiment: the 1992 Prop 13 case (8–1, Stevens dissenting). It's written as a template in `cases/nordlinger.yaml`, with variants that apply the same legal structure to other fees (`--variants all`). Each variant is asked three ways:
- blind
- told the Court upheld
- told the Court struck it down

```sh
.venv/bin/python probe.py --dry-run
.venv/bin/python probe.py
.venv/bin/python report.py
```

Every model upheld Prop 13 and called it bad policy. A disguised version was dropped because 12 of 13 models recognized it as Nordlinger anyway.
