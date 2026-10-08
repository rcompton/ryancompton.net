---
title: "Which Supreme Court Justice is your chatbot?"
description: "13 language models read the full opinions in 250 Supreme Court cases and voted. Claude sides with the Court, GPT votes with Sotomayor, and Grok votes like Scalia."
tags: ["politics", "llm"]
image: "/assets/scotus/positions.svg"
---

I think *Nordlinger v. Hahn*, the 1992 case that upheld California's Prop 13, was wrongly decided, and I agree with Justice Stevens's lone dissent. I wondered whether AI models would agree with me. So I gave 13 of them the case, with the facts and the full text of every opinion, and asked how they'd vote.

All 13 upheld Prop 13. Every one also said it was bad policy. So much for that.

The broader question was more interesting. How do models vote on Supreme Court cases in general, and which justices do they vote like?

![Models and justices by ideology and agreement with the Court](/assets/scotus/positions.svg)

<!--more-->

## Setup

I picked 200 random split decisions and 50 unanimous ones, almost all from 2010–2025. Each model got the case name, the vote count, the facts, the question presented, and the full text of every opinion: majority, concurrences and dissents. The majority's opinions came first in half the prompts and the dissents' in the other half. I asked each model three things:

1. Whose reading of the law is correct, the majority's or the dissent's?
2. Which single opinion is closest to your view?
3. Separately from the law, was the outcome good or bad for the country?

The models were Claude Opus 5.5 and Sonnet 5.5, GPT-6.1, Gemini 3.8 Flash, Grok 4.7, Llama 4 Maverick, DeepSeek v4, Qwen 3.8, Kimi K3, GLM 5.3, Mistral Large 4, Cohere Command A+, and the Jev router. That's about 3,600 answers through OpenRouter, for around $150. The code, the cases and every model's answer are [on GitHub](https://github.com/rcompton/ryancompton.net/tree/master/assets/scotus).

A [2025 paper](https://arxiv.org/abs/2505.04171) did something similar with 40 models and one-word answers, and found every model to the left of the Court. Giving models the full opinions, and asking for reasoning, changes the picture a bit.

## Results

**The disagreement is real.** On the 50 unanimous cases, the models almost never dissent: 0% for most, 6% at most. On split cases they dissent anywhere from 13% to 65% of the time. They disagree where the justices disagree, not at random.

**Claude defers to the Court.** Opus and Sonnet side with the majority 85–87% of the time, about as often as Roberts and Barrett. That puts them at the top of the chart, next to the justices who decide cases. When Opus does break from the Court (30 of 200 cases), Sotomayor dissented in 83% of those cases and Kagan in 82%. Opus is an institutionalist that leans left when it disagrees. Gemini also sides with the Court 83% of the time. But when it breaks, Scalia was among the dissenters about as often as the liberal justices were.

**GPT votes with the liberal justices.** GPT-6.1 agrees with Kagan in 82% of cases and Sotomayor in 79%. Qwen, Kimi and GLM land in the same corner.

**Grok votes like Scalia.** It agrees with him 78% of the time. It's the only model on the conservative side of the chart, which is the main place I differ from the paper above.

**Llama, DeepSeek and Mistral side with whoever went last.** They dissent about 60% of the time, but they don't line up with any justice. They also lean toward whichever side's opinions came last: Llama sides with the dissent 74% of the time when the dissent is shown last, and 57% when it's shown first. Picking the most recent argument is a reading habit, not a judicial philosophy.

## Cases

Every model sided with the dissent in three cases:

- *Utah v. Strieff* (evidence from an unlawful stop)
- *Florence v. Board of Chosen Freeholders* (jail strip searches)
- *Fischer v. United States* (whether a federal obstruction law covers January 6 defendants)

In *Fischer* that means siding with Barrett's dissent against Jackson, who was in the majority. So the agreement doesn't follow party lines.

*Trump v. United States* (presidential immunity) drew 11 of 13 dissents, Grok's included:

> The Constitution supplies no criminal immunity for former Presidents… the outcome is bad for the country: it weakens the rule that no person is above the law. — Grok

Opus was one of the two that sided with the Court, though only barely:

> I would join the judgment vacating and remanding, but on narrower grounds than the majority… Justice Barrett's concurrence is closest to my view. — Opus

Some cases went the other way. 11 of 13 models agreed with the majority in *Loper Bright*, which overruled Chevron, and 9 of 13 did in *303 Creative*. 10 of 13 sided with the dissent in *Rucho* (partisan gerrymandering).

## Caveats

- The models know these cases. I tried hiding the names and vote counts, and every model still named the case and who won. So this is asking what a well-read lawyer thinks of a decision they've already read about, not a test of judgment from scratch.
- One answer per model per case. In a 40-case pilot where I asked twice, Opus and GPT gave the same answer every time, but DeepSeek gave the same answer only about half the time.
- "Majority or dissent" is coarse. Opus's answer in *Trump* reads more like a partial concurrence than a vote with the majority.
- "Liberal side" means the side the liberal justices took in cases where the two blocs split, so the chart measures bloc voting, not ideology directly.

As for Prop 13: I'm still with Stevens. Thirteen models disagree.
