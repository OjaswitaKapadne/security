import os
import sys
from dotenv import load_dotenv
import certifi
import pandas as pd
import pymongo

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging

# Load environment variables
load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

# SSL certificate
ca = certifi.where()


## ETL Pipeline
class NetworkDataExtract():

    def __init__(self):
        try:
            pass
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ✅ Convert CSV → JSON (list of dicts)
    def csv_to_json_converter(self, file_path):
        try:
            print("📂 Reading CSV file...")

            data = pd.read_csv(file_path)
            data.reset_index(drop=True, inplace=True)

            # Convert to list of dictionaries
            records = data.to_dict(orient="records")

            print(f"✅ Total records extracted: {len(records)}")

            return records

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # ✅ Insert into MongoDB
    def insert_data_mongodb(self, records, database, collection):
        try:
            if not records:
                print("❌ No records found to insert")
                return 0

            print("🔌 Connecting to MongoDB...")

            client = pymongo.MongoClient(
                MONGO_DB_URL,
                tlsCAFile=ca
            )

            # Test connection
            client.admin.command('ping')
            print("✅ MongoDB connection successful")

            db = client[database]
            col = db[collection]

            print("📤 Inserting data into MongoDB...")

            result = col.insert_many(records)

            print(f"✅ Inserted {len(result.inserted_ids)} records")

            return len(result.inserted_ids)

        except Exception as e:
            raise NetworkSecurityException(e, sys)


# 🚀 MAIN EXECUTION
if __name__ == "__main__":
    try:
        FILE_PATH = r"Network_Data\phisingData.csv"   # ✅ fixed path
        DATABASE = "OJAI"
        COLLECTION = "NetworkData"

        print("🔍 Mongo URL:", MONGO_DB_URL)

        networkobj = NetworkDataExtract()

        # Step 1: Extract data
        records = networkobj.csv_to_json_converter(FILE_PATH)

        # Step 2: Insert into MongoDB
        no_of_records = networkobj.insert_data_mongodb(
            records, DATABASE, COLLECTION
        )

        print(f"\n🎯 Final inserted records: {no_of_records}")

    except Exception as e:
        raise NetworkSecurityException(e, sys)