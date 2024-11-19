from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window, avg, count
from pyspark.sql.types import StructType, StructField, StringType, FloatType, IntegerType

def main():
    # Δημιουργία SparkSession με υποστήριξη Kafka
    spark = SparkSession.builder \
        .appName("KafkaSparkVehicleDataProcessing") \
        .getOrCreate()
    #spark.sql("select version()").show()
    print(f'The PySpark {spark.version} version is running...')
    spark.sparkContext.setLogLevel("WARN")  # Μειώστε τα logs αν χρειάζεται

    # Ορισμός του σχήματος για τα εισερχόμενα JSON δεδομένα
    vehicle_schema = StructType([
        StructField("id", StringType(), True),
        StructField("dn", StringType(), True),
        StructField("orig", StringType(), True),
        StructField("dest", StringType(), True),
        StructField("t", IntegerType(), True),
        StructField("link", StringType(), True),
        StructField("x", FloatType(), True),
        StructField("s", FloatType(), True),
        StructField("v", FloatType(), True),
        StructField("timestamp", StringType(), True)  # Χρονική σφραγίδα αποστολής
    ])

    # Κατανάλωση δεδομένων από το Kafka topic
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "hostname:9092")\
        .option("subscribe", "vehiclePositions")\
        .option("startingOffsets", "earliest")\
        .load()

    # Μετατροπή των binary messages σε string και αποσυσκευασία του JSON
    vehicle_df = kafka_df.selectExpr("CAST(value AS STRING) as json_str") \
        .select(from_json(col("json_str"), vehicle_schema).alias("data")) \
        .select("data.*")

    # Επεξεργασία των δεδομένων για υπολογισμό vcount και vspeed
    processed_df = vehicle_df.groupBy("t", "link") \
        .agg(
            count("id").alias("vcount"),
            avg("v").alias("vspeed")
        ) \
        .withColumnRenamed("t", "time")

    # Επιλογή των απαιτούμενων πεδίων
    final_df = processed_df.select("time", "link", "vcount", "vspeed")

    # Καθορισμός του τρόπου εξόδου (console για αυτό το παράδειγμα)
    query = final_df.writeStream \
        .outputMode("complete") \
        .format("console") \
        .option("truncate", "false") \
        .start()

    # Αναμονή για το τέλος της διαδικασίας streaming
    query.awaitTermination()

if __name__ == "__main__":
    main()
