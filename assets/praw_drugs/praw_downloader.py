# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

import pandas as pd
import praw
import collections
import logging

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class PRAWSubredditDownloader(object):
    def __init__(self,subreddit):
        self.subreddit = subreddit
        self.redditors = None
        self.r = praw.Reddit(user_agent='get_drugs_subreddits; subreddit_name={0}'
                                    .format(self.subreddit))
        self.r.login(username='lunada_account',password='oodqWk67WeLk')

    def get_subreddit_authors(self,limit=None):
        """
        Collect unique authors of recent comments in a subreddit
        """
        comments = self.r.get_comments(self.subreddit,'all',limit=limit)
        rs = []
        for x in comments:
           try:
              rs.append(x.author)
           except:
              logger.error('comments download problem')
        #hash based on usernames, Redditor class has no __hash__ ...
        d = {str(x): x for x in rs}
        return list(d.values())

    def get_commented_subreddits(self, redditor, limit=None):
        """
        Figure all the subreddits a redditor comments to
        """
        logger.info('getting post history for {0} limit={1}'.format(redditor,limit))
        rcs = redditor.get_comments(limit=limit)
        out = [c.submission.subreddit for c in rcs]
        logger.info('Dowloaded comments from {0}: {1}'.format(redditor, len(out)))
        return out

    def get_adjacent_subreddits(self,redditors_limit=5, comments_limit=10):
        """
        Find all subreddits which share a redditor with the argument subreddit
        return a list of tuples which will be used as the graph's edgelist
        """
        if self.redditors is None:
            self.redditors = self.get_subreddit_authors(limit=redditors_limit)
        logger.info('redditors in {0}: {1}'.format(self.subreddit, self.redditors))
        edges = []
        for redditor in self.redditors:
            try:
                #if redditor is not None:
                rscs = self.get_commented_subreddits(redditor, limit=comments_limit)
                edges.extend([(self.subreddit.lower(), str(x).lower()) for x in rscs])
            except:
                logger.error('problem with redditor {0}'.format(redditor))

        #figure weights
        c = collections.Counter(edges)
        weighted_edges = [(x[0], x[1], c[x]) for x in c]
        return weighted_edges

def main():

    praw_downloader = PRAWSubredditDownloader('surfing')
    ws = praw_downloader.get_adjacent_subreddits(redditors_limit=5,comments_limit=3)
    for w in ws:
        logger.warning(w)

    return



if __name__ == '__main__':
    main()
