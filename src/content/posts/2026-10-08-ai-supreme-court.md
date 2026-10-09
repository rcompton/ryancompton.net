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

![For each model, how often it votes with the liberal justices on the law, and how often it prefers the liberal outcome](/assets/scotus/law_vs_policy.svg)

<!--more-->

## Setup

I picked 200 random split decisions, almost all from 2010–2025. Each model got the case name, the vote count, the facts, the question presented, and the full text of every opinion. There's no point in hiding the outcome; they've all read about these cases before. I asked three things:

1. Whose reading of the law is correct, the majority's or the dissent's?
2. Which single opinion is closest to your view?
3. Separately from the law, was the outcome good or bad for the country?

The models were Claude Opus 5.5 and Sonnet 5.5, GPT-6.1, Gemini 3.8 Flash, Grok 4.7, Llama 4 Maverick, DeepSeek v4, Qwen 3.8, Kimi K3, GLM 5.3, Mistral Large 4, Cohere Command A+, and the Jev router. That's about 3,600 answers through OpenRouter, for around $150. The code, the cases and every answer are [on GitHub](https://github.com/rcompton/ryancompton.net/tree/master/assets/scotus).

## The law to the right of the politics

In 160 of the cases the liberal and conservative justices took opposite sides. For each model I counted how often it voted with the liberal justices on the law (question 1), and how often it said the liberal side's result was better for the country (question 3).

All 13 models land further left on outcomes than on law, by 7 to 24 points. When the two answers disagree, it's almost always "the conservative reading of the law is right, but the liberal result would be better": 426 answers go that way and 41 go the other.

It isn't just deference to the Court. In 161 of those 426 answers the model sided with a *conservative dissent* against a liberal majority, while saying it liked the majority's result. And it isn't a handful of cases: it shows up in 119 of the 160.

The models say so in plain terms. Here's Opus on *Garland v. Cargill*, which struck down the bump stock ban:

> On practical consequences I judge the result unfortunate, even though I believe it was legally compelled.

And Sonnet on *Johnson v. Guzman Chavez*, which held that some detained immigrants don't get bond hearings:

> Congress drew the line, though… I lean slightly toward "bad" on policy grounds, because individualized bond hearings for people with credible fear claims seem sensible and low-cost.

## Is that how justices behave?

It's how they say they behave. "I'd oppose this as a legislator, but the Constitution allows it" is the textbook ideal of judicial restraint. Thomas called the Texas sodomy law in *Lawrence* "uncommonly silly" and wrote that he'd vote to repeal it, then dissented anyway. Scalia said he'd jail "every sandal-wearing, scruffy-bearded weirdo who burns the American flag. But I am not king."

But political scientists have found for decades that justices' votes mostly track their policy preferences. The famous law-over-policy quotes are famous because they're rare, and they go in both directions: Thomas's split runs one way, Scalia's the other. The models split law from policy in 9–27% of their answers, and almost always in the same direction. They seem to have absorbed the restraint ideal and apply it more consistently than the justices do.

## Where they sit

On the law alone, every model lands left of the Court's center, as [an earlier paper](https://arxiv.org/abs/2505.04171) also found. Even Grok, which votes most like Scalia, ends up just left of Roberts, Barrett and Kavanaugh.

![Models and justices: share of votes with the conservative side, and how often each sides with the Court's majority](/assets/scotus/positions.svg)

A few other things showed up:

- The Claude models side with the Court's majority 85–87% of the time, as often as Roberts and Barrett. When Opus does break from the Court, Sotomayor and Kagan were among the dissenters over 80% of the time.
- GPT-6.1 votes with Kagan and Sotomayor about 80% of the time.
- Llama, DeepSeek and Mistral tend to side with whichever opinion they read last.
- All 13 models sided with the dissent in *Utah v. Strieff*, *Florence v. Board of Chosen Freeholders* and *Fischer v. United States*.

## Caveats

- One answer per model per case.
- "Liberal side" is defined by which side the liberal justices took, not by any judgment of the issues.
- Question 3 told the models their policy answer "does not need to match your legal view." That may raise how often they split, but it can't explain why the splits almost all go one way.
- There's no matching measurement for the justices, since nobody asked them whether each outcome was good for the country.

As for Prop 13: the models and I agree it's bad policy. Where we differ is that I'm with Stevens, who thought a bad enough result should change how you read the law. The models almost never let it.
