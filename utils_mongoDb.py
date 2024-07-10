from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
load_dotenv()


DEFAULT_CONNECTION_STRING = os.getenv("CONNECTION_STRING")
DEFAULT_DBNAME = os.getenv("MONGODD_NAME")
DEFAULT_COLLECTION_NAME= os.getenv("COLLECTION_NAME")



class MongoDBUtils():

    def __init__(
        self, connection_string: str = DEFAULT_CONNECTION_STRING, database_name: str = DEFAULT_DBNAME, collection_name: str = DEFAULT_COLLECTION_NAME):
        try:
            self.client: MongoClient = MongoClient(connection_string)
        except errors.ConnectionFailure as error:
            print(error)       
        
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
    # Read (Find)
    def read_documents(self):
        print("All Documents:")
        for item in self.collection.find():
            print(item)

    # Delete
    def delete_document(self, query):
        result = self.collection.delete_one(query)
        print(f"Deleted {result.deleted_count} document")
    
    def delete_conversation_by_session_id(self, session_id):
        query = {"SessionId": session_id}
        result = self.collection.delete_many(query)
        print(f"Deleted {result.deleted_count} documents for SessionId: {session_id}")
    def delete_all_conversations(self):
        result = self.collection.delete_many({})
        print(f"Deleted all documents. Total count: {result.deleted_count}")


    
    def get_unique_session_ids(self):
        unique_session_ids = self.collection.distinct("SessionId")
        print("unique_session_ids", unique_session_ids)
        return unique_session_ids

if __name__ == "__main__":
    db_utils = MongoDBUtils()
    db_utils.get_unique_session_ids()
