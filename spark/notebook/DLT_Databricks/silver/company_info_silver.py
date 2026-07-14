import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="company_silver",
    comment="Cleaned company dimension data"
)
@dlt.expect(
    "valid_symbol",
    "symbol IS NOT NULL"
)
@dlt.expect(
    "valid_market_cap",
    "market_cap > 0"
)
def company_silver():


    return (

        spark.read.table("`jarvis-catalog`.bronze.company_bronze")


        # Rename columns

        .withColumnRenamed(
            "Symbol",
            "symbol"
        )

        .withColumnRenamed(
            "OfficialSite",
            "official_site"
        )
        .withColumnRenamed(
            "Name",
            "company_name"
        )

        .withColumnRenamed(
            "MarketCapitalization",
            "market_cap"
        )

        .withColumnRenamed(
            "PERatio",
            "pe_ratio"
        )

        .withColumnRenamed(
            "PEGRatio",
            "peg_ratio"
        )

        .withColumnRenamed(
            "RevenueTTM",
            "revenue_ttm"
        )

        .withColumnRenamed(
            "GrossProfitTTM",
            "gross_profit_ttm"
        )

        .withColumnRenamed(
            "EBITDA",
            "ebitda"
        )

        .withColumnRenamed(
            "Beta",
            "beta"
        )

        .withColumnRenamed(
            "52WeekHigh",
            "week_52_high"
        )

        .withColumnRenamed(
            "52WeekLow",
            "week_52_low"
        )

        .withColumnRenamed(
            "50DayMovingAverage",
            "moving_avg_50"
        )

        .withColumnRenamed(
            "200DayMovingAverage",
            "moving_avg_200"
        )


        # Numeric conversions

        .withColumn(
            "market_cap",
            F.col("market_cap").cast("long")
        )

        .withColumn(
            "revenue_ttm",
            F.col("revenue_ttm").cast("long")
        )

        .withColumn(
            "gross_profit_ttm",
            F.col("gross_profit_ttm").cast("long")
        )

        .withColumn(
            "ebitda",
            F.col("ebitda").cast("long")
        )


        .withColumn(
            "pe_ratio",
            F.col("pe_ratio").cast("double")
        )

        .withColumn(
            "peg_ratio",
            F.col("peg_ratio").cast("double")
        )


        .withColumn(
            "eps",
            F.col("EPS").cast("double")
        )


        .withColumn(
            "beta",
            F.col("beta").cast("double")
        )


        .withColumn(
            "week_52_high",
            F.col("week_52_high").cast("double")
        )


        .withColumn(
            "week_52_low",
            F.col("week_52_low").cast("double")
        )


        .withColumn(
            "moving_avg_50",
            F.col("moving_avg_50").cast("double")
        )


        .withColumn(
            "moving_avg_200",
            F.col("moving_avg_200").cast("double")
        )


        # Date columns

        .withColumn(
            "latest_quarter",
            F.to_date("LatestQuarter")
        )

        .withColumn(
            "dividend_date",
            F.to_date("DividendDate")
        )

        .withColumn(
            "ex_dividend_date",
            F.to_date("ExDividendDate")
        )


        # Keep analytics columns

        .select(

            "symbol",
            "company_name",

            "exchange",
            "currency",
            "country",

            "sector",
            "industry",

            "market_cap",

            "pe_ratio",
            "peg_ratio",

            "eps",

            "revenue_ttm",
            "gross_profit_ttm",
            "ebitda",

            "beta",

            "week_52_high",
            "week_52_low",

            "moving_avg_50",
            "moving_avg_200",

            "latest_quarter",

            "dividend_date",
            "ex_dividend_date",

            "official_site",

            "_bronze_ingestion_timestamp"

        )

        .dropDuplicates(
            ["symbol"]
        )

    )