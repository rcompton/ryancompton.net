# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import pandas as pd
import numpy as np
import sklearn
import nltk
import sqlalchemy
import sqlite3
import collections
import matplotlib.pyplot as plt

import urlmarker
import re

import seaborn as sns

# sns.set(style="white", context="talk")

import logging

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler("naive_bayes.log")
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)


# sqlite3 connection
dbname = "/home/aahu/Dropbox/ryancompton.net/assets/praw_drugs/drugs.db"
conn = sqlalchemy.create_engine("sqlite+pysqlite:///" + dbname, module=sqlite3.dbapi2)


def load_subreddit(tablename, conn):
    df = pd.read_sql(tablename, conn)
    return df


# <codecell>

from nltk.tokenize.stanford import StanfordTokenizer

stanfordTokenizer = StanfordTokenizer(
    path_to_jar="/home/aahu/Downloads/stanford-corenlp-full-2015-01-30/stanford-corenlp-3.5.1.jar"
)


def my_tokenize(text):
    return nltk.word_tokenize(text)
    # return nltk.wordpunct_tokenize(text)
    # return stanfordTokenizer.tokenize(text)
    # return nltk.tokenize.TreebankWordTokenizer().tokenize(text)


def build_tfidf_transformer(
    docs=[], tokenizer=my_tokenize, max_doc_count=2000, vocab_limit=10000
):
    """
    fit tfidf vocabulary
    max_doc_count tosses out words that are too common (e.g. 'dude')
    """
    if max_doc_count is not None:
        max_doc_f = float(max_doc_count) / len(docs)
        logger.info("max_doc_f\t{}".format(max_doc_f))
    else:
        max_doc_f = 1.0
    tfidf = sklearn.feature_extraction.text.TfidfVectorizer(
        tokenizer=tokenizer,
        stop_words="english",
        max_df=max_doc_f,
        max_features=vocab_limit,
    )
    tfidf.fit_transform(docs)

    return tfidf


def build_count_transformer(
    docs=[], tokenizer=my_tokenize, max_doc_count=2000, vocab_limit=10000
):
    """
    fit count vocabulary (seems to work better than tfidf here)
    max_doc_count tosses out words that are too common (e.g. 'dude')
    """
    if max_doc_count is not None:
        max_doc_f = float(max_doc_count) / len(docs)
        logger.info("max_doc_f\t{}".format(max_doc_f))
    else:
        max_doc_f = 1.0
    tfidf = sklearn.feature_extraction.text.CountVectorizer(
        tokenizer=tokenizer,
        stop_words="english",
        max_df=max_doc_f,
        max_features=vocab_limit,
    )
    tfidf.fit_transform(docs)

    return tfidf


# <codecell>

import scipy


def sparse_to_dict(mat, fnames):
    """
    convert scipy.sparse (which is what sklean uses)
    to dict (which is easier for nltk)
    usually fnames is from tfidf.get_feature_names()
    """
    cx = scipy.sparse.coo_matrix(mat)
    d = {}
    for i, j, v in zip(cx.row, cx.col, cx.data):
        d[fnames[j]] = v
    return d


def features_from_messages(messages, label, feature_extractor, **kwargs):
    """
    Make a (features, label) tuple for each message in a list of a certain,
    label of e-mails ('spam', 'ham') and return a list of these tuples.

    Note every text in 'messages' should have the same label.
    """
    features_labels = []
    feature_vecs = feature_extractor(messages)
    for feature_vec in feature_vecs:
        features_labels.append((feature_vec, label))
    return features_labels


def test_train_split(feature_vecs, hold_out_frac=0.1):
    test_idxs = np.random.choice(
        range(len(feature_vecs)), int(len(feature_vecs) * hold_out_frac), replace=False
    )
    test_idxs = list(test_idxs)
    train_idxs = [idx for idx in range(len(feature_vecs)) if idx not in test_idxs]

    test_out = [feature_vecs[idx] for idx in test_idxs]
    train_out = [feature_vecs[idx] for idx in train_idxs]

    return test_out, train_out


# <codecell>


def feature_vecs_to_nltk_fmt(feature_vecs, transformer):
    out = []
    for fv, lbl in feature_vecs:
        out.append((sparse_to_dict(fv, transformer), lbl))
    return out


def check_classifier(test_pos, train_pos, test_neg, train_neg):
    """
    Train the classifier on the training spam and ham, then check its accuracy
    on the test data, and show the classifier's most informative features.
    """
    train_set = train_pos + train_neg
    # Train the classifier on the training set
    classifier = nltk.classify.NaiveBayesClassifier.train(train_set)

    # How accurate is the classifier on the test sets?
    print(
        "Test positive labels accuracy: {0:.2f}%".format(
            100 * nltk.classify.accuracy(classifier, test_pos)
        )
    )
    print(
        "Test negative labels accuracy: {0:.2f}%".format(
            100 * nltk.classify.accuracy(classifier, test_neg)
        )
    )

    pdf = my_show_most_informative_features(classifier, 50)
    print(pdf)
    pdf = pdf[pdf["predicts_for"] == test_pos[0][1]]

    # plt.suptitle('Most informative features')
    # plt.xkcd()
    # pdf[['fname','ratio']].plot(x='fname',kind='barh')
    # plt.title('Most distinguishing terms for drug subreddits')
    # plt.figtext(.5,.85,'The ratios describe the probability that each \
    # term appears in a comment within the subreddit divided by the \
    # probability that the term appears in a comment outside the subreddit.',fontsize=10,ha='center')

    #    plt.title(r"""\Huge{Probability} term appears in a comment in the subreddit \
    #        divided by \newline the probability that the term appears in a comment outside the subreddit.""")
    # Make room for the ridiculously large title.
    return pdf.sort(columns="ratio")


# <codecell>


def build_binary_classifier_inputs(df, tfidf, subreddit_name="opiates"):
    opiates_txt = df[df["subreddit"] == subreddit_name]["body"]
    opiate_vecs = features_from_messages(
        opiates_txt, label=subreddit_name, feature_extractor=tfidf.transform
    )

    non_opiates_txt = df[df["subreddit"] != subreddit_name]["body"]
    sample_rows = np.random.choice(
        non_opiates_txt.index.values, len(opiates_txt), replace=False
    )  # downsample to balance
    non_opiates_txt = non_opiates_txt.iloc[sample_rows]
    non_opiate_vecs = features_from_messages(
        non_opiates_txt,
        label="not_" + subreddit_name,
        feature_extractor=tfidf.transform,
    )

    test_pos, train_pos = test_train_split(opiate_vecs)
    test_neg, train_neg = test_train_split(non_opiate_vecs)

    # convert to dicts (for nltk)
    test_pos = feature_vecs_to_nltk_fmt(test_pos, tfidf.get_feature_names())
    train_pos = feature_vecs_to_nltk_fmt(train_pos, tfidf.get_feature_names())
    test_neg = feature_vecs_to_nltk_fmt(test_neg, tfidf.get_feature_names())
    train_neg = feature_vecs_to_nltk_fmt(train_neg, tfidf.get_feature_names())

    return test_pos, train_pos, test_neg, train_neg


def my_show_most_informative_features(classifier, n=10):
    # Determine the most relevant features, and display them.
    cpdist = classifier._feature_probdist
    print("Most Informative Features")

    l = []
    for fname, fval in classifier.most_informative_features(n):
        d = {"fname": fname, "fval": fval}

        def labelprob(l):
            return cpdist[l, fname].prob(fval)

        labels = sorted(
            [l for l in classifier._labels if fval in cpdist[l, fname].samples()],
            key=labelprob,
        )
        if len(labels) == 1:
            continue
        l0 = labels[0]
        l1 = labels[-1]

        d["predicts_for"] = l1
        d["predicts_against"] = l0

        if cpdist[l0, fname].prob(fval) == 0:
            ratio = np.inf
        else:
            ratio = cpdist[l1, fname].prob(fval) / cpdist[l0, fname].prob(fval)

        d["ratio"] = ratio
        l.append(d)
        print(
            (
                "%24s = %-14r %6s : %-6s = %s : 1.0"
                % (fname, fval, ("%s" % l1)[:6], ("%s" % l0)[:6], ratio)
            )
        )
    return pd.DataFrame(l)


def main():
    st = """The regex patterns in this gist are intended to match any URLs,
including "mailto:foo@example.com", "x-whatever://foo", etc. For a
pattern that attempts only to match web URLs (http, https), see:
https://gist.github.com/gruber/8891611
"""
    logger.info(re.findall(urlmarker.WEB_URL_REGEX, st))
    logger.info(re.findall(urlmarker.ANY_URL_REGEX, st))

    # load the data
    subs = [
        "lsd",
        "Benzodiazepines",
        "opiates",
        "cripplingalcoholism",
        "cocaine",
        "trees",
    ]
    # subs = ['lsd','opiates','cocaine']
    dfs = []
    for sub in subs:
        df = load_subreddit(sub, conn)
        df = df.head(3000)
        dfs.append(df)
    df = pd.concat(dfs)

    # clean out urls
    df["body"] = df["body"].map(lambda x: re.sub(urlmarker.WEB_URL_REGEX, "", x))

    logger.info("tokenize and build vectors...")
    transformer = build_count_transformer(
        df["body"], tokenizer=my_tokenize, max_doc_count=None, vocab_limit=25000
    )
    logger.info("done!")

    test_pos, train_pos, test_neg, train_neg = build_binary_classifier_inputs(
        df, transformer, subreddit_name="cocaine"
    )
    cocaine_df = check_classifier(test_pos, train_pos, test_neg, train_neg)

    test_pos, train_pos, test_neg, train_neg = build_binary_classifier_inputs(
        df, transformer, subreddit_name="lsd"
    )
    lsd_df = check_classifier(test_pos, train_pos, test_neg, train_neg)

    f, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))

    x1 = cocaine_df["fname"]
    y1 = cocaine_df["ratio"]
    # sns.barplot(x1, y1, ci=None, palette="coolwarm", hline=0, ax=ax1)
    cocaine_df["ratio"].plot(kind="bar", ax=ax1)
    # ax1.set_ylim(0, max(cocaine_df['ratio']))
    for i, label in enumerate(list(cocaine_df.index)):
        text = cocaine_df.ix[label]["fname"]
        ax1.annotate(str(text), (i, cocaine_df.ix[label]["ratio"] + 0))
    ax1.set_ylabel("/r/cocaine")

    # x2 = lsd_df['fname']
    # y2 = lsd_df['ratio']
    # sns.barplot(x2, y2, ci=None, palette="coolwarm", hline=0, ax=ax2)
    lsd_df.plot(kind="bar", ax=ax2)
    ax2.set_ylabel("/r/lsd")

    # y3 = pdf['ratio']
    # sns.barplot(x, y3, ci=None, palette="Paired", hline=.1, ax=ax3)
    # ax3.set_ylabel("Qualitative")

    # sns.despine(bottom=True)
    plt.setp(f.axes, yticks=[])
    plt.tight_layout(h_pad=3)
    plt.title("Most distinguishing terms for drug subreddits")

    plt.show()


if __name__ == "__main__":
    main()
