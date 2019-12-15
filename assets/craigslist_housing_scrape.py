#!/usr/bin/env python
# coding: utf-8

import os
import boto3
import datetime
import feedparser
import logging
import pandas as pd
import numpy as np
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
logger.info("starting new scrape!")

proxies = {"http": "http://{}:@proxy.crawlera.com:8010/".format(os.environ["CRAWLERA_API_KEY"])}
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

def accumulate_posts(city):
    # Accumulate the day's posts.
    posts = []
    for offset in [120*x for x in range(0,3)]:
        # All houses posted today in sfbay
        search_url = make_search_url(city,offset)
        logger.info('search_url: {}'.format(search_url))
        r = requests.get(search_url, proxies=proxies)
        if r.status_code != requests.codes.ok:
            logger.error('search parse failed: {}; status: {}'.format(search_url, r))
            return posts
        #parse search result html
        dics = parse_search_html(r)
        logger.info('feed URL: {}; hits: {}'.format(search_url, len(dics)))
        posts.extend(dics)
        if len(dics) < 120:
            break
    return posts

def writes3(city, dics):
    outstr = '\n'.join([json.dumps(dic) for dic in dics])
    s3 = boto3.resource('s3')
    s3object = s3.Object('rycpt-crawls', 'craigslist-housing/{0}_{1}.json'.format(city, datetime.datetime.now().isoformat()))
    s3object.put(Body=(bytes(outstr.encode('UTF-8'))))
    return

def make_search_url(city, offset=0):
    surl = 'https://{}.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates'.format(city)
    if offset:
        surl = '{0}&s={1}'.format(surl, offset)
    return surl

def parse_search_html(r):
    #parse search result response
    feed_soup = BeautifulSoup(r.text,'html.parser')
    posts = feed_soup.find_all('li', class_= 'result-row')
    #extract data item-wise
    dics = []
    for post in posts:
        #import ipdb;ipdb.set_trace()
        dic = {}
        if post.find('span', class_ = 'result-hood') is not None:
            #posting date
            #grab the datetime element 0 for date and 1 for time
            dic['post_datetime'] = post.find('time', class_= 'result-date')['datetime']
            #neighborhoods
            dic['post_hood'] = post.find('span', class_= 'result-hood').text
            #title text
            post_title = post.find('a', class_='result-title hdrlnk')
            dic['post_title_text'] = post_title.text
            #post link
            dic['post_link'] = post_title['href']
            #removes the \n whitespace from each side, removes the currency symbol, and turns it into an int
            try:
                dic['post_price'] = int(post.a.text.strip().replace("$", ""))
            except:
                logger.info("no price: {}".format(post.a.text))
                dic['post_price'] = np.nan
            if post.find('span', class_ = 'housing') is not None:
                #if the first element is accidentally square footage
                if 'ft2' in post.find('span', class_ = 'housing').text.split()[0]:
                    #make bedroom nan
                    dic['post_bedroom_count'] = np.nan
                    #make sqft the first element
                    dic['post_sqft'] = int(post.find('span', class_ = 'housing').text.split()[0][:-3])
                #if the length of the housing details element is more than 2
                elif len(post.find('span', class_ = 'housing').text.split()) > 2:
                    #therefore element 0 will be bedroom count
                    dic['post_bedroom_count'] = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                    #and sqft will be number 3, so set these here and append
                    dic['post_sqft'] = int(post.find('span', class_ = 'housing').text.split()[2][:-3])
                #if there is num bedrooms but no sqft
                elif len(post.find('span', class_ = 'housing').text.split()) == 2:
                    #therefore element 0 will be bedroom count
                    dic['post_bedroom_count'] = post.find('span', class_ = 'housing').text.replace("br", "").split()[0]
                    #and sqft will be number 3, so set these here and append
                    dic['post_sqft'] = np.nan
                else:
                    dic['post_bedroom_count'] = np.nan
                    dic['post_sqft'] = np.nan
        dics.append(dic)
    return dics

def main():
    california_cities = [
                        'bakersfield',
                        'chico',
                        'fresno',
                        'goldcountry',
                        'hanford',
                        'humboldt',
                        'imperial',
                        'inlandempire',
                        'losangeles',
                        'mendocino',
                        'merced',
                        'modesto',
                        'monterey',
                        'orangecounty',
                        'palmsprings',
                        'redding',
                        'sacramento',
                        'sandiego',
                        'sfbay',
                        'slo',
                        'santabarbara',
                        'santamaria',
                        'siskiyou',
                        'stockton',
                        'susanville',
                        'ventura',
                        'visalia',
                        'yubasutter',
                        ]
    texas_cities = [
                   'abilene',
                   'amarillo',
                   'austin',
                   'beaumont',
                   'brownsville',
                   'collegestation',
                   'corpuschristi',
                   'dallas',
                   'nacogdoches',
                   'delrio',
                   'elpaso',
                   'galveston',
                   'houston',
                   'killeen',
                   'laredo',
                   'lubbock',
                   'mcallen',
                   'odessa',
                   'sanangelo',
                   'sanantonio',
                   'sanmarcos',
                   'bigbend',
                   'texoma',
                   'easttexas',
                   'victoriatx',
                   'waco',
                   'wichitafalls',
                    ]



    for city in texas_cities + california_cities:
        posts = accumulate_posts(city)
        dics = []
        logger.info("fetching {0} posts for {1}".format(len(posts), city))
        no_links = 0
        for post in posts:
            if 'post_link' not in post:
                no_links += 1
                continue
            r = requests.get(post['post_link'], proxies=proxies)
            if r.status_code != requests.codes.ok:
                logger.error('search parse failed: {}; status: {}'.format(search_url, r))
                continue
            html_soup = BeautifulSoup(r.text, features='html.parser')
            dic = parse_page(html_soup)
            dic['crawl_date'] = datetime.datetime.now().isoformat()
            dic = {**dic, **post}
            dics.append(dic)
            logger.info('fetched URL: {}; successes: {}'.format(post['post_link'], len(dics)))
        logger.info("no link counter: {}".format(no_links))
        writes3(city, dics)
    return

if __name__ == "__main__":
    main()
