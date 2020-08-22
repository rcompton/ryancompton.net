---
layout: post
title: "Paper update: Geotagging One Hundred Million Twitter Accounts with Total Variation Minimization"
description: ""
category:
tags: ["papers"]
redirect_from:
  - /2015-03-05-paper-update-geotagging-one-hundred-million-twitter-accounts-with-total-variation-minimization.md
---


***

### *Press coverage (updated 2015-05-02):*{: style="color: white"}

+ [Forbes](http://www.forbes.com/sites/thomasbrewster/2015/03/07/twitter-location-can-be-determined-through-friends/)
+ [Business Insider](http://www.businessinsider.com/twitter-location-research-at-mentions-cornell-2015-3)
+ [New York Observer](http://observer.com/2015/03/you-dont-have-to-geotag-your-tweets-to-give-away-your-location/)
+ [Schneier on Security](https://www.schneier.com/blog/archives/2015/03/geotagging_twit.html)
+ [Daily Caller](http://dailycaller.com/2015/03/06/how-your-tweets-can-reveal-your-real-location/)
+ [Komando](http://www.komando.com/happening-now/299085/forget-gps-hackers-can-pinpoint-your-exact-location-using-social-media/all)
+ [UCLA math website](https://www.math.ucla.edu/news/recent-ucla-math-grads-research-makes-news)
+ [MIT Tech Review junior varsity](http://www.technologyreview.com/view/527246/other-interesting-arxiv-papers-week-ending-may-10-2014/)
+ [Serene Risc Quarterly Digest](http://ryancompton.net/assets/resume/Serene_Risc_Digest_2015_Spring.pdf)

[Altmetrics link](https://www.altmetric.com/details/2314147)


***

Earlier this week I updated a paper on the arxiv: [http://arxiv.org/abs/1404.7152](http://arxiv.org/abs/1404.7152). The paper appeared a few months ago at [IEEE BigData 2014](http://cci.drexel.edu/bigdata/bigdata2014/) and was the subject of [all](http://papyrus.math.ucla.edu/seminars/display.php?&id=831425
) [my](http://calendar.ics.uci.edu/event.php?calendar=1&category=&event=1386&date=2015-01-16) [talks](http://wwwcontent.cs.ucr.edu/department/eventlookup/491
) [last](http://myweb.lmu.edu/yma/LMUMathSeminar.htm
) [year](http://web.csulb.edu/depts/math/?q=node/36
).  This update syncs the arxiv paper with what was accepted for the conference. Here's the abstract:

Geographically annotated social media is extremely valuable for modern information retrieval. However, when researchers can only access publicly-visible data, one quickly finds that social media users rarely publish location information. In this work, we provide a method which can geolocate the overwhelming majority of active Twitter users, independent of their location sharing preferences, using only publicly-visible Twitter data.

Our method infers an unknown user's location by examining their friend's locations. We frame the geotagging problem as an optimization over a social network with a total variation-based objective and provide a scalable and distributed algorithm for its solution. Furthermore, we show how a robust estimate of the geographic dispersion of each user's ego network can be used as a per-user accuracy measure which is effective at removing outlying errors.

Leave-many-out evaluation shows that our method is able to infer location for 101,846,236 Twitter users at a median error of 6.38 km, allowing us to geotag over 80% of public tweets.
