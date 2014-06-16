---
layout: post
title: "Infinite Jest by the numbers"
description: ""
category:
tags: ["books", "coding"]
---
{% include JB/setup %}

{% excerpt %}
After stressing my reading comprehension over the past eight months I've finally finished David Foster Wallace's Infinite Jest. The writing is, in a word, impressive. Wallace's command of the English language allows him to do things that I've never seen before. In this post I'll try to quantify a few of the stylistic features that I think really stood out.

First off, to run these experiments, one needs an electronic version of the book. It turns out that these are remarkably easy to find online. I ran the .pdf [here](http://nkelber.com/engl295/blog/2012/07/03/playing-with-infinite-jests-corpus-exploring-tradition-literature-electronically/) through [pdftotext](https://en.wikipedia.org/wiki/Pdftotext), imported [nltk](http://www.nltk.org), and got these results:

###*"But and so and but so" is the longest uninterrupted chain of conjunctions*{: style="color: white"}

In Infinite Jest conjunctions often appear in chains of length three or greater. There is a length-six chain on page 379 of the .pdf. It's due to a minor character, "old Mikey", standing at the Boston AA podium and speaking to a crowd:

> *I'm wanting to light my cunt of a sister up so bad I can't hardly see to get the truck off the lawn and leave. But and so and but so I'm
driving back home, and I'm so mad I all of a sudden try and pray.*

Now, according to Wiktionary, there are [224 conjunctions in the English language](https://en.wiktionary.org/wiki/Category:English_conjunctions). It's possible to quickly get all of them by entering this query into [DBpedia's public Wiktionary endpoint](http://wiktionary.dbpedia.org/sparql):

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

With this list we can find the most common uninterrupted conjunction chains along with the number of times they appeared in the text:

| Conjunction Triples |  | Conjunction Quadruples |  | Conjunction Quintuples |  |
|-:|:-|-:|:-|-:|:-|
| and / or :| 23 | not until then that :| 1 | but so but then so :| 1 |
| whether or not :| 9 | so and but that :| 1 | and not only that but :| 1 |
| and then but :| 8 | not only that but :| 1 | and so and but so :| 1 |
| and but so :| 6 | so then but so :| 1 |  |  |
| and then when :| 6 | but so but then :| 1 |   |   |
| and that if :| 5 | and where and when :| 1 |   |   |
| and then only :| 5 | and but then when :| 1 |   |   |
| and but then :| 5 | and but so why :| 1 |   |   |
| and then if :| 5 | and so but since :| 1 |   |   |
| if and when :| 5 | but not until after :| 1 |   |   |

(Remark: according to Wiktionary, "/" is a valid conjunction)
{% endexcerpt %}

The only length six chain is "But and so and but so".

We can perform a similar experiment using prepositions, of which there are [496](https://en.wiktionary.org/wiki/Category:English_prepositions). Here, we discover the longest chain of uninterrupted prepositions is "in over from behind like". This occurs on page 402, while Michael Pemulis is opening Hal's door:

> *With the door just cracked and his head poked in he brings his other arm in over from behind like it's not his arm, his hand in the shape of a claw just over his head, and makes as if the claw from behind is pulling him back out into the hall. W/ an eye-rolling look of fake terror.*

Here's the corresponding frequency table for prepositions:

| Preposition Triples |  | Preposition Quadruples |  | Preposition Quintuples |  |
|-:|:-|-:|:-|-:|:-|
| up next to :| 24 | to come out of :| 2 | in over from behind like :| 1 |
| up out of :| 14 | to come in to :| 2 |   |   |
| as in like :| 13 | to come up to :| 1 |   |   |
| come out of :| 9 | around with down in :| 1 |   |   |
| to come to :| 8 | to come up with :| 1 |   |   |
| come up with :| 7 | in over from behind like :| 1 |   |   |
| out from under :| 6 | come out of on :| 1 |   |   |
| come in to :| 6 | in from out over :| 1 |   |   |
| come in for :| 5 | as in with like :| 1 |   |   |
| to come in :| 5 | over from behind like :| 1 |   |   |

<br>

The longest uninterrupted chain composed entirely of either prepositions or conjunctions is "again/And again and again/And again and again and again". It occurs on page 264, during a storytelling session in the Tunnel Club:

>*Peterson to Traub, while Gopnik holds the light: 'Eighteen-year-old top-ranked John Wayne / Had sex with Herr Schtitt on a train / They had sex again/And again and again/And again and again and again,' which the slightly older kids find more entertaining than Traub does.*

And here's the frequency table for chains of either prepositions or conjunctions:

| Either Triples |  | Either Quadruples |  | Either Quintuples |  |
|-:|:-|-:|:-|-:|:-|
| and out of :| 41 | in and out of :| 30 | and so on and so :| 9 |
| and so on :| 39 | so on and so :| 11 | on out and over to :| 1 |
| up and down :| 32 | and so on and so :| 9 | up and out and down and :| 1 |
| in and out of :| 30 | over and over again :| 6 | and up and down through :| 1 |
| over and over :| 28 | up and down in :| 4 | and down over and over for :| 1 |
| up next to :| 24 | to come in and :| 4 | but so but then so :| 1 |
| and / or :| 22 | come and gone and :| 3 | as in like not to :| 1 |
| on and on :| 15 | over and over and :| 3 | only that at times like :| 1 |
| up out of :| 14 | over and over for :| 3 | not to come down or :| 1 |
| as in like :| 12 | up and down both :| 3 | about wanting to and so on :| 1 |

<br>

If we toss out "/" from our word list the longest chain of either is "up and down over and over for". Not surprisingly, it's due to Michael Pemulis (page 403):

>*Tell him we read books and tirelessly access D-bases and run our asses off all day here and need to eat instead of we don't just stand there and swing one leg up and down over and over for seven-plus figures.*

For reference, here's the code to identify the longest uninterrupted chains of conjunctions/prepositions:
{% highlight python %}
def all_uninterrupted_seqs(raw, prep_conj, min_seq_length=3):
    """
    Given a string of text and a set of terms to search for
    return all uninterrupted chains of the terms
    """
    tokens = nltk.wordpunct_tokenize(raw)
    all_seqs = []
    for idx,token in enumerate(tokens):
        tokl = token.lower()
        if tokl in prep_conj:
            seq = [tokl]
            n_ahead = 0
            while tokl in prep_conj:
                n_ahead += 1
                tokl = tokens[idx+n_ahead].lower()
                if tokl in prep_conj:
                    seq.append(tokl)
            if len(seq) >= min_seq_length:
                all_seqs.append(seq)
    return all_seqs
{% endhighlight %}

***

Our next result:

###*Wallace used a vocabulary of 20,584 words to write Infinite Jest*{: style="color: white"}

By comparison, the [Brown Corpus](https://en.wikipedia.org/wiki/Brown_Corpus), which is roughly three times longer than Infinite Jest, contains only 26,126 unique words. To be precise, the Brown Corpus contains 9,964,284 characters and 2,074,513 (not necessarily unique) words, while Infinite Jest contains 3,204,159 characters and 577,608 words. If we restrict the Brown Corpus to its first 3,204,159 characters we find a vocabulary of only 15,771 unique words.

If we restrict to the first 35,000 words, Infinite Jest contains 4,923 unique words ([more than most rappers, but still less than the Wu-Tang clan](http://rappers.mdaniels.com.s3-website-us-east-1.amazonaws.com/)) while the Brown Corpus contains 2,708.

One issue with measuring vocabulary size is that suffixes may artificially inflate the number of distinct words in the set (e.g. fantod and fantods should not count as two words). To mitigate this, I used the
Porter [Stemming](https://en.wikipedia.org/wiki/Stemming) algorithm to first remove suffixes for every word in the text before counting uniques. I also removed all characters which were not ascii letters (e.g. digits).

Here's the code:
{% highlight python %}
def vocabulary_size(raw):
    """
    Compute the number of distinct words (stemmed)
    """
    #remove non-ascii letters and capitalization
    rec = re.compile('[^A-Za-z ]')
    no_punct_lower = re.sub(rec,' ',raw).lower()

    #tokenize, stem, and count
    tokens = nltk.word_tokenize(no_punct_lower)
    stemmer = nltk.stem.PorterStemmer()
    stemmed_tokens = map(lambda x: stemmer.stem(x), tokens)
    return len(set(stemmed_tokens))
{% endhighlight %}

***

Finally,

###*The longest acronyms are O.N.A.N.D.E.A. and O.N.A.N.C.A.A.*{: style="color: white"}

These are used to abbreviate institutions within the Organization of North American Nations (O.N.A.N.): the Drug Enforcement Organization (D.E.A.) and the Commonwealth Academy Association (C.A.A).

O.N.A.N.D.E.A appears in footnote 12a. on page 388:

>*Following the Continental Controlled Substance Act of Y.T.M.P., O.N.A.N.D.E.A.'s hierarchy of analgesics/antipyretics/anxiolytics establishes drug-classes of Category-II through Category-VI, with C-II's (e.g. Dilaudid, Demerol) being judged the heaviest w/r/t dependence and possible abuse*

If we allow a "/" in a acronym, the longest becomes "N./O.N.A.N.C.A.A.":

>*Orin had exited his own substance-phase about the time he discovered sex, plus of course the N./O.N.A.N.C.A.A.-urine considerations, and he declined it, the cocaine, but not in a judgmental or killjoy way, and found he liked being with his P.G.O.A.T. straight while she ingested, he found it exciting, a vicariously on-the-edge feeling he associated with giving yourself not to any one game's definition but to yourself and how you unjudgmentally feel about somebody who's high and feeling even freer and better than normal, with you, alone, under the red balls.*

Table of the most common long acronyms (length 5 or greater):

| Acronym :| Number of Occurrences |
|-:|:-|
| O.N.A.N.T.A. :| 31
| P.G.O.A.T. :| 13
| U.S.O.U.S. :| 11
| E.M.P.H.H. :| 11
| U.S.S.M.K. :| 7
| O.N.A.N.C.A.A. :| 5
| U.S.B.S.S. :| 3
| Y.T.S.D.B. :| 2
| Y.D.P.A.H. :| 2
| ESCHAX.DIR. :| 1
| A.A.O.A.A. :| 1
| O.N.A.N.F.L. :| 1
| Y.W.Q.M.D. :| 1
| O.N.A.N.M.A. :| 1
| F.O.P.P.P. :| 1
| N.A.A.U.P. :| 1
| O.N.A.N.D.E.A. :| 1
| B.A.M.E.S. :| 1
| I.B.P.W.D.W. :| 1

<br>

And the code used to find them:
{% highlight python %}
def acronyms(raw):
    rec = re.compile('[^A-Z\.]')
    caps = re.sub(rec,' ',raw)
    toks = nltk.tokenize.word_tokenize(caps)
    acks = filter(lambda x:('.' in x) and re.search('[A-Z]',x), toks)
    return collections.Counter(acks)
{% endhighlight %}

The complete code for all experiments is available here: <https://github.com/rcompton/ryancompton.net/blob/master/assets/dfw/dfw.py>
