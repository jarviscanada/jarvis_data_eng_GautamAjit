import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType


COMPANY_TABLES = [
    "`jarvis-catalog`.landing.company_aapl",
    "`jarvis-catalog`.landing.company_ibm",
    "`jarvis-catalog`.landing.company_msft",
    "`jarvis-catalog`.landing.company_ba"
]


# Raw JSON schema
company_schema = StructType([

    StructField("Symbol", StringType()),
    StructField("AssetType", StringType()),
    StructField("Name", StringType()),
    StructField("Description", StringType()),

    StructField("CIK", StringType()),

    StructField("Exchange", StringType()),
    StructField("Currency", StringType()),
    StructField("Country", StringType()),

    StructField("Sector", StringType()),
    StructField("Industry", StringType()),

    StructField("Address", StringType()),
    StructField("OfficialSite", StringType()),

    StructField("FiscalYearEnd", StringType()),
    StructField("LatestQuarter", StringType()),


    StructField("MarketCapitalization", StringType()),
    StructField("EBITDA", StringType()),

    StructField("PERatio", StringType()),
    StructField("PEGRatio", StringType()),

    StructField("BookValue", StringType()),
    StructField("DividendPerShare", StringType()),
    StructField("DividendYield", StringType()),

    StructField("EPS", StringType()),

    StructField("RevenuePerShareTTM", StringType()),

    StructField("ProfitMargin", StringType()),
    StructField("OperatingMarginTTM", StringType()),

    StructField("ReturnOnAssetsTTM", StringType()),
    StructField("ReturnOnEquityTTM", StringType()),

    StructField("RevenueTTM", StringType()),
    StructField("GrossProfitTTM", StringType()),

    StructField("DilutedEPSTTM", StringType()),

    StructField("QuarterlyEarningsGrowthYOY", StringType()),
    StructField("QuarterlyRevenueGrowthYOY", StringType()),

    StructField("AnalystTargetPrice", StringType()),

    StructField("AnalystRatingStrongBuy", StringType()),
    StructField("AnalystRatingBuy", StringType()),
    StructField("AnalystRatingHold", StringType()),
    StructField("AnalystRatingSell", StringType()),
    StructField("AnalystRatingStrongSell", StringType()),

    StructField("TrailingPE", StringType()),
    StructField("ForwardPE", StringType()),

    StructField("PriceToSalesRatioTTM", StringType()),
    StructField("PriceToBookRatio", StringType()),

    StructField("EVToRevenue", StringType()),
    StructField("EVToEBITDA", StringType()),

    StructField("Beta", StringType()),

    StructField("52WeekHigh", StringType()),
    StructField("52WeekLow", StringType()),

    StructField("50DayMovingAverage", StringType()),
    StructField("200DayMovingAverage", StringType()),

    StructField("SharesOutstanding", StringType()),
    StructField("SharesFloat", StringType()),

    StructField("PercentInsiders", StringType()),
    StructField("PercentInstitutions", StringType()),

    StructField("DividendDate", StringType()),
    StructField("ExDividendDate", StringType())
])



@dlt.table(
    name="company_bronze",
    comment="Raw company information flattened from Alpha Vantage"
)
def company_bronze():

    dfs = [
        spark.read.table(table)
        for table in COMPANY_TABLES
    ]


    df = dfs[0]

    for next_df in dfs[1:]:
        df = df.unionByName(next_df)


    return (

        df

        .withColumn(
            "company_data",
            F.from_json(
                F.col("raw_json"),
                company_schema
            )
        )


        .select(

            F.col("company_data.*"),

            F.current_timestamp()
            .alias("_bronze_ingestion_timestamp")

        )

    )