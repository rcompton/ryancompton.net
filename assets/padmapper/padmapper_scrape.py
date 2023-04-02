import re
import boto3
import os
import requests
import random
import logging
import time
import geocoder
import pandas as pd
from io import BytesIO
from datetime import datetime as dt
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


from assessor_api import process_address


GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler(
    os.path.join(os.environ["HOME"], "padmapper-data/log.log")
)
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)
logger.info("starting padmapper scrape!")

conn_str = os.getenv("CRAIGGER_CONN")  # make sure the tunnel is open
engine = create_engine(conn_str)

# selenium setup
options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--headless")
options.add_argument("--disable_gpu")
options.add_argument("--force-device-scale-factor=1")
options.add_argument("--window-size=1220,1480")
service = Service(executable_path=ChromeDriverManager().install())
# service=Service("/usr/local/bin/chromedriver")

LA_CITIES = [
    "agoura-hills",
    "alhambra",
    "arcadia",
    "artesia",
    "avalon",
    "azusa",
    "baldwin-park",
    "bell",
    "bell-gardens",
    "bellflower",
    "beverly-hills",
    "bradbury",
    "burbank",
    "calabasas",
    "carson",
    "cerritos",
    "claremont",
    "commerce",
    "compton",
    "covina",
    "cudahy",
    "culver-city",
    "diamond-bar",
    "downey",
    "duarte",
    "el-monte",
    "el-segundo",
    "gardena",
    "glendale",
    "glendora",
    "hawaiian-gardens",
    "hawthorne",
    "hermosa-beach",
    "hidden-hills",
    "huntington-park",
    "industry",
    "inglewood",
    "irwindale",
    "la-cañada-flintridge",
    "la-habra-heights",
    "la-mirada",
    "la-puente",
    "la-verne",
    "lakewood",
    "lancaster",
    "lawndale",
    "lomita",
    "long-beach",
    "los-angeles",
    "lynwood",
    "malibu",
    "manhattan-beach",
    "maywood",
    "monrovia",
    "montebello",
    "monterey-park",
    "norwalk",
    "palmdale",
    "palos-verdes-estates",
    "paramount",
    "pasadena",
    "pico-rivera",
    "pomona",
    "rancho-palos-verdes",
    "redondo-beach",
    "rolling-hills",
    "rolling-hills-estates",
    "rosemead",
    "san-dimas",
    "san-fernando",
    "san-gabriel",
    "san-marino",
    "santa-clarita",
    "santa-fe-springs",
    "santa-monica",
    "sierra-madre",
    "signal-hill",
    "south-el-monte",
    "south-gate",
    "south-pasadena",
    "temple-city",
    "torrance",
    "vernon",
    "walnut",
    "west-covina",
    "west-hollywood",
    "westlake-village",
    "whittier",
]
random.shuffle(LA_CITIES)
logger.info(LA_CITIES)


def geocode_and_assess(padmapper_address):
    try:
        g = geocoder.google(padmapper_address, key=GOOGLE_MAPS_API_KEY)
    except:
        logger.exception(padmapper_address)
    if not g.ok:
        logging.error(g.json)

    out = {
        "gaddress": g.address,
        "gquality": g.quality,
        "glat": g.lat,
        "glng": g.lng,
        "gzip": g.postal,
        "gconfidence": g.confidence,
    }
    tax = process_address(g.address)
    if tax is None:
        logger.error(f"No tax for {g.address}")
    else:
        out.update(tax)
    return out


def get_and_scroll(url):
    logger.info(f"get and scroll {url}")
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(45)
    driver.get(url)
    # Wait for the page to fully render
    driver.implicitly_wait(10)
    prev_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        logger.info("Scroll...")
        driver.execute_script(
            "var elems = document.querySelectorAll('*'); for(var i=0; i<elems.length; i++){ var elem = elems[i]; if(elem.scrollHeight > elem.clientHeight){ elem.scrollTop = elem.scrollHeight; } }"
        )
        # Wait for a few seconds for the content to load
        time.sleep(3)
        # Calculate the current height of the page
        current_height = driver.execute_script("return document.body.scrollHeight")
        # Check if the current height is equal to the previous height
        if current_height == prev_height:
            break
        # Update the previous height variable
        prev_height = current_height
    logger.debug("Scroll done.")

    html_content = driver.page_source
    driver.quit()
    return html_content


def screenshot_ad(ad):
    driver = webdriver.Chrome(service=service, options=options)
    logger.info(f"about to get: {ad['padmapper_url']}")
    driver.get(ad["padmapper_url"])
    time.sleep(2)
    byte_buffer = BytesIO()
    screenshot_bytes = driver.get_screenshot_as_png()
    byte_buffer.write(screenshot_bytes)
    logger.info(f"BytesIO: {byte_buffer.getbuffer().nbytes}")
    bsize = byte_buffer.getbuffer().nbytes
    if bsize > 0:
        fname = os.path.join(
            "padmapper-data",
            ad["crawl_date"],
            ad["gaddress"].replace(" ", "_") + ".png",
        )
        s3 = boto3.client("s3")
        byte_buffer.seek(0)
        s3.upload_fileobj(
            byte_buffer, "rycpt-crawls", fname, ExtraArgs={"ContentType": "image/jpeg"}
        )
        response = s3.head_object(Bucket="rycpt-crawls", Key=fname)
        if "ContentLength" in response and response["ContentLength"] > 0:
            logger.info(
                f'success s3: {fname}. ContentLength: {response["ContentLength"]} bsize: {bsize}'
            )
            ad["screenshot"] = fname
        else:
            logger.info(
                f'failed s3: {fname}. ContentLength: {response["ContentLength"]} bsize: {bsize}'
            )
    driver.quit()
    return ad


def search_and_parse(la_city):
    url = f"https://www.padmapper.com/apartments/{la_city}-ca?property-categories=house&max-days=1&lease-term=long"
    logger.info(f"{la_city}\t{url}")
    html_content = get_and_scroll(url)
    soup = BeautifulSoup(html_content, "html.parser")

    list_item_container = soup.find(
        "div", class_=re.compile("list_listItemContainer.*")
    )
    if not list_item_container:
        logger.error("no list_item_container")
        return []

    list_items = list_item_container.find_all("div", class_=re.compile(".*noGutter.*"))
    ads = []
    for list_item in list_items:
        ad = {"la_city": la_city}
        ad["crawl_date"] = dt.today().date().isoformat()
        address = list_item.find("div", class_=re.compile(".*ListItemFull_address.*"))
        if not address:
            continue
        ad["address"] = address.get_text(strip=True)

        for infos in list_item.find_all(
            "div", class_=re.compile(".*ListItemFull_info.*")
        ):
            info3 = infos.find_all("span")
            if len(info3) != 3:
                continue
            ad["bedbath"] = info3[0].get_text(strip=True)
            ad["housetype"] = info3[1].get_text(strip=True)
            ad["hood"] = info3[2].get_text(strip=True)

        header_text = list_item.find(
            "a", class_=re.compile("ListItemFull_headerText.*")
        )
        if not header_text:
            continue
        ad["padmapper_url"] = "https://www.padmapper.com" + header_text["href"]

        price = list_item.find("span", class_=re.compile(".*ListItemFull_text.*"))
        if not price:
            continue
        ad["price"] = price.get_text()

        tax = geocode_and_assess(ad["address"] + " " + ad["hood"])
        ad.update(tax)

        if "CurrentRoll_LandValue" in tax and float(tax["CurrentRoll_LandValue"]) > 0.0:
            try:
                ad = screenshot_ad(ad)
            except:
                logger.exception("screenshot fail")

        ads.append(ad)

    # Write to db
    df = pd.DataFrame(ads)
    logger.info(f"df {la_city}: {df.shape}")
    df.to_sql("padmapper_ads", engine, if_exists="append", index=False)

    return ads


def main():
    #for la_city in ["long-beach", "los-angeles", "santa-monica", "culver-city"]:
    for la_city in LA_CITIES:
        city_ads = search_and_parse(la_city)
        if not city_ads:
            logger.info(f"Welcome to Dumpville: {la_city}")
            continue
        logger.info(f"Hits: {la_city} {len(city_ads)}")


if __name__ == "__main__":
    main()
