# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

import pandas as pd
import praw
import collections
import multiprocessing
import random
import logging
import datetime
import requests
import os
import pytz
import sqlite3
import sqlalchemy

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)

handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler('/home/ubuntu/praw_downloader.log')
fhandler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)

class PRAWSubredditDownloader(object):
    def __init__(self,subreddit_name,username,pw):
        self.subreddit_name = subreddit_name
        self.redditors = None
        self.r = praw.Reddit(user_agent='get_drugs_subreddits; subreddit_name={0}'
                                    .format(self.subreddit_name))
        self.r.login(username=username,password=pw)

        self.run_datetime = datetime.datetime.now()

        self.out_dir = os.path.join('subreddit_downloader','results_'+str(self.run_datetime))
        if not os.path.exists(self.out_dir):
             os.mkdir(self.out_dir)

        self.conn = sqlalchemy.create_engine('sqlite+pysqlite:////home/ubuntu/drugs.db', 
                                            module=sqlite3.dbapi2)


    def get_subreddit_authors(self,limit=None):
        """
        Collect unique authors of recent comments in a subreddit
        """
        out_dir = os.path.join(self.out_dir,'subreddit_authors')
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        comments = self.r.get_comments(self.subreddit_name,limit=limit)
        cs = []
        for c in comments:
            try:
                d = {'author':c.author,
                'subreddit':self.subreddit_name,
                'body':c.body.replace('\n',' '), 
                'posted_time': datetime.datetime.utcfromtimestamp(c.created_utc)}
                cs.append(d)
            except:
                logger.exception('comments download problem')
        
        #save to sql
        c_strs = [{k:str(v) for (k,v) in d.items()} for d in cs]
        df = pd.DataFrame(c_strs)
        df = df.drop_duplicates()
        df.to_sql(self.subreddit_name,self.conn,index=False,if_exists='append')
        self.drop_sqlite3_duplicates(self.subreddit_name,'body')

        #hash based on usernames, Redditor class has no __hash__ ...
        d = {str(x['author']): x['author'] for x in cs}
        return list(d.values())

    def get_redditor_history(self, redditor, limit=None):
        """
        Figure all the subreddits a redditor comments to
        """
        logger.info('getting post history for {0} limit={1}'.format(redditor,limit))
        rcs = redditor.get_comments(limit=limit)
        out = [{'redditor':redditor.name,
                'subreddit':c.subreddit.display_name, 
                'posted_time': datetime.datetime.utcfromtimestamp(c.created_utc),
                'body':c.body.replace('\n',' ')} for c in rcs]

        #save to sql
        out_table_name = 'redditors_history'
        df = pd.DataFrame(out)
        df = df.drop_duplicates()
        df.to_sql(out_table_name, self.conn, index=False, if_exists='append')
        self.drop_sqlite3_duplicates(out_table_name, 'body')

        logger.info('Dowloaded comments from {0}: {1}'.format(redditor, len(out)))
        return out

    def get_adjacent_subreddits(self,redditors_limit=5, comments_limit=10):
        """
        Find all subreddits which share a redditor with the argument subreddit
        return a list of tuples which will be used as the graph's edgelist
        """
        if self.redditors is None:
            self.redditors = self.get_subreddit_authors(limit=redditors_limit)

        logger.info('num redditors in {0}: {1}'.format(self.subreddit_name, len(self.redditors)))
        edges = []
        for redditor in self.redditors:
            try:
                if redditor is not None:
                    rscs = self.get_redditor_history(redditor, limit=comments_limit)
                    rscs = [d['subreddit'] for d in rscs]
                    edges.extend([(self.subreddit_name.lower(), str(x).lower()) for x in rscs])
            except:
                logger.exception('problem with redditor {0}'.format(redditor))

        #figure weights
        c = collections.Counter(edges)
        weighted_edges = [(x[0], x[1], c[x]) for x in c]
        return weighted_edges

    def drop_sqlite3_duplicates(self, table, hash_column):
        """
        remove rows that contain duplicate text
        take the min rowid
        """
        logger.info('dropping duplicates from: {0}, hash on table: {1}'.format(table, hash_column))

        tbl_size = [r for r in self.conn.engine.execute('SELECT COUNT(rowid) FROM {};'.format(table))]
        logger.info('size: before drop: {}'.format(tbl_size))

        self.conn.engine.execute('DELETE FROM {0} WHERE rowid NOT IN (SELECT MIN(rowid) FROM {0} GROUP BY {1});'
            .format(table, hash_column))

        tbl_size = [r for r in self.conn.engine.execute('SELECT COUNT(rowid) FROM {};'.format(table))]
        logger.info('size: after drop: {}'.format(tbl_size))
        return



def single_subreddit_worker(subreddit_name):
    """
    function to scrape a single subreddit
    amenable to multiprocessing library
    """
    # #choose random credentials
    # df = pd.read_csv('throwaway_accounts.tsv',sep='\t')
    # idx = random.randint(0,len(df)-1)
    # u = df.iloc[idx]['username']
    # pw = df.iloc[idx]['pw']
    # logger.info('praw username={0}'.format(u))

    praw_downloader = PRAWSubredditDownloader(subreddit_name,username='fukumupo',pw='sixoroxo')

    #redditor limit determines how many posts to pull from the subreddit
    #comments_limit is # c's per redditor...
    edges = praw_downloader.get_adjacent_subreddits(redditors_limit=1000,comments_limit=100)

    out_dir = praw_downloader.out_dir
    
    with open(os.path.join(out_dir,subreddit_name+'_edgelist.tsv'),'w') as fout:
        for edge in edges:
            fout.write('{0}\t{1}\t{2}\n'.format(edge[0],edge[1],edge[2]))

    return edges

def main():

    df = pd.read_csv('/home/ubuntu/ryancompton.net/assets/praw_drugs/drugs_subreddit_list_sorted.tsv',sep='\t')
    srs = df['subreddit']

    for sr in srs.tolist()[6:]:
        logger.info(sr)
        while True: #try until no HTTPError
            try:
                single_subreddit_worker(sr)
            except requests.exceptions.HTTPError:
                continue
            break

    # this didn't help due to IP rate-limits
    # p = multiprocessing.Pool(1) #ugh turns out that more processes just gets me rate limited
    # results = p.map(single_subreddit_worker, srs)
    # p.close()
    # p.join()

    return

if __name__ == '__main__':
    main()
