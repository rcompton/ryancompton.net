---
layout: post
title: "New Paper: Geotagging One Hundred Million Twitter Accounts with Total Variation Minimization"
description: ""
category:
tags: ["papers"]
---
{% include JB/setup %}

Recently published a paper on the arxiv: [http://arxiv.org/abs/1404.7152](http://arxiv.org/abs/1404.7152),  and it made [Tech Review juinor varisty!](http://www.technologyreview.com/view/527246/other-interesting-arxiv-papers-week-ending-may-10-2014/) Here's the abstract:

Geographically annotated social media is extremely valuable for modern information retrieval. However, when researchers can only access publicly-visible data, one quickly finds that social media users rarely publish location information. In this work, we provide a method which can geolocate the overwhelming majority of active Twitter users, independent of their location sharing preferences, using only publicly-visible Twitter data.

Our method infers an unknown user's location by examining their friend's locations. We frame the geotagging problem as an optimization over a social network with a total variation-based objective and provide a scalable and distributed algorithm for its solution. Furthermore, we show how a robust estimate of the geographic dispersion of each user's ego network can be used as a per-user accuracy measure, allowing us to discard poor location inferences and control the overall error of our approach.

Leave-many-out evaluation shows that our method is able to infer location for 101,846,236 Twitter users at a median error of 6.33 km, allowing us to geotag roughly 89% of public tweets.
