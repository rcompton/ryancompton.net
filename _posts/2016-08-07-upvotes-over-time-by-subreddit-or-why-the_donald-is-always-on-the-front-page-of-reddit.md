---
layout: post
title: "Upvotes over time by subreddit or: Why /r/The_Donald is always on the front page of reddit"
description: ""
category:
tags: ["coding"]
---

{% include JB/setup %}

{% excerpt %}

Here's a plot of the cumulative number of upvotes per minute for submissions to a few major subreddits:

![avg-votes]({{ site.url }}/assets/reddit_scrape/ups_per_subreddit.jpg)

The data was collected by polling `/new/` every 2 minutes for each subreddit over the paste 3 days (2942138 records were found). The vast majority of submissions to reddit never get anywhere - I removed submissions which never attained over 50 upvotes which left me with 154160 records. The raw data is shown below:

{% endexcerpt %}

![avg-votes]({{ site.url }}/assets/reddit_scrape/ups_per_subreddit.jpg)

Ranking on reddit is determined using a combination of upvotes, downvotes, and the age of the post at the time of each vote (cf. [here](https://medium.com/hacking-and-gonzo/how-reddit-ranking-algorithms-work-ef111e33d0d9#.2t9s2cn3k), [here](http://scienceblogs.com/builtonfacts/2013/01/16/the-mathematics-of-reddit-rankings-or-how-upvotes-are-time-travel/), and [here](https://web.archive.org/web/20160407110929/http://www.redditblog.com/2009/10/reddits-new-comment-sorting-system.html) for some good explanations). In short, the ranking of a submission is determined by the rating function
$$
f(n,t) = 45000\log_{10}(n) + t
where $n$ is the difference between upvotes and downvotes and $t$ is the number of seconds which elapsed between the post's creation time and 7:46:43 am December 8th, 2005. More recent posts have a larger $t$ which translates to a better ranking. Additionally, due to the shape of $\log_{10}$, votes matter substantially more when the number of upvotes nearly equals the number of downvotes (eg. when the post is brand new). Thus, the best way to get your post to the front page is to upvote aggressively when the post is very young. My data suggests that members of [/r/The_Donald](https://www.reddit.com/r/The_Donald/comments/4oo3up/the_new_algorithm_is_a_totally_impartial_and_fair/) are aware of this which explains why their posts have so many more upvotes on new posts despite the fact that competing subreddits in the plot are several orders of magnitude larger.
