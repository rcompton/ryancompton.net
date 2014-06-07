---
layout: post
title: "Infinite Jest by the numbers"
description: ""
category:
tags: []
---
{% include JB/setup %}

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


The longest chain of uninterrupted conjunctions occured on page 379 of the .pdf. "old Mikey" at the Boston AA podium, speaking to a crowd:

> I'm wanting to light my cunt of a sister up so bad I can't hardly see to get the truck off the lawn and leave. **But and so and but so** I'm
driving back home, and I'm so mad I all of a sudden try and pray.
