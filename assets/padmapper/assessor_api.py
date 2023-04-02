#!/usr/bin/env python
# coding: utf-8

import logging
import os
import requests
import urllib.parse
import usaddress
from urllib3.exceptions import InsecureRequestWarning

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}
proxies = {}
# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


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
logger.info("starting new scrape!")


def fetch_address_ain(address):
    url_base = "https://portal.assessor.lacounty.gov/api/search?search="
    final_url = url_base + urllib.parse.quote(address)
    logger.info(f"searching: {final_url}")
    r = requests.get(final_url, headers=headers, proxies=proxies, verify=False)
    srpj = r.json()
    try:
        parsed_query = usaddress.tag(address)
    except usaddress.RepeatedLabelError:
        return
    match_fields = ("AddressNumber", "StreetName", "PlaceName", "StateName")
    zip_field = "ZipCode"
    matches = []
    for parcel in srpj["Parcels"]:
        try:
            parsed_result = usaddress.tag(
                f'{parcel["SitusStreet"]}, {parcel["SitusCity"]}, {parcel["SitusZipCode"]}'
            )
        except usaddress.RepeatedLabelError:
            continue
        if parsed_query[1] != parsed_result[1]:
            continue
        matched = True
        for match_field in match_fields:
            if (match_field not in parsed_query[0]) or (
                match_field not in parsed_result[0]
            ):
                matched = False
                continue
            if (
                parsed_query[0][match_field].lower()
                != parsed_result[0][match_field].lower()
            ):
                matched = False
                continue
        if (zip_field not in parsed_query[0]) or (zip_field not in parsed_result[0]):
            matched = False
            continue
        if parsed_query[0][zip_field][0:5] != parsed_result[0][zip_field][0:5]:
            matched = False
            continue
        if matched:
            parsed_result[0]["AIN"] = parcel["AIN"]
            matches.append(parsed_result[0])
    if len(matches) != 1:
        return
    return matches[0]["AIN"]


def fetch_ain_details(ain):
    url_base = "https://portal.assessor.lacounty.gov/api/parceldetail?ain="
    final_url = url_base + ain
    logger.info(f"parcel details: {final_url}")
    r = requests.get(final_url, headers=headers, proxies=proxies, verify=False)
    pdj = r.json()
    try:
        pdj = pdj["Parcel"]
    except KeyError:
        logger.info("no Parcel")
        return
    try:
        if len(pdj["SubParts"]) != 1:
            logger.info("len(pdj['SubParts']:" + str(len(pdj["SubParts"])))
            return
    except KeyError:
        logger.info("no SubParts")
        return
    out = {}
    kept_fields = (
        "AIN",
        "Longitude",
        "Latitude",
        "UseType",
        "SqftMain",
        "SqftLot",
        "NumOfBeds",
        "NumOfBaths",
        "RollPreparation_BaseYear",
        "RollPreparation_LandValue",
        "RollPreparation_ImpValue",
        "RollPreparation_LandReasonCode",
        "RollPreparation_ImpReasonCode",
        "RollPreparation_LandBaseYear",
        "RollPreparation_ImpBaseYear",
        "CurrentRoll_BaseYear",
        "CurrentRoll_LandValue",
        "CurrentRoll_ImpValue",
        "CurrentRoll_LandBaseYear",
        "CurrentRoll_ImpBaseYear",
        "TrendedBaseValue_Land",
        "TrendedBaseValue_Imp",
        "BaseValue_Land",
        "BaseValue_Imp",
        "BaseValue_Year",
        "UseCode1stDigit",
        "UseCode2ndDigit",
        "UseCode3rdDigit",
        "UseCode4thDigit",
        "UsableSqftLot",
    )
    for kept_field in kept_fields:
        if kept_field in pdj:
            out[kept_field] = pdj[kept_field]
        else:
            logger.info("pdj missing: " + kept_field)
    return out


def process_address(address):
    ain = fetch_address_ain(address)
    if ain is None:
        logger.info(f"No AIN for: {address}")
        return
    deets = fetch_ain_details(ain)
    if deets is None:
        return
    deets["gAddress"] = address
    return deets


# def main():
#    logger.info("query the postpostprocessed db...")
#    dfrent = pd.read_sql(
#        "SELECT address from joined_results WHERE gconfidence >= 9 AND netloc = 'losangeles.craigslist.org'",
#        engine,
#    )
#    logger.warning("dfrent.shape" + str(dfrent.shape))
#    addresses = set()
#    for idx, row in dfrent.iterrows():
#        addresses.add(row["address"])
#    results = []
#    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
#        for result in executor.map(process_address, addresses):
#            if result:
#                results.append(result)
#    df_taxes = pd.DataFrame(results)
#    print(df_taxes)
#    logger.info("df_taxes.to_sql...")
#    df_taxes.to_sql("tax_results", engine, if_exists="append", index=False)
#
#
# if __name__ == "__main__":
#    logger.info("starting new scrape! main")
#    main()
