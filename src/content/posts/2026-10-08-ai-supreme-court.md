---
title: "AI models read the law to the right of their politics"
description: "13 language models read the full opinions in 200 split Supreme Court cases. Every one reads the law more conservatively than the outcomes it says it wants."
tags: ["politics", "llm"]
image: "/assets/scotus/law_vs_policy.svg"
---

Like any clear-thinking level-headed individual I have strong opinions about various Supreme Court rulings. For example, I think *Nordlinger v. Hahn*, the 1992 case that upheld California's Prop 13, was wrongly decided, and I agree with [Justice Stevens's lone dissent](https://www.law.cornell.edu/supct/html/90-1912.ZD.html). I don't care if it was 8-1, the court was wrong and Clarence Thomas should be disbarred.

Anyway, since AI is smart now I was wondering if it agrees with me on this. I gave 13 of them the case, with the facts and the full text of every opinion, and asked how they'd vote.

All 13 agreed with the court. Every one also said it was bad policy. So much for that.

It turns out that's a pattern. Across 200 Supreme Court cases, every model reads the law more conservatively than the outcomes it says it wants.

![Every answer from all 13 models, by reading of the law and preferred result: 1,366 liberal on both, 569 conservative on both, 420 conservative on the law but preferring the liberal result, 41 the reverse](/assets/scotus/law_vs_policy.svg)

Every answer from all 13 models, on the 159 cases where the liberal and conservative justices took opposite sides. "Liberal" means the side the liberal justices took. Usually a model's reading of the law and its preferred result line up. When they don't, it's 420 to 41.

<!--more-->

## Setup

I picked 200 random split decisions, mostly from 2010–2025. Each model got the facts, the question presented, the vote, and the full text of every opinion. They already know these cases, so there was no point hiding the outcome. I asked:

1. Whose reading of the law is correct, the majority's or the dissent's?
2. Which single opinion is closest to your view?
3. Separately from the law, was the outcome good or bad for the country?

The models were Claude Opus 5.5 and Sonnet 5.5, GPT-6.1, Gemini 3.8 Flash, Grok 4.7, Llama 4 Maverick, DeepSeek v4, Qwen 3.8, Kimi K3, GLM 5.3, Mistral Large 4, Cohere Command A+, and the Jev router. About 3,600 answers through OpenRouter cost around $150. The code, cases and answers are [on GitHub](https://github.com/rcompton/ryancompton.net/tree/master/assets/scotus).

## The law to the right of the politics

When a model's two answers disagree, it's almost always "the conservative reading of the law is right, but the liberal result is better." All 13 models lean that way individually, and it shows up in 118 of the 159 cases.

Part of this is deference. In 259 of the 420, the model agreed with a conservative majority on the law and disliked the result, which is what you'd expect from a model that defers to the Court and leans left on policy. But in the other 161, it sided with a conservative dissent *against* the Court while preferring the liberal majority's result. Deference doesn't explain those.

Opus on *Garland v. Cargill*, which struck down the bump stock ban:

> On practical consequences I judge the result unfortunate, even though I believe it was legally compelled.

Sonnet on *Johnson v. Guzman Chavez*, which denied bond hearings to some detained immigrants:

> Congress drew the line, though… I lean slightly toward "bad" on policy grounds, because individualized bond hearings for people with credible fear claims seem sensible and low-cost.

## Is that how justices behave?

It's how they say they behave. Thomas called the Texas sodomy law in *Lawrence* "uncommonly silly" and dissented anyway. Scalia said he'd jail "every sandal-wearing, scruffy-bearded weirdo who burns the American flag. But I am not king."

But political scientists have long found that justices mostly vote their policy preferences. Those quotes are famous because they're rare, and they point in opposite directions. The models make this split in about one answer in six, and almost never the reverse. They seem to have learned the ideal of judicial restraint and apply it more consistently than the justices do.

## Where they sit

On the law alone, every model lands left of the Court's center, as [an earlier paper](https://arxiv.org/abs/2505.04171) also found. Even Grok, the most conservative model, is just left of Roberts, Barrett and Kavanaugh.

![Models and justices: share of votes with the conservative side, and how often each sides with the Court's majority](/assets/scotus/positions.svg)

Blue dots are models, hollow circles are justices. Higher means siding with the Court's majority more often.

- The Claude models side with the majority 85–87% of the time, like Roberts and Barrett. When Opus breaks from the Court, Sotomayor and Kagan were among the dissenters over 80% of the time.
- GPT-6.1 votes with Kagan and Sotomayor about 80% of the time.
- Llama, DeepSeek and Mistral tend to side with whichever opinion they read last.
- All 13 sided with the dissent in *Utah v. Strieff*, *Florence v. Board of Chosen Freeholders* and *Fischer v. United States*.

## Caveats

- One answer per model per case, or two for the 40 cases from the pilot run.
- "Liberal side" means whichever side the liberal justices took.
- Question 3 told the models their policy answer "does not need to match your legal view." That may raise how often they split, but not which way.
- Nobody asked the justices whether each outcome was good for the country, so there's no direct comparison.

As for Prop 13: the models and I agree it's bad policy. Where we differ is that I'm with Stevens, who thought a bad enough result should change how you read the law. The models almost never let it.
