---
layout: post
title: "Url extraction in python"
description: ""
category:
tags: ["coding"]
---
{% include JB/setup %}

I was looking for a way to identify urls in text and eventually found this huge regex <http://daringfireball.net/2010/07/improved_regex_for_matching_urls> . I figured I'll need to do this again so I stuck all that into [urlmaker.py](https://github.com/rcompton/ryancompton.net/blob/master/assets/praw_drugs/urlmarker.py) so now when I need it I can just import it, eg.

{% highlight python %}
import urlmarker
import re

text = """
The regex patterns in this gist are intended only to match web URLs -- http,
https, and naked domains like "example.com". For a pattern that attempts to
match all URLs, regardless of protocol, see: https://gist.github.com/gruber/249502
"""

print(re.findall(urlmarker.WEB_URL_REGEX,text))
{% endhighlight %}
will show `['example.com', 'https://gist.github.com/gruber/249502']`
