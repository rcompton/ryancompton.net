# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

import pandas as pd
import praw
import collections
import logging

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# <codecell>


def get_subreddit_authors(subreddit_name="surfing", limit=None):
    """
    Collect unique authors of recent comments in a subreddit
    """
    r = praw.Reddit(
        user_agent="get_coauthors_for_plotting; subreddit={0}; limit={1}".format(
            subreddit_name, limit
        )
    )
    r.login(username="lunada_account", password="oodqWk67WeLk")
    comments = r.get_comments(subreddit_name, "all", limit=limit)

    redditors = []
    for x in comments:
        try:
            redditors.append(x.author)
        except:
            logger.error("comments problem on {0}".format(subreddit_name))

    # hash based on usernames, Redditor class has no __hash__ ...
    d = {str(x): x for x in redditors}
    return list(d.values())


def get_commented_subreddits(redditor, limit=None):
    """
    Figure all the subreddits a redditor comments to
    """
    logger.info("getting post history for {0} limit={1}".format(redditor, limit))
    rcs = redditor.get_comments(limit=limit)
    out = [c.submission.subreddit for c in rcs]
    logger.info("Dowloaded comments from {0}: {1}".format(redditor, len(out)))
    return out


def get_adjacent_subreddits(
    subreddit_name="surfing", redditors_limit=5, comments_limit=10
):
    """
    Find all subreddits which share a redditor with the argument subreddit
    return a list of tuples which will be used as the graph's edgelist
    """
    redditors = get_subreddit_authors(
        subreddit_name=subreddit_name, limit=redditors_limit
    )
    logger.info("redditors in {0}: {1}".format(subreddit_name, redditors))
    edges = []
    for redditor in redditors:
        try:
            # if redditor is not None:
            rscs = get_commented_subreddits(redditor, limit=comments_limit)
            edges.extend([(subreddit_name.lower(), str(x).lower()) for x in rscs])
        except:
            logger.error("problem with redditor {0}".format(redditor))

    # figure weights
    c = collections.Counter(edges)
    weighted_edges = [(x[0], x[1], c[x]) for x in c]
    print(weighted_edges)
    return weighted_edges


def main_from_source():
    source_subreddit = "surfing"
    redditors_limit = 100
    comments_limit = 50

    all_edges = get_adjacent_subreddits(
        subreddit_name=source_subreddit,
        redditors_limit=redditors_limit,
        comments_limit=comments_limit,
    )

    # repeat the experiment for all distance-1 subreddits
    d1_subreddits = set([x[1] for x in all_edges])
    logger.info(d1_subreddits)
    for d1_subreddit in d1_subreddits:
        new_edges = get_adjacent_subreddits(
            subreddit_name=d1_subreddit,
            redditors_limit=redditors_limit,
            comments_limit=comments_limit,
        )
        all_edges.extend(new_edges)

    with open(source_subreddit + "_edgelist.tsv", "w") as fout:
        for edge in all_edges:
            fout.write("{0}\t{1}\t{2}\n".format(edge[0], edge[1], edge[2]))

    return


def main():
    df = pd.read_csv("redditmetrics_top500.tsv", sep="\t")
    logger.info(df.columns)
    df = df[df["Rank "] < 300]
    subreddits = df["Reddit "].map(lambda x: x.split("/")[2].strip().lower()).tolist()
    logger.info(subreddits)

    redditors_limit = 100
    comments_limit = 50
    all_edges = []
    for subreddit in subreddits:
        logger.info("downloading: /r/{0}".format(subreddit))
        try:
            new_edges = get_adjacent_subreddits(
                subreddit_name=subreddit,
                redditors_limit=redditors_limit,
                comments_limit=comments_limit,
            )
            all_edges.extend(new_edges)
        except:
            logger.exception("something??")

    with open("top500_edgelist.tsv", "w") as fout:
        for edge in all_edges:
            fout.write("{0}\t{1}\t{2}\n".format(edge[0], edge[1], edge[2]))

    return


if __name__ == "__main__":
    main()
