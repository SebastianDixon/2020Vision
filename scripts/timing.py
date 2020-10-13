import pymongo
from pymongo import MongoClient
import time
import logging

client = MongoClient("mongodb://user:1234@cluster0-shard-00-00.dircn.gcp.mongodb.net:27017,cluster0-shard-00-01.dircn.gcp.mongodb.net:27017,cluster0-shard-00-02.dircn.gcp.mongodb.net:27017/parcel?ssl=true&replicaSet=atlas-jcizbw-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client["parcel"]
collection = db["timings"]

def timeit(time_type):
    def inner(fn):
        def _fn(*args):
            start_time = time.time()
            results = fn(*args)
            end_time = time.time()

            diff = end_time - start_time
            print(f'time to run {time_type} : {diff} seconds')

            val = collection.count()

            post = {"_id":val , "name": time_type, "time":diff}
            collection.insert_one(post)
            
            return results
        return _fn
    return inner

