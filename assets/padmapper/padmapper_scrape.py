import re
import os
import requests
import logging
import geocoder
import pandas as pd
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
            "gconfidence": g.confidence
        }
    tax = process_address(g.address)
    if tax is None:
        logger.error(f"No tax for {g.address}")
    else:
        out.update(tax)
    return out

def search_and_parse(la_city):
    url = f"https://www.padmapper.com/apartments/{la_city}-ca?property-categories=house&max-days=1&lease-term=long"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}

    response = requests.get(url, headers=headers)
    logger.info(f"{url} {response.status_code}")
    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')

    list_item_container = soup.find("div", class_=re.compile('list_listItemContainer.*'))

    if not list_item_container:
        logger.debug("no listItemContainer")
        return []

    list_items = list_item_container.find_all("div", class_=re.compile(".*noGutter.*"))
    ads = []

    for list_item in list_items:
        ad = {"la_city": la_city}
        ad['crawl_date'] = dt.today().isoformat()
        address = list_item.find("div", class_=re.compile(".*ListItemFull_address.*"))
        if not address:
            continue
        ad["address"] = address.get_text(strip=True)

        for infos in list_item.find_all("div", class_=re.compile(".*ListItemFull_info.*")):
            info3 = infos.find_all("span")
            if len(info3) != 3:
                logger.info("len(info3) != 3")
                continue
            ad["bedbath"] = info3[0].get_text(strip=True)
            ad["housetype"] = info3[1].get_text(strip=True)
            ad["hood"] = info3[2].get_text(strip=True)

        header_text = list_item.find('a', class_=re.compile("ListItemFull_headerText.*"))
        if not header_text:
            logger.debug("if not header_text")
            continue
        ad['padmapper_url'] = "https://www.padmapper.com" + header_text['href']

        price = list_item.find('span', class_=re.compile(".*ListItemFull_text.*"))
        if not price:
            logger.debug("if not price")
            continue
        ad['price'] = price.get_text()

        tax = geocode_and_assess(ad["address"] + " " + ad["hood"])
        ad.update(tax)

        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--single-process')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--user-data-dir=~/.config/google-chrome')
            options.add_argument('--window-size=1420,2080')
            options.add_argument('--profile-directory=Default')
            options.add_argument('--user-data-dir=~/.config/google-chrome')
            service=Service("/usr/local/bin/chromedriver")
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(ad['padmapper_url'])
            driver.save_screenshot(os.path.join(os.environ["HOME"], "padmapper-data",
                ad["crawl_date"]+"_"+
                ad['gaddress'].replace(" ", "_")+'.png'))
            driver.quit()
        except:
            logger.exception(f'screenshot fail {ad["padmapper_url"]}')

        ads.append(ad)

    return ads


LA_CITIES = ["whittier",
"westlake-village",
"west-hollywood",
"west-covina",
"walnut",
"vernon",
"torrance",
"temple-city",
"south-pasadena",
"south-gate",
"south-el-monte",
"signal-hill",
"sierra-madre",
"santa-monica",
"santa-fe-springs",
"santa-clarita",
"san-marino",
"san-gabriel",
"san-fernando",
"san-dimas",
"rosemead",
"rolling-hills-estates",
"rolling-hills",
"redondo-beach",
"rancho-palos-verdes",
"pomona",
"pico-rivera",
"pasadena",
"paramount",
"palos-verdes-estates",
"palmdale",
"norwalk",
"monterey-park",
"montebello",
"monrovia",
"maywood",
"manhattan-beach",
"malibu",
"lynwood",
"los-angeles",
"long-beach",
"lomita",
"lawndale",
"lancaster",
"lakewood",
"la-verne",
"la-puente",
"la-mirada",
"la-habra-heights",
"la-cañada-flintridge",
"irwindale",
"inglewood",
"industry",
"huntington-park",
"hidden-hills",
"hermosa-beach",
"hawthorne",
"hawaiian-gardens",
"glendora",
"glendale",
"gardena",
"el-segundo",
"el-monte",
"duarte",
"downey",
"diamond-bar",
"culver-city",
"cudahy",
"covina",
"compton",
"commerce",
"claremont",
"cerritos",
"carson",
"calabasas",
"burbank",
"bradbury",
"beverly-hills",
"bellflower",
"bell-gardens",
"bell",
"baldwin-park",
"azusa",
"avalon",
"artesia",
"arcadia",
"alhambra",
"agoura-hills"]

def main():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--window-size=1220,1480')
    service=Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.padmapper.com/apartments/14815827p/1-bedroom-1-bath-apartment-at-2015-e-broadway-long-beach-ca-90803")
    driver.save_screenshot(os.path.join(os.environ["HOME"], "padmapper-data","asd.png"))
    driver.quit()

    ads = []
    for la_city in LA_CITIES:
        city_ads = search_and_parse(la_city)
        if not city_ads:
            logger.info(f"Welcome to Dumpville: {la_city}")
            continue

        logger.info(f"Hits: {la_city} {len(city_ads)}")
        ads.extend(city_ads)
    df = pd.DataFrame(ads)
    df.to_sql("padmapper_ads", engine, if_exists="append", index=False)

if __name__ == "__main__":
    main()
