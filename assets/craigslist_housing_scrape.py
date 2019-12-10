#!/usr/bin/env python
# coding: utf-8

import datetime
import feedparser
import logging
import pandas as pd
import random
import requests
import time

from bs4 import BeautifulSoup

FORMAT = '%(asctime)-15s %(levelname)-6s %(message)s'
DATE_FORMAT = '%b %d %H:%M:%S'
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler('/home/rycpt/craigslist-data/log2.log')
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)


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


def parse_page(html_soup):
    return {**parse_metas(html_soup), **parse_divs(html_soup) , **parse_spans(html_soup)}


def main():
    # Accumulate the day's feeds.
    postss = []
    for offset in [0,25,50,75,100]:
        # All houses posted today in sfbay
        rssurl = 'https://sfbay.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates&format=rss&s={}'.format(offset)
        posts = feedparser.parse(rssurl)
        postss.append(posts)
        logger.info('feed URL: {}; hits: {}'.format(rssurl, len(posts.entries)))

    # Iterate through the listings and get what you can.
    dics = []
    for posts in postss:
        for post in posts.entries:
            url = post.links[0].href
            time.sleep(random.choice([0,20]))
            response = requests.get(url)
            if response.status_code != 200:
                logger.warning('failed URL: {}; Status code: {}'.format(url, response.status_code))
                continue
            html_soup = BeautifulSoup(response.text, features='html.parser')
            dics.append(parse_page(html_soup))
            logger.info('fetched URL: {}; successes: {}'.format(url, len(dics)))
            #if len(dics) > 1:
            #    break
        df = pd.DataFrame(dics)
        df.to_json('/home/rycpt/craigslist-data/{}.json'.format(datetime.datetime.now().isoformat()), orient='records')


if __name__ == "__main__":
    main()
