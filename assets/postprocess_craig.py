import argparse
import concurrent
import json
import logging
import os
import pandas as pd
import smart_open
import boto3
import urllib
from datetime import datetime
from sqlalchemy import create_engine
from money_parser import price_dec

parser = argparse.ArgumentParser(description='Parse the crawled data in S3 to the database.')
parser.add_argument('date', type=str, help='iso format date to process')
args = parser.parse_args()

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler(
    os.path.join(
        os.environ['HOME'],
        'craigslist-data/log.log'))
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)
logger.info("starting new parse!")


engine = create_engine(os.getenv('CRAIGGER_CONN'))

s3_bucket = 'rycpt-crawls'
s3_prefix = 'craigslist-housing'

def s3_to_dics(s3_fname):
    fields = set(['geo.region', 'og:url', 'post_hood', 'price',
                  'data_accuracy', 'post_bedroom_count',
                  'post_sqft', 'post_price', 'post_datetime', 'housing',
                  'crawl_date', 'geo.placename', 'mapaddress', 'og:title'
                 ])
    dics = []
    for line in smart_open.smart_open(s3_fname):
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
        if 'price' in dic and (pd.isna(dic['post_price'])):
            dic['post_price'] = float(price_dec(dic['price'])) # should not use floats for money but whatever
        dics.append(dic)
        if 'data_accuracy' not in dic:
            dic['data_accuracy'] = 9999
    try:
        df = pd.DataFrame(dics)
        df = postprocess_df(df)
        df.to_sql('cragprod', engine, if_exists='append', index=False)
        logger.info(f'wrote to cragprod: {s3_fname}')
    except KeyError:
        logger.info(f'KeyError, skipping. df.shape: {df.shape}')
    except:
        logger.exception('Real database issue')
    return

def parse_dir(date, s3dir = 's3://rycpt-crawls/craigslist-housing/'):
    dics = []

    s3 = boto3.client('s3')
    partial_list = s3.list_objects_v2(
        Bucket=s3_bucket,
        Prefix=s3_prefix)
    obj_list = partial_list['Contents']
    while partial_list['IsTruncated']:
        next_token = partial_list['NextContinuationToken']
        partial_list = s3.list_objects_v2(
            Bucket=s3_bucket,
            Prefix=s3_prefix,
            ContinuationToken=next_token)
        obj_list.extend(partial_list['Contents'])
    s3_fnames = [f's3://{s3_bucket}/'+x['Key'] for x in obj_list if date in x['Key']] #date filter brittle af
    for s3_fname in s3_fnames:
        s3_to_dics(s3_fname)
    return dics

def postprocess_df(df):
    #df=df[df['mapaddress'].notnull()]
    #df=df[df['data_accuracy'].notnull()]
    #logger.warning(f'df.shape init {df.shape}')
    df = df[df.price.notnull()]
    #logger.warning(f'df.shape with price {df.shape}')
    df = df[df.post_price.notnull()]
    #logger.warning(f'df.shape with post_price {df.shape}')
    df['data_accuracy'] = df['data_accuracy'].map(lambda x: int(x) if pd.notnull(x) else None)
    #logger.warning(f'df.shape with any data_accuracy {df.shape}')
    df = df[df.data_accuracy<11]
    #logger.warning(f'df.shape with any data_accuracy < 11 {df.shape}')
    df['netloc'] = df['og:url'].map(lambda x: urllib.parse.urlparse(x).netloc)
    df['price_per_sqft'] = df['post_price']/df['post_sqft']
    #df = df[df.post_price < 10000]
    #df = df[df.post_sqft < 10000]
    #df = df[df.price_per_sqft < 10]
    df.crawl_date = df.crawl_date.map(pd.to_datetime).map(datetime.date)
    df['post_date'] = df.post_datetime.map(pd.to_datetime).map(datetime.date)
    return df

def main():
    #s3_to_dics('s3://rycpt-crawls/craigslist-housing/losangeles.craigslist.org_2021-06-01T11:59:30.179023.json')
    logger.warning(f'args.date: {args.date}')
    parse_dir(args.date)

if __name__=='__main__':
    main()
