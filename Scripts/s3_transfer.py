# -*- coding: utf-8 -*-
"""S3 transfer.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/151VGRlo0rySLSdazynDg--ZzHaRMHjgD
"""

import pandas as pd
import boto3
from boto3.s3.transfer import S3Transfer
import os
from io import BytesIO
import findspark
findspark.init()
import shutil

from pyspark import SparkConf, SparkContext
from pyspark.sql import DataFrame
from pyspark.sql import SparkSession
from pyspark.sql.functions import expr
from pyspark.sql.functions import col, when, lit, count, sum, avg, max, datediff, current_date
from pyspark.sql.functions import *

#  Spark configuration and context
spark_con = SparkSession.builder.appName("Olist-ETL").getOrCreate()
from pyspark.sql import SQLContext
sqlContext = SQLContext(spark_con)
spark_con.conf.set("spark.sql.execution.arrow.enabled", "true")

# Personal AWS credentials
AWS_ACCESS_KEY_ID = 'AKIATTS7E5DTF3IHFRV3'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = 'us-east-1'
bucket_name = "ecommercelogistics"

# S3 resource setup
s3_files = boto3.resource(
    service_name='s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

s3_files.create_bucket(Bucket=bucket_name)
print("Objects in S3 bucket:")

bucket = s3_files.Bucket(bucket_name)

for obj in bucket.objects.all():
    print(obj.key)

def get_dfname(df):
    name =[xi for xi in globals() if globals()[xi] is df][0]
    return name

def csv_export(dataframe: DataFrame):
    df_name = get_dfname(dataframe)
    output_dir = "/content/kpi"

    temp_dir = f"{output_dir}/temp_{df_name}"
    output_file = f"{output_dir}/{df_name}.csv"

    # Coalesce to single partition
    dataframe.coalesce(1).write.option("header", "true").csv(temp_dir)

    temp_file = [file for file in os.listdir(temp_dir) if file.startswith("part-")][0]
    shutil.move(f"{temp_dir}/{temp_file}", output_file)

    # Remove the temporary directory
    shutil.rmtree(temp_dir)
    print(f"CSV file created at: {output_file}")

dff_items = spark_con.read.csv("olist_order_items_dataset.csv",header=True,inferSchema=True)
dff_orders = spark_con.read.csv("olist_orders_dataset.csv",header=True,inferSchema=True)
dff_products = spark_con.read.csv('olist_products_dataset.csv',header=True,inferSchema=True)
dff_customers = spark_con.read.csv("olist_customers_dataset.csv", header=True, inferSchema=True)
dff_payments = spark_con.read.csv("olist_order_payments_dataset.csv", header=True, inferSchema=True)
dff_reviews = spark_con.read.csv("olist_order_reviews_dataset.csv", header=True, inferSchema=True)
dff_geolocation = spark_con.read.csv("olist_geolocation_dataset.csv", header=True, inferSchema=True)
dff_sellers = spark_con.read.csv("olist_sellers_dataset.csv", header=True, inferSchema=True)

dff_items.head()

# Create SQL Tables from dfs
dff_items.createOrReplaceTempView('items')
dff_orders.createOrReplaceTempView('orders')
dff_products.createOrReplaceTempView('products')
dff_customers.createOrReplaceTempView('customers')
dff_payments.createOrReplaceTempView('payments')
dff_reviews.createOrReplaceTempView('reviews')
dff_geolocation.createOrReplaceTempView('geolocation')
dff_sellers.createOrReplaceTempView('sellers')

#tranfer_s3.py
def upload_to_s3(bucket_name, folder_path, s3_prefix=""):
    s3_client = boto3.client('s3')
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, folder_path)
            s3_path = os.path.join(s3_prefix, relative_path).replace("\\", "/")

            s3_client.upload_file(local_path, bucket_name, s3_path)
            print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_path}")


folder_path = '/content/kpi'
s3_prefix = 'logistics'

upload_to_s3(bucket_name, folder_path, s3_prefix)