import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dlt.materialized_view(
    name="gold_price_trends",
    comment="Price trend analytics"
)
def gold_price_trends():

    quotes = spark.read.table("`jarvis-catalog`.silver.quote_silver")
    companies = spark.read.table("`jarvis-catalog`.silver.company_silver")

    w = Window.partitionBy("symbol").orderBy("trade_date")

    w7 = w.rowsBetween(-6, 0)
    w30 = w.rowsBetween(-29, 0)
    w90 = w.rowsBetween(-89, 0)

    return (
        quotes

        .join(
            companies.select(
                "symbol",
                "company_name",
                "sector",
                "industry",
                "market_cap"
            ),
            "symbol",
            "left"
        )

        # Previous day's closing price
        .withColumn(
            "previous_close",
            F.lag("close").over(w)
        )

        # Daily price change
        .withColumn(
            "daily_price_change",
            F.col("close") - F.col("previous_close")
        )

        # Daily %
        .withColumn(
            "daily_price_change_percent",
            (
                (F.col("close") - F.col("previous_close"))
                / F.col("previous_close")
            ) * 100
        )

        # Moving averages
        .withColumn(
            "ma_7",
            F.avg("close").over(w7)
        )

        .withColumn(
            "ma_30",
            F.avg("close").over(w30)
        )

        .withColumn(
            "ma_90",
            F.avg("close").over(w90)
        )
    )