import concurrent
import geocoder
import json
import pandas as pd
import urllib
import logging
import os
from datetime import datetime
from sqlalchemy import create_engine
import zlib
from itertools import zip_longest
import time


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
        start = time.process_time()
        q = '{0} {1} {2}'.format(mapaddress2, geo_region, post_hood2)
        g = geocoder.google(q, key=mykey)
        #logger.info("processed_time: {0} || {1} || google address: {2}, confidence: {3}".format(
        #        round(time.process_time()-start,4), q, g.address, g.confidence))
        return {'mapaddress':mapaddress, 'geo.region':geo_region,'post_hood':post_hood, 'address':g.address, 'quality':g.quality, 'lat':g.lat, 'lng':g.lng, 'zip':g.postal, 'craig_address_hash':address_hash((mapaddress,geo_region,post_hood)), 'gconfidence': g.confidence}
    except:
        logger.exception(post_hood)

def process_chunk(chunk):
    def geo_helper(x):
        if x is None:
            return
        try:
            if all(x):
                return geocode(x[0], x[1], x[2])
            else:
                logger.info("None in geo input: {}".format(x))
        except:
            logger.exception('geo ehhh')
    results = []
    #not threaded ok.
    #for x in chunk:
    #    result = geo_helper(x)
    #    if result:
    #        results.append(result)
    #logger.info('chunk done! size was: {}'.format(len(chunk)))
    #queue.full ....
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for result in executor.map(geo_helper, chunk):
            if result:
                results.append(result)
    geo_results = pd.DataFrame(results)
    geo_results = geo_results.dropna()
    ts = time.process_time()
    # psycopg2 connections are thread safe but not across processes "level 2 thread safe"
    little_engine = create_engine(os.getenv('CRAIGGER_CONN'))
    geo_results.to_sql('geocoder_results', little_engine, if_exists='append', index=False)
    logger.info('wrote {0} geocoder results. time: {1}'.format(len(geo_results), round(time.process_time()-ts,5)))
    return geo_results


def build_address_map(limit=5):
    logger.info('query postprocess db for addresses to geocode')
    df = pd.read_sql('SELECT mapaddress, "geo.region", post_hood, data_accuracy FROM cragprod WHERE "geo.region" = \'US-CA\' and data_accuracy > 9 LIMIT {}'.format(limit), engine)
    df = df[df['mapaddress'].notnull()]
    df = df.drop_duplicates()
    try:
        geo_already_done = pd.read_sql('SELECT * FROM geocoder_results', engine)
    except:
        geo_already_done = None

    cache_hits = 0
    geo_input = set()
    for idx,row in df.iterrows():
        try:
            craig_hash = address_hash((row['mapaddress'], row['geo.region'], row['post_hood']))
            if geo_already_done is None or craig_hash not in geo_already_done['craig_address_hash'].values:
                geo_input.add((row['mapaddress'], row['geo.region'], row['post_hood']))
            else:
                cache_hits += 1
                logger.debug('cache hit: {}'.format(craig_hash))
        except KeyError:
            logger.exception('eh')
    geo_chunks = chunks(geo_input, 100)
    logger.warning('starting google geocoder, df.shape: {0} rows: {1} cache_hits: {2}'.format(df.shape, len(geo_input), cache_hits))
    results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=10) as pexecutor:
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
    dfgeo = build_address_map(limit=450000)
    print(dfgeo)

    # query the postprocessed db
    logger.info('query the postprocessed db...')
    dfrent = pd.read_sql('SELECT post_price, post_date, post_bedroom_count, post_sqft, price_per_sqft, netloc, housing, furnished, crawl_date, mapaddress, "geo.region", post_hood from cragprod WHERE "geo.region" = \'US-CA\' and data_accuracy > 9', engine)
    dfrent = dfrent.drop_duplicates()
    dfrent['craig_address_hash'] = dfrent[['mapaddress', 'geo.region', 'post_hood']].apply(address_hash,axis=1)

    logger.info('dfg = pd.merge(dfgeo,dfrent)')
    dfg = pd.merge(dfgeo,dfrent)
    print(dfg)
    logger.info("dfg.to_sql('joined_results', engine, if_exists='append', index=False)")
    dfg.to_sql('joined_results', engine, if_exists='append', index=False)
    return 0



if __name__ == '__main__':
    main()

