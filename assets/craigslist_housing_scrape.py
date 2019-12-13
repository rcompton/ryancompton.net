#!/usr/bin/env python
# coding: utf-8

import os
import boto
import datetime
import feedparser
import logging
import pandas as pd
import random
import requests
import time
import json
import urllib

from bs4 import BeautifulSoup

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler(os.path.join(os.environ['HOME'],'craigslist-data/log.log'))
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)

proxies = {"http": "http://{}:@proxy.crawlera.com:8010/".format(os.environ["CRAWLERA_API_KEY"]}
proxy_handler = urllib.request.ProxyHandler(proxies)


def parse_divs(html_soup):
    dic = {}
    if not html_soup.find_all('div'):
        return dic
    for div in html_soup.find_all('div', class_='mapaddress'):
        dic['mapaddress'] = div.text
    for viewposting in html_soup.find_all('div', class_='viewposting'):
        dic['data_accuracy'] = viewposting.get('data-accuracy')
        dic['data-latitude'] = viewposting.get('data-latitude')
        dic['data-longitude'] = viewposting.get('data-longitude')
    return dic


def parse_spans(html_soup):
    dic = {}
    if not html_soup.find_all('span'):
        return dic
    for span in html_soup.find_all('span', class_='price'):
        dic['price'] = span.text
    for span in html_soup.find_all('span', class_='housing'):
        dic['housing'] = span.text
    for span in html_soup.find_all('span', class_='hxxousing'):
        dic['housing'] = span.text
    return dic


def parse_metas(html_soup):
    dic = {}
    if not html_soup.find_all('meta'):
        return dic
    for tag in html_soup.find_all('meta'):
        if tag.get('name') == 'description':
            dic['description'] = tag.get('content')
        if tag.get('name') == 'geo.placename':
            dic['geo.placename'] = tag.get('content')
        if tag.get('name') == 'geo.position':
            dic['geo.position'] = tag.get('content')
        if tag.get('name') == 'geo.region':
            dic['geo.region'] = tag.get('content')
        if tag.get('property') == 'og:url':
            dic['og:url'] = tag.get('content')
        if tag.get('property') == 'og:image':
            dic['og:image'] = tag.get('content')
        if tag.get('property') == 'og:title':
            dic['og:title'] = tag.get('content')
    return dic


def parse_text(html_soup):
    return {'text':html_soup.get_text()}


def parse_page(html_soup):
    return {**parse_metas(html_soup),
            **parse_divs(html_soup),
            **parse_spans(html_soup),
            **parse_text(html_soup)}

def accumulate_feeds(rssurl_base):
    # Accumulate the day's feeds.
    postss = []
    for offset in [25*x for x in range(0,8)]:
        # All houses posted today in sfbay
        rssurl = '{0}&s={1}'.format(rssurl_base,offset)
        #posts = feedparser.parse(rssurl)
        posts = feedparser.parse(rssurl, handlers=[proxy_handler])
        print(posts)
        if posts.status != 200:
            logger.error('feedparser failed: {}; status: '.format(rssurl, posts.status))
            return
        postss.append(posts)
        logger.info('feed URL: {}; hits: {}'.format(rssurl, len(posts.entries)))
        hits = len(posts.entries)
        if hits < 25:
            break
    return postss

def writes3(dics):
    outstr = '\n'.join([json.dumps(dic) for dic in dics])
    s3 = boto3.resource('s3')
    s3object = s3.Object('rycpt-crawls', 'craigslist-housing/{}.json'.format(datetime.datetime.now().isoformat()))
    s3object.put(Body=(bytes(json.dumps(json_data).encode('UTF-8'))))
    return

def main():
    rssurls = [
               'https://chico.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://miami.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://sfbay.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://losangeles.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://austin.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://seattle.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://chicago.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://portland.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://humboldt.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
               'https://fresno.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss',
              ]
    for rssurl in rssurls:
        postss = accumulate_feeds(rssurl)
        # Iterate through the listings and get what you can.
        for posts in postss:
            dics = []
            for post in posts.entries:
                url = post.links[0].href
                #time.sleep(random.choice([0,20]))
                response = requests.get(url, proxies=proxies)
                if response.status_code != 200:
                    logger.warning('failed URL: {}; Status code: {}'.format(url, response.status_code))
                    continue
                html_soup = BeautifulSoup(response.text, features='html.parser')
                dic = parse_page(html_soup)
                dic['crawl_date'] = datetime.datetime.now().isoformat()
                dics.append(dic)
                logger.info('fetched URL: {}; successes: {}'.format(url, len(dics)))
            writes3(dics)
            #df = pd.DataFrame(dics)
            #df.to_json('/home/rycpt/craigslist-data/{}.json'.format(datetime.datetime.now().isoformat()), orient='records')
    return

if __name__ == "__main__":
    main()
