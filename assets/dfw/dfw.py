# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import nltk
import string
import re
import collections

# <codecell>

# first, run pdftotext on this:
# http://nkelber.com/engl295/wp-content/uploads/2012/07/David-Foster-Wallace-Infinite-Jest-v2.0.pdf
raw = open("David-Foster-Wallace-Infinite-Jest-v2.0.txt", "rU").read()

rec = re.compile("[^A-Za-z ]")
no_punct_lower = re.sub(rec, " ", raw).lower()

# <codecell>


def vocabulary_size(raw):
    """
    Compute the number of distinct words (stemmed)
    ignores non-ascii letters
    """
    print("chars in raw: ", len(raw))
    # remove non-ascii letters
    rec = re.compile("[^A-Za-z ]")
    no_punct_lower = re.sub(rec, " ", raw).lower()

    # tokenize, stem, and count
    tokens = nltk.word_tokenize(no_punct_lower)
    print("tokens in raw: ", len(tokens))

    stemmer = nltk.stem.PorterStemmer()
    stemmed_tokens = []
    for token in tokens:
        stemmed_tokens.append(stemmer.stem(token))
    return len(set(stemmed_tokens))


print("words in vocabulary:\t", vocabulary_size(raw))

# <codecell>

conjunctions = set(open("conjunctions.txt", "rU").read().splitlines())
print("num conjunctions in Wiktionary:", len(conjunctions))

prepositions = set(open("prepositions.txt", "rU").read().splitlines())
print("num prepositions in Wiktionary:", len(prepositions))


def all_uninterrupted_seqs(raw, prep_conj, min_seq_length=3):
    """
    Given a string of text and a set of terms to search for
    return all uninterrupted chains of the terms
    """
    tokens = nltk.wordpunct_tokenize(raw)

    all_seqs = []
    for idx, token in enumerate(tokens):
        tokl = token.lower()
        if tokl in prep_conj:
            seq = [tokl]
            n_ahead = 0
            while tokl in prep_conj:
                n_ahead += 1
                tokl = tokens[idx + n_ahead].lower()
                if tokl in prep_conj:
                    seq.append(tokl)
            if len(seq) >= min_seq_length:
                all_seqs.append(seq)
    return all_seqs


def longest_seq(seqs):
    """
    Find the longest chain in the output of all_uninterrupted_seqs
    """
    max_len = 0
    max_seq = []
    for seq in seqs:
        if len(seq) >= max_len:
            max_seq = seq
            max_len = len(max_seq)
    return max_seq


# the type of terms to search for chains of
term_set = prepositions.union(conjunctions)

minlen = 3
chains = all_uninterrupted_seqs(raw, term_set, minlen)
chainsp1 = all_uninterrupted_seqs(raw, term_set, minlen + 1)
chainsp2 = all_uninterrupted_seqs(raw, term_set, minlen + 2)

n = 10
top_conjs = collections.Counter(list(map(lambda x: " ".join(x), chains))).most_common(n)
top_conjsp1 = collections.Counter(
    list(map(lambda x: " ".join(x), chainsp1))
).most_common(n)
top_conjsp2 = collections.Counter(
    list(map(lambda x: " ".join(x), chainsp2))
).most_common(n)

# print out the longest chain
top_seq = longest_seq(chains)
print("\nlongest sequence:\t", len(top_seq), " ".join(top_seq), "\n")

for i in range(n):
    try:
        print(
            "|",
            top_conjs[i][0],
            ":|",
            top_conjs[i][1],
            "|",
            top_conjsp1[i][0],
            ":|",
            top_conjsp1[i][1],
            "|",
            top_conjsp2[i][0],
            ":|",
            top_conjsp2[i][1],
            "|",
        )
    except IndexError:
        print(
            "|",
            top_conjs[i][0],
            ":|",
            top_conjs[i][1],
            "|",
            top_conjsp1[i][0],
            ":|",
            top_conjsp1[i][1],
            "|",
            " ",
            "|",
            " ",
            "|",
        )

# <codecell>


def acronyms(raw):
    rec = re.compile("[^A-Z\.]")
    caps = re.sub(rec, " ", raw)
    toks = nltk.tokenize.word_tokenize(caps)
    acks = filter(lambda x: ("." in x) and re.search("[A-Z]", x) and len(x) > 8, toks)
    return collections.Counter(acks)


acks = acronyms(raw)

top_acks = acks.most_common(20)
for i in range(20):
    print("|", top_acks[i][0], ":|", top_acks[i][1], "")

# <codecell>

max_ack = ""
for ack in set(acks):
    if len(ack) > len(max_ack):
        max_ack = ack
        print(max_ack)

# <codecell>

brwn = nltk.corpus.brown.raw()[:3204159]
print("words in brown corpus:\t", vocabulary_size(brwn))

# <codecell>

# bigram_measures = nltk.collocations.BigramAssocMeasures()
# finder = nltk.collocations.BigramCollocationFinder.from_words(raw)
# list(filter(lambda x: max(len(x[0]),len(x[1]))>2,finder.nbest(bigram_measures.pmi, 300000)))
