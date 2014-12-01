# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

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

# <codecell>

def get_subreddit_authors(subreddit_name='surfing',limit=None):
    """
    Collect unique authors of recent comments in a subreddit
    """
    r = praw.Reddit(user_agent='get_subreddit_coauthors_for_plotting;; v1.0')
    comments = r.get_comments(subreddit_name,'all',limit=limit)
    redditors = [x.author for x in comments]
    
    #hash based on usernames, Redditor class has no __hash__ ...
    d = {str(x): x for x in redditors}
    return list(d.values())

def get_commented_subreddits(redditor, limit=None):
    """
    Figure all the subreddits a redditor comments to
    """
    logger.info('getting post history for {0}'.format(redditor))
    rcs = redditor.get_comments(limit=limit)
    out = [c.submission.subreddit for c in rcs]
    logger.info('Dowloaded comments from {0}: {1}'.format(redditor, len(out)))
    return out

def get_adjacent_subreddits(subreddit_name='surfing',limit=5):
    """
    Find all subreddits which share a redditor with the argument subreddit
    return a list of tuples which will be used as the graph's edgelist
    """
    redditors = get_subreddit_authors(subreddit_name=subreddit_name,limit=limit)
    logger.info('redditors in {0}: {1}'.format(subreddit_name, redditors))
    edges = []
    for redditor in redditors:
        rscs = get_commented_subreddits(redditor, limit=limit)
        edges.extend([(subreddit_name.lower(), str(x).lower()) for x in rscs])

    #figure weights
    c = collections.Counter(edges)
    weighted_edges = [(x[0], x[1], c[x]) for x in c]
    print(weighted_edges)
    return weighted_edges

def main():
	source_subreddit = 'worldnews'
	edges = get_adjacent_subreddits(subreddit_name=source_subreddit, limit=None)
	with open(source_subreddit+'_edgelist.tsv','w') as fout:
		for edge in edges:
			fout.write('{0}\t{1}\t{2}\n'.format(edge[0],edge[1],edge[2]))

	return

if __name__ == '__main__':
	main()
