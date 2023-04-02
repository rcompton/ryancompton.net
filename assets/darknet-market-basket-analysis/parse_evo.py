# coding: utf-8

from bs4 import BeautifulSoup
import re
import pandas as pd
import dateutil
import os

import logging

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DATA_DIR = "/home/aahu/Downloads/evolution/evolution/"


def html_to_df(fname, fdate):
    """
    parse an evolution catergory html file
    must spec file date (it doesn't appear in the html)
    """
    logger.info("processing: {}".format(fname))
    soup = BeautifulSoup(open(fname))
    profs = soup.find_all(href=re.compile("http://k5zq47j6wd3wdvjq.onion/profile/.*"))
    l = []
    for p in profs:
        if p.text != "simurgh":  # Welcome back simurgh!
            d = {}
            d["vendor"] = p.text.strip()
            d["product"] = p.fetchPrevious()[1].text.strip()
            d["category"] = soup.title.text.strip().split("::")[1].strip()
            d["date"] = fdate
            l.append(d)
    return pd.DataFrame(l)


def catdir_to_df(catdir, fdate):
    fs = os.listdir(catdir)
    fs = map(lambda x: os.path.join(catdir, x), fs)
    l = [html_to_df(f, fdate) for f in fs]
    return pd.concat(l).reindex()


def main():
    for datestr in os.listdir(DATA_DIR):
        d1 = os.path.join(DATA_DIR, datestr)
        fdate = dateutil.parser.parse(datestr)
        catdir = os.path.join(d1, "category")
        if os.path.exists(catdir):
            logger.info(catdir)
            df = catdir_to_df(catdir, fdate)
            outname = "category_df_" + datestr + ".tsv"
            df.to_csv(os.path.join(DATA_DIR, outname), "\t", index=False)


if __name__ == "__main__":
    main()
