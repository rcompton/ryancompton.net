---
title: "Which Supreme Court Justice is your chatbot?"
description: "13 language models read the full opinions in 250 Supreme Court cases and voted. Claude sides with the Court, GPT votes with Sotomayor, and Grok votes like Scalia."
tags: ["politics", "llm"]
image: "/assets/scotus/positions.svg"
---

Like any clear-thinking level-headed individual I have strong opinions about various Supreme Court rulings. For example, I think *Nordlinger v. Hahn*, the 1992 case that upheld California's Prop 13, was wrongly decided, and I agree with [Justice Stevens's lone dissent](https://www.law.cornell.edu/supct/html/90-1912.ZD.html). I don't care if it was 8-1, the court was wrong and Clarence Thomas should be disbarred.

Anyway, since AI is smart now I was wondering if it agrees with me on this. I gave 13 of them the case, with the facts and the full text of every opinion, and asked how they'd vote.

All 13 agreed with the court. Every one also said it was bad policy. So much for that.

Ok but how do models vote on Supreme Court cases in general, and which justices do they vote like?

![Models and justices by ideology and agreement with the Court](/assets/scotus/positions.svg)

<!--more-->

## Setup

I picked 200 random split decisions and 50 unanimous ones, almost all from 2010–2025. Each model got the case name, the vote count, the facts, the question presented, and the full text of every opinion: majority, concurrences and dissents. There's no point in trying to hide the outcome they've all read about these cases before. I asked each model three things:

1. Whose reading of the law is correct, the majority's or the dissent's?
2. Which single opinion is closest to your view?
3. Separately from the law, was the outcome good or bad for the country?

The models were Claude Opus 5.5 and Sonnet 5.5, GPT-6.1, Gemini 3.8 Flash, Grok 4.7, Llama 4 Maverick, DeepSeek v4, Qwen 3.8, Kimi K3, GLM 5.3, Mistral Large 4, Cohere Command A+, and the Jev router. That's about 3,600 answers through OpenRouter, for around $150. The code, the cases and every model's answer are [on GitHub](https://github.com/rcompton/ryancompton.net/tree/master/assets/scotus).

A [2025 paper](https://arxiv.org/abs/2505.04171) did something similar at a larger scale. It had 43 models rule on about 1,750 cases, answering just "Side A" or "Side B," and found every model to the left of the Court's Roberts/Kennedy center. My results agree. What the full opinions add is the reasoning, and how often each model defers to the Court.

## Results

**The models disagree.** On the 50 unanimous cases, the models almost never dissent: 0% for most, 6% at most. On split cases they dissent anywhere from 13% to 65% of the time.

**Claude defers to the Court.** Opus and Sonnet side with the majority 85–87% of the time, about as often as Roberts and Barrett. When Opus does break from the Court (30 of 200 cases), Sotomayor dissented in 83% of those cases and Kagan in 82%. Opus is an institutionalist that leans left when it disagrees.

**GPT votes with the liberal justices.** GPT-6.1 agrees with Kagan in 82% of cases and Sotomayor in 79%. Qwen, Kimi and GLM land in the same corner.

**Grok votes like Scalia.** It agrees with him 78% of the time, and it's the only model on the conservative half of the chart. Even so, it lands just to the left of Roberts, Barrett and Kavanaugh, as the paper found for every model.

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
