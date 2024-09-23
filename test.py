from dotenv import load_dotenv
from pymongo import MongoClient, errors
import logging

load_dotenv()

MONGO_URI = "mongodb+srv://adesidaadebola1:Pheonix148%24%24@cluster0.xew48.mongodb.net/Cluster0?retryWrites=true&w=majority"
DATABASE_NAME = "test_database"
COLLECTION_NAME = "test_collection"

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def connect_to_mongo():
    try:
        print("Connecting to MongoDB...")
        return MongoClient(MONGO_URI, serverSelectionTimeoutMS=60000)
    except errors.ConnectionFailure as e:
        logging.error("MongoDB connection error:", e)
        print("MongoDB connection error:", e)
        return None

def create_collection(client, db_name, collection_name):
    try:
        print("Creating collection...")
        return client[db_name][collection_name]
    except errors.CollectionInvalid as e:
        logging.error("Collection invalid:", e)
        print("Collection invalid:", e)
        return None

def perform_crud_operations(collection):
    print("Performing CRUD operations...")
    data = {'name': 'John Doe', 'age': 30}

    try:
        result = collection.insert_one(data)
        print("Insert result:", result.inserted_id)
        logging.info(f"Insert result: {result.inserted_id}")

        document = collection.find_one({'name': 'John Doe'})
        if document:
            print("Document found:", document)
            logging.info(f"Document: {document}")
        else:
            print("Document not found")
            logging.info("Document not found")

        update_result = collection.update_one({'name': 'John Doe'}, {'$set': {'age': 31}})
        print("Update result:", update_result.modified_count)
        logging.info(f"Update result: {update_result.modified_count}")

        delete_result = collection.delete_one({'name': 'John Doe'})
        print("Delete result:", delete_result.deleted_count)
        logging.info(f"Delete result: {delete_result.deleted_count}")

    except errors.WriteError as e:
        logging.error("Write error:", e)
        print("Write error:", e)
    except errors.BulkWriteError as e:
        logging.error("Bulk write error:", e)
        print("Bulk write error:", e)

def main():
    client = connect_to_mongo()
    if client:
        print("Connected to MongoDB")
        collection = create_collection(client, DATABASE_NAME, COLLECTION_NAME)
        if collection is not None:
            perform_crud_operations(collection)
        client.close()
        print("Script executed successfully.")
    else:
        print("Failed to connect to MongoDB.")

if __name__ == "__main__":
    main()
