import os
import pandas as pd
import seaborn as sns
import logging
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

FORMAT = "%(asctime)-15s %(levelname)-6s %(message)s"
DATE_FORMAT = "%b %d %H:%M:%S"
formatter = logging.Formatter(fmt=FORMAT, datefmt=DATE_FORMAT)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
fhandler = logging.FileHandler(
    os.path.join(os.environ["HOME"], "padmapper-data/gitlog.log")
)
fhandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.addHandler(fhandler)
logger.setLevel(logging.INFO)

conn_str = os.getenv("CRAIGGER_CONN")  # make sure the tunnel is open
engine = create_engine(conn_str)


def query_db():
    df = pd.read_sql(
        """SELECT
  "gaddress",
  replace(
    replace(price, '$', ''),
    ',',
    ''
  ):: numeric AS current_rent,
  "glat" :: numeric,
  "glng" :: numeric,
  "bedbath",
  "NumOfBeds",
  "screenshot",
  "NumOfBaths",
  coalesce(
    nullif("SqftMain", ''),
    '0.00'
  ):: numeric(10, 2) AS sqft,
  "BaseValue_Year",
  "AIN",
  "CurrentRoll_BaseYear",
  "CurrentRoll_LandValue" :: numeric + "CurrentRoll_ImpValue" :: numeric AS current_assessment
FROM
  "padmapper_ads"
WHERE
  "UseType" = 'Single Family Residence'
  AND "SqftMain" IS NOT NULL
  AND "NumOfBeds" != ''
  AND "NumOfBaths" != '';
  """,
        con=engine,
    )
    df["rent_per_sqft"] = df["current_rent"] / df["sqft"]
    df["assessment_per_sqft"] = df["current_assessment"] / df["sqft"]
    df = df[df["assessment_per_sqft"] > 1]
    df["assessment_to_rent_ratio"] = df["current_assessment"] / df["current_rent"]
    df["years_held"] = df["CurrentRoll_BaseYear"].map(int) - df["BaseValue_Year"].map(
        int
    )
    df = df.drop_duplicates().dropna()
    df["screenshot"] = (
        "https://rycpt-crawls.s3.us-west-2.amazonaws.com/" + df["screenshot"]
    )
    df["lagov"] = "https://portal.assessor.lacounty.gov/parceldetail/" + df["AIN"]
    logger.info(df.shape)
    return df


def plot_scatter(df):
    sns.set_theme(style="whitegrid")
    sns.set_context("paper")

    cmap = sns.color_palette("coolwarm", as_cmap=True)

    g = sns.relplot(
        data=df,
        x="assessment_per_sqft",
        y="rent_per_sqft",
        hue="years_held",
        linewidth=0,
        alpha=0.7,
        palette=cmap,
    )
    g.despine(left=True, bottom=True)
    plt.suptitle(
        "Rent per sqft vs. Tax Assessment per sqft\nPadmapper rental ads in Los Angeles"
    )
    output = os.path.join(
        os.environ["HOME"], "ryancompton.net/assets/pix/tax_vs_rent_padmapper.png"
    )
    print("output!", output)
    plt.savefig(output)


def write_tsv(df):
    hex_cmap = sns.color_palette("coolwarm", n_colors=len(set(df.years_held))).as_hex()

    def get_color(x):
        for idx, years in enumerate(sorted(set(df.years_held))):
            if x == years:
                return hex_cmap[max(0, idx)]

    df["gmap_color"] = df["years_held"].map(get_color)
    df["assessment_to_rent_ratio"] = df["assessment_to_rent_ratio"].round(2)
    dfp = df[
        [
            "glat",
            "glng",
            "gmap_color",
            "gaddress",
            "current_rent",
            "current_assessment",
            "assessment_to_rent_ratio",
            "BaseValue_Year",
            "lagov",
            "screenshot",
        ]
    ]
    dfp.to_csv(
        os.path.join(os.environ["HOME"], "ryancompton.net/assets/taxrentlocations.tsv"),
        sep="\t",
        index=False,
    )
    logger.info("wrote tsv")


def main():
    df = query_db()
    logger.info("df shape {}".format(df.shape))
    plot_scatter(df)
    write_tsv(df)


if __name__ == "__main__":
    main()
