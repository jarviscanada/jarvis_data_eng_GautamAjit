import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window


@dlt.materialized_view(
    name="gold_volume_trends",
    comment="Volume trend analytics"
)
def gold_volume_trends():

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
                "industry"
            ),
            "symbol",
            "left"
        )

        .withColumn(
            "avg_volume_7",
            F.avg("volume").over(w7)
        )

        .withColumn(
            "avg_volume_30",
            F.avg("volume").over(w30)
        )

        .withColumn(
            "avg_volume_90",
            F.avg("volume").over(w90)
        )

        .withColumn(
            "volume_change",
            F.col("volume") - F.lag("volume").over(w)
        )

        .withColumn(
            "volume_change_percent",
            (
                (
                    F.col("volume") - F.lag("volume").over(w)
                )
                / F.lag("volume").over(w)
            ) * 100
        )
    )