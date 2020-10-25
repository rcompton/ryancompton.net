import concurrent
import geocoder
import json
import s3fs
import pandas as pd
import urllib
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine
import zlib
from itertools import zip_longest


FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

engine = create_engine(os.getenv('CRAIGGER_CONN'))

def geocode(mapaddress, geo_region, post_hood,
            min_confidence=9, mykey=GOOGLE_MAPS_API_KEY):
    try:
        mapaddress2 = mapaddress if ' near ' not in mapaddress else mapaddress.split('near')[0]
        post_hood2 = post_hood.replace('(', '').replace(')', '')
        q = '{0} {1} {2}'.format(mapaddress2, geo_region, post_hood2)
        g = geocoder.google(q, key=mykey)
        logger.info(
            "google address: {0}, confidence: {1}".format(
                g.address, g.confidence))
        if(g.confidence >= min_confidence):
            return {'mapaddress':mapaddress, 'geo.region':geo_region,'post_hood':post_hood, 'address':g.address, 'quality':g.quality, 'lat':g.lat, 'lng':g.lng, 'zip':g.postal, 'craig_address_hash':address_hash((mapaddress,geo_region,post_hood)), 'gconfidence': g.confidence}
    except:
        logger.exception('geo meh')

def process_chunk(chunk):
    def geo_helper(x):
        try:
            return geocode(x[0], x[1], x[2])
        except:
            pass
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(geo_helper, chunk):
            if result:
                results.append(result)
            else:
                logger.warning('geo err')
    geo_results = pd.DataFrame(results)
    geo_results = geo_results.dropna()
    logger.info('writing {} geocoder results'.format(geo_results.shape))
    # psycopg2 connections are thread safe but not across processes "level 2 thread safe"
    little_engine = create_engine(os.getenv('CRAIGGER_CONN'))
    geo_results.to_sql('geocoder_results', little_engine, if_exists='append', index=False)
    return geo_results


def build_address_map(limit=5):
    df = pd.read_sql('SELECT mapaddress, "geo.region", post_hood, data_accuracy from cragprod WHERE "geo.region" = \'US-CA\' and data_accuracy > 9 LIMIT {}'.format(limit), engine)
    df = df[df['mapaddress'].notnull()]
    df = df.drop_duplicates()
    try:
        geo_already_done = pd.read_sql('SELECT * FROM geocoder_results', engine)
    except:
        geo_already_done = None

    geo_input = set()
    for idx,row in df.iterrows():
        try:
            craig_hash = address_hash((row['mapaddress'], row['geo.region'], row['post_hood']))
            if geo_already_done is None or craig_hash not in geo_already_done['craig_address_hash'].values:
                geo_input.add((row['mapaddress'], row['geo.region'], row['post_hood']))
            else:
                logger.info('cache hit')
        except KeyError:
            logger.exception('eh')
    geo_chunks = chunks(geo_input, 200)
    logger.warning('starting google geocoder, df.shape: {0} rows: {1}'.format(df.shape,len(geo_input)))
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=50) as pexecutor:
        for result in pexecutor.map(process_chunk, geo_chunks):
            try:
                if len(result) > 0:
                    results.append(result)
            except:
                logger.exception('??')
    if not results:
        return geo_already_done
    geo_results = pd.concat(results)
    if geo_already_done is not None:
        logger.info('stacking cached')
        geo_results = pd.concat([geo_results, geo_already_done])
    print(geo_results)
    return geo_results

def address_hash(x):
    try:
        return zlib.adler32((x[0]+x[1]+x[2]).encode('utf-8'))
    except:
        return 0

def chunks(iterable, n):
    """Yield successive n-sized chunks from iterable"""
    return zip_longest(*[iter(iterable)]*n, fillvalue=None)


def main():
    # this uses geocoder api but saves to my db
    dfgeo = build_address_map(limit=1000)
    print(dfgeo)

    # query the postprocessed db
    logger.info('query the postprocessed db...')
    dfrent = pd.read_sql('SELECT post_price, post_date, post_bedroom_count, post_sqft, price_per_sqft, netloc, housing, furnished, crawl_date, mapaddress, "geo.region", post_hood from cragprod WHERE "geo.region" = \'US-CA\' and data_accuracy > 9', engine)
    dfrent = dfrent.drop_duplicates()
    dfrent['craig_address_hash'] = dfrent[['mapaddress', 'geo.region', 'post_hood']].apply(address_hash,axis=1)
    print(dfrent)

    logger.info('dfg = pd.merge(dfgeo,dfrent)')
    dfg = pd.merge(dfgeo,dfrent)
    print(dfg)
    dfg.to_sql('joined_results', engine, if_exists='append', index=False)



if __name__ == '__main__':
    main()

