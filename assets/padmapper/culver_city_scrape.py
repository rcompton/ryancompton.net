import os
import pandas as pd
import geocoder
import logging
from sqlalchemy import create_engine
from assessor_api import process_address

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

conn_str = os.getenv("CRAIGGER_CONN")  # make sure the tunnel is open
engine = create_engine(conn_str)


def geocode_and_assess(padmapper_address):
    # try:
    #    g = geocoder.google(padmapper_address, key=GOOGLE_MAPS_API_KEY)
    # except:
    #    logger.exception(padmapper_address)
    # if not g.ok:
    #    logging.error(g.json)

    # out = {
    #    "gaddress": g.address,
    #    "gquality": g.quality,
    #    "glat": g.lat,
    #    "glng": g.lng,
    #    "gzip": g.postal,
    #    "gconfidence": g.confidence,
    # }
    # cleaned_address = g.address

    out = {}
    cleaned_address = padmapper_address  # skip Google
    tax = process_address(cleaned_address, try_google=False)
    if tax is None:
        logger.error(f"No tax for {padmapper_address}")
    else:
        out.update(tax)
    return out


def main():
    sheet_name = os.path.join(
        os.environ["HOME"],
        "ryancompton.net",
        "assets",
        "culver_city",
        "responsive_record.xlsx",
    )
    df = pd.read_excel(sheet_name)
    logger.info(df.sample(20))
    df["AddressLineSum"] = (
        df["AddressLine1"].map(str) + ", " + df["AddressLine2"].map(str)
    )
    unique_addresses = list(set(df["AddressLineSum"]))
    logger.info(len(unique_addresses))
    assessments = []
    for address_line_sum in unique_addresses:
        try:
            assessment = geocode_and_assess(address_line_sum)
            assessment["AddressLineSum"] = address_line_sum
            assessments.append(assessment)
        except:
            logger.exception(address_line_sum)
    dfa = pd.DataFrame(assessments)
    print(dfa.sample(10))
    dfa.to_sql("culver_city_rental_tax", engine, if_exists="replace", index=False)


if __name__ == "__main__":
    main()
