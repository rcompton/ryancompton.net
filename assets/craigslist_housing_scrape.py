#!/usr/bin/env python
# coding: utf-8

import os
import boto3
import concurrent.futures
import datetime
import logging
import numpy as np
import random
import requests
import time
import json
import urllib
import geocoder

from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler(
    os.path.join(os.environ["HOME"], "craigslist-data/log.log")
)
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)
logger.info("starting new scrape!")

proxy_host = "proxy.zyte.com"
proxy_port = "8011"
proxy_auth = os.environ["CRAWLERA_API_KEY"] + ":"
proxies = {
    "https": f"http://{proxy_auth}@{proxy_host}:{proxy_port}/",
    "http": f"http://{proxy_auth}@{proxy_host}:{proxy_port}/",
}


GOOGLE_MAPS_API_KEY = os.environ["GOOGLE_MAPS_API_KEY"]


def parse_divs(html_soup):
    dic = {}
    if not html_soup.find_all("div"):
        return dic
    for div in html_soup.find_all("div", class_="mapaddress"):
        dic["mapaddress"] = div.text
    for viewposting in html_soup.find_all("div", class_="viewposting"):
        dic["data_accuracy"] = viewposting.get("data-accuracy")
        dic["data-latitude"] = viewposting.get("data-latitude")
        dic["data-longitude"] = viewposting.get("data-longitude")
    return dic


def parse_spans(html_soup):
    dic = {}
    if not html_soup.find_all("span"):
        return dic
    for span in html_soup.find_all("span", class_="price"):
        dic["price"] = span.text
    for span in html_soup.find_all("span", class_="housing"):
        dic["housing"] = span.text
    return dic


def parse_metas(html_soup):
    dic = {}
    if not html_soup.find_all("meta"):
        return dic
    for tag in html_soup.find_all("meta"):
        if tag.get("name") == "description":
            dic["description"] = tag.get("content")
        if tag.get("name") == "geo.placename":
            dic["geo.placename"] = tag.get("content")
        if tag.get("name") == "geo.position":
            dic["geo.position"] = tag.get("content")
        if tag.get("name") == "geo.region":
            dic["geo.region"] = tag.get("content")
        if tag.get("property") == "og:url":
            dic["og:url"] = tag.get("content")
        if tag.get("property") == "og:image":
            dic["og:image"] = tag.get("content")
        if tag.get("property") == "og:title":
            dic["og:title"] = tag.get("content")
    return dic


def parse_text(html_soup):
    return {"html_content": str(html_soup)}


def parse_page(html_soup):
    return {
        **parse_metas(html_soup),
        **parse_divs(html_soup),
        **parse_spans(html_soup),
        **parse_text(html_soup),
    }


def accumulate_posts(city_url):
    # Accumulate the day's posts.
    posts = []
    for offset in [120 * x for x in range(0, 3)]:
        # All houses posted today in sfbay
        search_url = make_search_url(city_url, offset)
        logger.info("search_url: {}".format(search_url))
        try:
            r = requests.get(
                search_url,
                proxies=proxies,
                verify="/usr/local/share/ca-certificates/zyte-smartproxy-ca.crt",
            )
        except requests.exceptions.RequestException as reqe:
            logger.error(reqe)
            continue
        if r.status_code != requests.codes.ok:
            logger.error("search parse failed: {}; status: {}".format(search_url, r))
            return posts
        # parse search result html
        dics = parse_search_html(r)
        logger.info("search_url: {}; hits: {}".format(search_url, len(dics)))
        posts.extend(dics)
        if len(dics) < 120:
            break
    return posts


def writes3(dics, cityname):
    outstr = "\n".join([json.dumps(dic) for dic in dics])
    fname = "craigslist-housing/{0}_{1}.json".format(
        cityname, datetime.datetime.now().isoformat()
    )
    logger.info("writing: {}".format(fname))
    s3 = boto3.resource("s3")
    s3object = s3.Object("rycpt-crawls", fname)
    s3object.put(Body=(bytes(outstr.encode("UTF-8"))))
    return


def make_search_url(city_url, offset=0):
    # 'https://{}.craigslist.org/search/apa?postedToday=1&availabilityMode=0&housing_type=6&sale_date=all+dates' SFH only
    surl = urllib.parse.urljoin(
        city_url, "/search/apa?postedToday=1&availabilityMode=0&sale_date=all+dates"
    )
    if offset:
        surl = "{0}&s={1}".format(surl, offset)
    return surl


def parse_search_html(r):
    # parse search result response
    feed_soup = BeautifulSoup(r.text, "html.parser")
    posts = feed_soup.find_all("li", class_="result-row")
    # extract data item-wise
    dics = []
    for post in posts:
        # import ipdb;ipdb.set_trace()
        dic = {}
        if post.find("span", class_="result-hood") is not None:
            # posting date
            # grab the datetime element 0 for date and 1 for time
            dic["post_datetime"] = post.find("time", class_="result-date")["datetime"]
            # neighborhoods
            dic["post_hood"] = post.find("span", class_="result-hood").text
            # title text
            post_title = post.find("a", class_="result-title hdrlnk")
            dic["post_title_text"] = post_title.text
            # post link
            dic["post_link"] = post_title["href"]
            # removes the \n whitespace from each side, removes the currency
            # symbol, and turns it into an int
            try:
                dic["post_price"] = int(post.a.text.strip().replace("$", ""))
            except BaseException:
                dic["post_price"] = np.nan
            if post.find("span", class_="housing") is not None:
                # if the first element is accidentally square footage
                if "ft2" in post.find("span", class_="housing").text.split()[0]:
                    # make bedroom nan
                    dic["post_bedroom_count"] = np.nan
                    # make sqft the first element
                    dic["post_sqft"] = int(
                        post.find("span", class_="housing").text.split()[0][:-3]
                    )
                # if the length of the housing details element is more than 2
                elif len(post.find("span", class_="housing").text.split()) > 2:
                    # therefore element 0 will be bedroom count
                    dic["post_bedroom_count"] = (
                        post.find("span", class_="housing")
                        .text.replace("br", "")
                        .split()[0]
                    )
                    # and sqft will be number 3, so set these here and append
                    dic["post_sqft"] = int(
                        post.find("span", class_="housing").text.split()[2][:-3]
                    )
                # if there is num bedrooms but no sqft
                elif len(post.find("span", class_="housing").text.split()) == 2:
                    # therefore element 0 will be bedroom count
                    dic["post_bedroom_count"] = (
                        post.find("span", class_="housing")
                        .text.replace("br", "")
                        .split()[0]
                    )
                    # and sqft will be number 3, so set these here and append
                    dic["post_sqft"] = np.nan
                else:
                    dic["post_bedroom_count"] = np.nan
                    dic["post_sqft"] = np.nan
        dics.append(dic)
    return dics


def is_rf_eligible(dic):
    data_accuracy = dic.get("data_accuracy")
    if not data_accuracy:
        return False
    if int(data_accuracy) > 10:
        return False
    if not dic.get("post_price"):
        return False
    if dic.get("mapaddress") and dic.get("post_hood") and dic.get("geo.region"):
        return True


def geocode(
    mapaddress, geo_region, post_hood, min_confidence=9, mykey=GOOGLE_MAPS_API_KEY
):
    post_hood = post_hood.replace("(", "").replace(")", "")
    q = "{0} {1} {2}".format(mapaddress, geo_region, post_hood)
    g = geocoder.google(q, key=mykey)
    logger.info("google address: {0}, confidence: {1}".format(g.address, g.confidence))
    if g.confidence >= min_confidence:
        return g.address


def mangle_encode_address(address):
    mangled = address.replace(",", "")
    return urllib.parse.quote(mangled)


def get_redfin_url(address):
    mangled_address = mangle_encode_address(address)
    autocomplete_url = "https://www.redfin.com/stingray/do/location-autocomplete?location={0}&count=10&v=2".format(
        mangled_address
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    }
    r = requests.get(autocomplete_url, headers=headers)
    # , proxies=proxies, verify=False)
    if r.status_code != 200:
        logger.info(
            "rf url fail: {0} {1} {2}".format(
                r.status_code, r.headers, autocomplete_url
            )
        )
        return
    else:
        try:
            dic = json.loads(r.content.decode().split("&&")[-1])
            if "payload" in dic:
                payload = dic["payload"]
            else:
                logger.warning("payload absent: {0}".format(dic))
            if "exactMatch" in payload:
                match = payload["exactMatch"]
                return {
                    "rf_id": match["id"],
                    "rf_type": match["type"],
                    "rf_url": urllib.parse.urljoin(
                        "https://www.redfin.com", match["url"]
                    ),
                }
            else:
                logger.warning("rf payload no exactMatch fail: {0}".format(payload))
        except BaseException:
            logger.warning("rf content parse fail: {0}".format(r.content))


def extract_tax(rf_soup):
    for tag in rf_soup.find_all("div", class_="tax-record"):
        rdics = []
        for row in tag.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                rdic = {}
                rdic["rf_tax_year"] = cols[0].text
                rdic["rf_tax_paid"] = cols[1].text
                rdics.append(rdic)
    return rdics


def extract_basic_info(rf_soup):
    basic_info = rf_soup.find("div", class_="basic-info")
    facts_table = basic_info.find("div", class_="facts-table")
    fdic = {}
    for row in facts_table.find_all("div", class_="table-row"):
        fdic["rf_" + row.find("span", class_="table-label").text] = row.find(
            "div", class_="table-value"
        ).text
    return fdic


def extract_taxable_value(rf_soup):
    tax_val = rf_soup.find("div", class_="taxable-value")
    tax_table = tax_val.find("div", class_="tax-table").find("table")
    dic = {}
    for row in tax_table.find_all("tr"):
        dic["rf_" + row.find("td", class_="heading").text] = row.find(
            "td", class_="value"
        ).text
    return dic


def parse_rf(rf_soup):
    try:
        tax = extract_tax(rf_soup)
    except BaseException:
        logger.warning("rf tax parse fail: {0}".format(tax))
    try:
        basic_info = extract_basic_info(rf_soup)
    except BaseException:
        logger.warning("rf basic_info parse fail: {0}".format(basic_info))
    try:
        taxable_value = extract_taxable_value(rf_soup)
    except BaseException:
        logger.warning("rf taxable_value parse fail: {0}".format(taxable_value))
    return {"rf_tax_history": tax, **basic_info, **taxable_value}


def tax_join(mapaddress, geo_region, post_hood):
    output = {}
    address = geocode(mapaddress, geo_region, post_hood)
    if not address:
        return
    output["clean_address"] = address
    rf_url = get_redfin_url(address)
    if not rf_url:
        return output
    output = {**output, **rf_url}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
    }
    r = requests.get(rf_url["rf_url"], headers=headers, proxies=proxies, verify=False)
    rf_soup = BeautifulSoup(r.text, "html.parser")
    parsed_rf = parse_rf(rf_soup)
    if not parsed_rf:
        return output
    output = {**output, **parsed_rf}
    output["rf_soup_content"] = rf_soup.content
    return output


def do_one_city(city_url, do_rf_join=False):
    dics = []
    posts = accumulate_posts(city_url)
    logger.info("fetching {0} posts for {1}".format(len(posts), city_url))
    no_links = 0
    for post in posts:
        if "post_link" not in post:
            no_links += 1
            continue
        try:
            r = requests.get(post["post_link"], proxies=proxies, verify=False)
        except BaseException:
            continue
        if r.status_code != requests.codes.ok:
            logger.error("search parse failed: {}; status: {}".format(search_url, r))
            continue
        html_soup = BeautifulSoup(r.text, features="html.parser")
        dic = parse_page(html_soup)
        dic["crawl_date"] = datetime.datetime.now().isoformat()
        dic = {**dic, **post}
        # rf join
        if is_rf_eligible(dic) and do_rf_join:
            logger.debug("starting rf join for: {0}".format(dic["og:url"]))
            rf_data = tax_join(dic["mapaddress"], dic["geo.region"], dic["post_hood"])
            if rf_data:
                logger.debug("rf join success!")
                dic = {**dic, **rf_data}
        else:
            logger.debug(
                "not eligible: {0}".format(
                    {
                        k: dic.get(k)
                        for k in [
                            "mapaddress",
                            "post_hood",
                            "geo.region",
                            "data_accuracy",
                        ]
                    }
                )
            )
        dics.append(dic)
        logger.info(
            "fetched URL: {}; successes: {}".format(post["post_link"], len(dics))
        )
    logger.debug("no link counter: {}".format(no_links))
    if dics:
        cityname = urllib.parse.urlparse(city_url).netloc
        writes3(dics, cityname)


def main():

    with open(
        os.path.join(
            os.environ["HOME"], "ryancompton.net/assets/craig_housing_cities.txt"
        ),
        "r",
    ) as fin:
        city_urls = fin.read().splitlines()
        city_urls = set(city_urls)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(do_one_city, city_urls)

    return


if __name__ == "__main__":
    logger.info("starting new scrape! main")
    main()
