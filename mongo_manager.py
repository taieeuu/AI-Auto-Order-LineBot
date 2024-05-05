from pymongo import MongoClient

class MongoDBManager:
  def __init__(self, uri, dbname):
    self.client = MongoClient(uri)
    self.db = self.client[dbname]

  def insert_document(self, collection_name, document):
    return self.db[collection_name].insert_one(document)

  def find_document(self, collection_name, query):
    return self.db[collection_name].find(query)

  def update_document(self, collection_name, query, new_values):
    return self.db[collection_name].update_one(query, {'$set': new_values})

  def delete_document(self, collection_name, query):
    return self.db[collection_name].delete_one(query)
