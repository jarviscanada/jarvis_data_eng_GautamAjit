import dlt
from pyspark.sql import functions as F


@dlt.table(
    name="quote_silver",
    comment="Cleaned historical stock price data"
)
@dlt.expect("valid_symbol", "symbol IS NOT NULL")
@dlt.expect("valid_trade_date", "trade_date IS NOT NULL")
@dlt.expect("positive_close_price", "close > 0")
@dlt.expect("positive_volume", "volume >= 0")
def quote_silver():

    return (

        spark.read.table("`jarvis-catalog`.bronze.quote_bronze")


        # Standardize symbol
        .withColumn(
            "symbol",
            F.upper(F.col("symbol"))
        )


        # Convert data types
        .withColumn(
            "trade_date",
            F.to_date("trade_date")
        )

        .withColumn(
            "open",
            F.col("open").cast("double")
        )

        .withColumn(
            "high",
            F.col("high").cast("double")
        )

        .withColumn(
            "low",
            F.col("low").cast("double")
        )

        .withColumn(
            "close",
            F.col("close").cast("double")
        )

        .withColumn(
            "volume",
            F.col("volume").cast("long")
        )


        # Derived metrics
        .withColumn(
            "daily_price_change",
            F.col("close") - F.col("open")
        )


        .withColumn(
            "daily_return_percent",
            (
                (
                    F.col("close") - F.col("open")
                )
                /
                F.col("open")
            ) * 100
        )


        .withColumn(
            "daily_range",
            F.col("high") - F.col("low")
        )


        .withColumn(
            "daily_range_percent",
            (
                (
                    F.col("high") - F.col("low")
                )
                /
                F.col("low")
            ) * 100
        )


        # Select final silver columns
        .select(

            "symbol",

            "trade_date",

            "open",
            "high",
            "low",
            "close",

            "volume",

            "daily_price_change",
            "daily_return_percent",

            "daily_range",
            "daily_range_percent",

            "_bronze_ingestion_timestamp"

        )


        # Remove duplicate daily records
        .dropDuplicates(
            [
                "symbol",
                "trade_date"
            ]
        )

    )