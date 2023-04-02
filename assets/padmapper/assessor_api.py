#!/usr/bin/env python
# coding: utf-8

import logging
import os
import requests
import urllib.parse
import usaddress
import geocoder
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

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def usaddress_match(left, right):
    match_fields = ("AddressNumber", "StreetName", "PlaceName", "StateName")
    zip_field = "ZipCode"
    for match_field in match_fields:
        if (match_field not in left[0]) or (match_field not in right[0]):
            return False
        if (left[0][match_field].lower() != right[0][match_field].lower()):
            return False
    if (zip_field not in left[0]) or (zip_field not in right[0]):
        return False
    if left[0][zip_field][0:5] != right[0][zip_field][0:5]:
        return False
    return True


# Get AIN from address. Input address must match Google geocoder address exactly.
def fetch_address_ain(address, try_google=False):
    logger.debug(f"fetchAIN: {address}")
    url_base = "https://portal.assessor.lacounty.gov/api/search?search="
    final_url = url_base + urllib.parse.quote(address)
    logger.info(f"searching: {final_url}")
    r = requests.get(final_url, headers=headers, proxies=proxies, verify=False)
    srpj = r.json()
    try:
        parsed_input = usaddress.tag(address)
    except usaddress.RepeatedLabelError:
        return
    matches = []

    #Check 1st result only.
    parcel = srpj["Parcels"][0]

    parcel_address = f'{parcel["SitusStreet"]}, {parcel["SitusCity"]}, {parcel["SitusZipCode"]}'
    parsed_assessor_data = usaddress.tag(parcel_address)
    if usaddress_match(parsed_input, parsed_assessor_data):
        return parcel["AIN"]

    if not try_google:
        return
    logger.info(f"Fallback to Google API for: {parcel_address}")
    g = geocoder.google(parcel_address, key=GOOGLE_MAPS_API_KEY)
    if not g.ok:
        logging.error(g.json)
        return
    logger.info(f"Google found: {g.address}")
    parsed_google = usaddress.tag(g.address)
    if usaddress_match(parsed_input, parsed_google):
        logger.info(f'After Google we matched {g.address} to AIN: {parcel["AIN"]}')
        return parcel["AIN"]
    return





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


#address is assumed to be google geocoder output.
def process_address(address):
    ain = fetch_address_ain(address, try_google=True)
    if ain is None:
        logger.info(f"No AIN for: {address}")
        return
    deets = fetch_ain_details(ain)
    if deets is None:
        return
    deets["gAddress"] = address
    return deets

