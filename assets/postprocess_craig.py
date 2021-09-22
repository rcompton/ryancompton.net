import argparse
import concurrent
import json
import logging
import os
import pandas as pd
import s3fs
import urllib
from datetime import datetime
from sqlalchemy import create_engine

parser = argparse.ArgumentParser(description='Parse the crawled data in S3 to the database.')
parser.add_argument('date', type=str, help='iso format date to process')
args = parser.parse_args()

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

engine = create_engine(os.getenv('CRAIGGER_CONN'))


def s3_to_dics(s3_fname):
    fields = set(['geo.region', 'og:url', 'post_hood', 'post_price',
                  'data_accuracy', 'post_bedroom_count',
                  'post_sqft', 'post_price', 'post_datetime', 'housing',
                  'crawl_date', 'geo.placename', 'mapaddress'
                 ])
    dics = []
    logger.info(f"working on: {s3_fname}")
    s3 = s3fs.S3FileSystem(anon=False)
    with s3.open(s3_fname,'r') as fin:
        for line in fin.readlines():
            dic = json.loads(line)
            furnished_hack = False
            if 'text' in dic:
                furnished_hack = 'furnished' in dic['text']
            else:
                furnished_hack = False
            dic = {k:dic[k] for k in dic if k in fields}
            dic['furnished']  = furnished_hack
            try:
                if 'mapaddress' in dic and 'geo_region' in dic and 'post_hood' in dic:
                    dic['clean_address'] = geocode(dic['mapaddress'], dic['geo_region'], dic['post_hood'])
            except:
                logger.exception('geo meh')
            dics.append(dic)
    try:
        logger.info(f'writing parsed to cragprod: {s3_fname}')
        df = pd.DataFrame(dics)
        df = postprocess_df(df)
        df.to_sql('cragprod', engine, if_exists='append', index=False)
        logger.info(f'done! writing: {s3_fname}')
    except:
        logger.exception('database meh')
    return

def parse_dir(date, s3dir = 's3://rycpt-crawls/craigslist-housing/'):
    dics = []
    s3 = s3fs.S3FileSystem(anon=False)
    all_s3_fnames = s3.ls(s3dir)
    s3_fnames = [x for x in all_s3_fnames if date in x]  # brittle af date filter
    for s3_fname in s3_fnames:
        s3_to_dics(s3_fname)
    return dics

def postprocess_df(df):
    #df=df[df['mapaddress'].notnull()]
    #df=df[df['data_accuracy'].notnull()]
    df['data_accuracy'] = df['data_accuracy'].map(lambda x: int(x) if pd.notnull(x) else None)
    df = df[df.data_accuracy<11]
    df = df[df.post_price.notnull()]
    df['netloc'] = df['og:url'].map(lambda x: urllib.parse.urlparse(x).netloc)
    df['price_per_sqft'] = df['post_price']/df['post_sqft']
    #df = df[df.post_price < 10000]
    #df = df[df.post_sqft < 10000]
    #df = df[df.price_per_sqft < 10]
    df.crawl_date = df.crawl_date.map(pd.to_datetime).map(datetime.date)
    df['post_date'] = df.post_datetime.map(pd.to_datetime).map(datetime.date)
    return df

def main():
    logger.warning(f'args.date: {args.date}')
    parse_dir(args.date)

if __name__=='__main__':
    main()
