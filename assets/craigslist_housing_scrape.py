#!/usr/bin/env python
# coding: utf-8

import feedparser
import pandas as pd
import requests
import time
import random
import warnings

from bs4 import BeautifulSoup



# All houses posted today in sfbay
rssurl = 'https://sfbay.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates'
posts = feedparser.parse(rssurl)

# Santa Cruz only
#('https://sfbay.craigslist.org/search/scz/apa?availabilityMode=0&format=rss&hasPic=1&postedToday=1')


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
    dics = []
    for post in posts.entries:
        url = post.links[0].href
        time.sleep(random.choice([0,2]))
        response = requests.get(url)
        if response.status_code != 200:
            warnings.warn('URL: {}; Status code: {}'.format(url, response.status_code))
        html_soup = BeautifulSoup(response.text)
        dics.append(parse_page(html_soup))
    df = pd.DataFrame(dics)


if __name__ == "__main__":
    main()
