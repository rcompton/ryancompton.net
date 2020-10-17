import concurrent
import json
import s3fs
import pandas as pd
import urllib
import logging
import os


pd.set_option('display.max_columns', None)  
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', -1)

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def s3_to_dics(s3_fname):
    fields = set(['geo.region', 'og:url', 'post_hood', 'post_price',
                  'data_accuracy', 'post_bedroom_count',
                  'post_sqft', 'post_price', 'post_datetime', 'housing', 
                  'crawl_date', 'geo.placename', 'mapaddress'
                 ])
    dics = []
    logger.info(s3_fname)
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
            dics.append(dic)
    logger.info(len(dics))
    logger.info(os.path.basename(s3_fname))
    return dics

def parse_dir(s3dir = 's3://rycpt-crawls/craigslist-housing/'):
    dics = []
    s3 = s3fs.S3FileSystem(anon=False)
    s3_fnames = s3.ls(s3dir)
    s3_fnames = s3_fnames[10:20]
    for s3_fname in s3_fnames:
        s3_to_dics(s3_fname)
    #with concurrent.futures.ThreadPoolExecutor(max_workers=80) as executor:
    #    result = executor.map(s3_to_dics, s3_fnames)
    return dics

def postprocess_df(df):
    df=df[df['mapaddress'].notnull()]
    df=df[df['data_accuracy'].notnull()]
    df['data_accuracy'] = df['data_accuracy'].map(int)
    df = df[df.data_accuracy<11]
    df = df[df.post_price.notnull()]
    df['netloc'] = df['og:url'].map(lambda x: urllib.parse.urlparse(x).netloc)
    df['price_per_sqft'] = df['post_price']/df['post_sqft']
    df = df[df.post_price < 10000]
    df = df[df.post_sqft < 10000]
    df = df[df.price_per_sqft < 10]
    df.crawl_date = df.crawl_date.map(pd.to_datetime).map(pd.datetime.date)
    df['post_date'] = df.post_datetime.map(pd.to_datetime).map(pd.datetime.date)
    return df

def main():
    parse_dir()

if __name__=='__main__':
    main()
