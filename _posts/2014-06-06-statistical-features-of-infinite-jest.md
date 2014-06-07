---
layout: post
title: "Infinite Jest by the numbers"
description: ""
category:
tags: []
---
{% include JB/setup %}

After stressing my reading comprehension for eight months I've finally finished David Foster Wallace's Infinite Jest. The writing is, in a word, impressive. Wallace's command of the English language allows him to do things that I've never seen before. In this post I'll try to quantify some stylistic features that really stood out to me. It turns out that Infinite Jest .pdfs are easy to find online. To perform this study, I ran [this one](http://nkelber.com/engl295/wp-content/uploads/2012/07/David-Foster-Wallace-Infinite-Jest-v2.0.pdf) through [pdftotext](https://en.wikipedia.org/wiki/Pdftotext) and went at it with [nltk](http://www.nltk.org).

### "But and so and but so" is the longest uninterrupted chain of conjunctions.

Page 379 of the .pdf: "old Mikey" at the Boston AA podium, speaking to a crowd

> I'm wanting to light my cunt of a sister up so bad I can't hardly see to get the truck off the lawn and leave. **But and so and but so** I'm
driving back home, and I'm so mad I all of a sudden try and pray.


{% highlight python %}
def vocabulary_size(raw):
    """
    Compute the number of distinct words (stemmed)
    ignores non-ascii letters
    """
    #remove non-ascii letters
    rec = re.compile('[^A-Za-z ]')
    no_punct_lower = re.sub(rec,' ',raw).lower()

    #tokenize, stem, and count
    tokens=nltk.word_tokenize(no_punct_lower)
    stemmer = nltk.stem.PorterStemmer()
    stemmed_tokens = []
    for token in tokens:
        stemmed_tokens.append(stemmer.stem(token))
    return len(set(stemmed_tokens))

print("words in vocabulary:\t",vocabulary_size(raw))
{% endhighlight %}

words in vocabulary:	 20584

>With the door just cracked and his head poked in he brings his other arm **in over from behind like** it's not his arm, his hand in the shape of a claw just over his head, and makes as if the claw from behind is pulling him back out into the hall. W/ an eye-rolling look of fake terror.

Pemulis p 402

>Tell him we read books and tirelessly access D-bases and run our asses off all day here and need to eat instead of we don't just stand there and swing one leg **up and down over and over for** seven-plus figures.

Pemulis p 403


>Peterson to Traub, while Gopnik holds the light: 'Eighteen-year-old top-ranked John Wayne / Had sex with Herr Schtitt on a
train / They had sex **again/And again and again/And again and again and again**,' which the slightly older kids find more
entertaining than Traub does.

p 264 storytelling in the Tunnel Club


and / or 	 23
whether or not 	 9
and then but 	 8
and but so 	 6
and then when 	 6
and then if 	 5
and that if 	 5
and but then 	 5
if and when 	 5
and then only 	 5


up next to 	 24
up out of 	 14
as in like 	 13
come out of 	 9
to come to 	 8
come up with 	 7
out from under 	 6
come in to 	 6
come in for 	 5
to come in 	 5


and out of 	 41
and so on 	 39
up and down 	 32
in and out of 	 30
over and over 	 28
up next to 	 24
and / or 	 22
on and on 	 15
up out of 	 14
as in like 	 12






{% highlight SQL %}
PREFIX terms:<http://wiktionary.dbpedia.org/terms/>
PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:<http://purl.org/dc/elements/1.1/>
SELECT DISTINCT(?label)
WHERE {
  ?x terms:hasPoS terms:Conjunction .
  ?x dc:language terms:English .
  ?x rdfs:label ?label .
}
{% endhighlight %}


