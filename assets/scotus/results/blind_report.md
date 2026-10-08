# Blind vs labeled

127 blind answers, 847 labeled answers.

## Agreement with the Court's majority

Labeled: case name, vote count, and opinions labeled majority/dissent with authors. Blind: none of those; opinions grouped as Side A / Side B at random. Same cases in both columns (cases the model answered in both runs).

| model | labeled | blind | change (points) |
|---|---|---|---|
| opus-5.5 | 96% (26) | 100% (19) | +4 |
| sonnet-5.5 | 87% (69) | 92% (37) | +5 |
| gpt-6.1-sol | 64% (36) | 79% (24) | +15 |
| gemini-3.8-flash | 78% (58) | 100% (34) | +22 |
| grok-4.7 | 35% (20) | 69% (13) | +34 |

## Does the model recognize the case?

From the blind run. 'Recalls winner' = the model named the side the Court actually ruled for. The last two columns split agreement with the Court by whether it recalled the winner.

| model | names the case | recalls winner | agrees w/ Court | recalls | agrees w/ Court | doesn't |
|---|---|---|---|---|
| opus-5.5 | 100% | 100% | 100% (19) | – (0) |
| sonnet-5.5 | 100% | 100% | 92% (37) | – (0) |
| gpt-6.1-sol | 100% | 100% | 79% (24) | – (0) |
| gemini-3.8-flash | 100% | 100% | 100% (34) | – (0) |
| grok-4.7 | 100% | 100% | 69% (13) | – (0) |

## Position effect (blind run)

Side A is always shown first; which side is the majority is random. 50% means no position bias.

| model | picks Side A |
|---|---|
| opus-5.5 | 58% (19) |
| sonnet-5.5 | 68% (37) |
| gpt-6.1-sol | 46% (24) |
| gemini-3.8-flash | 68% (34) |
| grok-4.7 | 62% (13) |

## Siding with the government

30 cases where a government or official faced a private party (the Court sided with the government in 12). Share of answers siding with the government.

| model | labeled | blind |
|---|---|---|
| opus-5.5 | 38% (39) | 31% (16) |
| sonnet-5.5 | 34% (56) | 33% (27) |
| gpt-6.1-sol | 14% (44) | 20% (20) |
| gemini-3.8-flash | 28% (47) | 38% (24) |
| grok-4.7 | 58% (43) | 50% (12) |
| llama-4-maverick | 40% (60) | – |
| deepseek-v4-pro | 44% (57) | – |
| qwen3.8-max | 28% (57) | – |
| kimi-k3 | 26% (47) | – |
| glm-5.3 | 26% (42) | – |
| mistral-large-4 | 18% (50) | – |
| command-a-plus | 51% (43) | – |
| jev-router | 28% (57) | – |

Real justices, same cases: Thomas 77%, Alito 76%, Scalia 71%, Roberts 60%, Kavanaugh 54%, Kennedy 41%, Gorsuch 40%, Ginsburg 30%, Kagan 24%, Breyer 21%, Sotomayor 17%
