import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    MapType
)


QUOTE_TABLES = [
    "`jarvis-catalog`.landing.quote_ibm",
    "`jarvis-catalog`.landing.quote_msft",
    "`jarvis-catalog`.landing.quote_aapl",
    "`jarvis-catalog`.landing.quote_ba"
]


# JSON schema
daily_schema = StructType([
    
    StructField(
        "Meta Data",
        StructType([
            StructField(
                "2. Symbol",
                StringType()
            ),
            StructField(
                "3. Last Refreshed",
                StringType()
            )
        ])
    ),

    StructField(
        "Time Series (Daily)",
        MapType(
            StringType(),
            MapType(
                StringType(),
                StringType()
            )
        )
    )
])



@dlt.table(
    name="quote_bronze",
    comment="Historical daily stock prices from Alpha Vantage"
)
def quote_bronze():


    # Read landing tables
    dfs = [
        spark.read.table(table)
        for table in QUOTE_TABLES
    ]


    df = dfs[0]

    for next_df in dfs[1:]:
        df = df.unionByName(next_df)



    # Parse JSON
    parsed_df = (
        df
        .withColumn(
            "json_data",
            F.from_json(
                F.col("raw_json"),
                daily_schema
            )
        )
    )



    # Extract time series map
    exploded_df = (
        parsed_df

        .select(
            "symbol",

            F.explode(
                F.col(
                    "json_data.`Time Series (Daily)`"
                )
            )
            .alias(
                "trade_date",
                "daily_values"
            )
        )
    )



    return (

        exploded_df

        .select(

            "symbol",

            F.col("trade_date"),


            F.col(
                "daily_values.`1. open`"
            )
            .alias("open"),


            F.col(
                "daily_values.`2. high`"
            )
            .alias("high"),


            F.col(
                "daily_values.`3. low`"
            )
            .alias("low"),


            F.col(
                "daily_values.`4. close`"
            )
            .alias("close"),


            F.col(
                "daily_values.`5. volume`"
            )
            .alias("volume"),


            F.current_timestamp()
            .alias("_bronze_ingestion_timestamp")

        )
    )