import VISION
import pymongo
from pymongo import MongoClient
import csv


client = MongoClient("mongodb://user:1234@cluster0-shard-00-00.dircn.gcp.mongodb.net:27017,cluster0-shard-00-01.dircn.gcp.mongodb.net:27017,cluster0-shard-00-02.dircn.gcp.mongodb.net:27017/parcel?ssl=true&replicaSet=atlas-jcizbw-shard-0&authSource=admin&retryWrites=true&w=majority")
db = client["parcel"]


def write_post():
    collection = db["postcode"]

    for i in range(10):
        post_data = VISION.text_region(i)
        parcel_name = post_data[1]
        codes = post_data[0]

        codes = list(dict.fromkeys(codes))
        
        print("POSTCODE(s):", codes)


        total = 0
        all_doc = collection.find()
        for _ in all_doc:
            total += 1


        if len(codes) > 1:
            post = {"_id":total, "name": parcel_name, "post1":codes[0], "post2":codes[1]}
        elif len(codes) == 0:
            post = {"_id":total, "name": parcel_name, "post1":"", "post2":""}
        else:
            post = {"_id":total, "name": parcel_name, "post1":codes[0], "post2":""}

        collection.insert_one(post)


def delete_post():
    collection = db["post_validation"]
    x = collection.delete_many({})
    print(x.deleted_count, " documents deleted.")


def get_csv():
    collection = db["post_validation"]
    total = collection.estimated_document_count()

    with open('C:/Users/Sebastian Dixon/Downloads/codepo_gb/Data/CSV/al.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')

        for row in readCSV:
            total+=1
            post = row[0]

            post = {"_id":total, "postcode":post}
            collection.insert_one(post)

    print("done")


def accuracy():
    matched = 0
    
    col1 = db["postcode"]
    col2 = db["human_read"]

    total = col1.estimated_document_count()
    
    vision_doc = col1.find()

    for doc1 in vision_doc:
        human_doc = col2.find()
        
        for doc2 in human_doc:
            oneandtwo = [doc2["post1"], doc2["post2"]]

            if doc1["name"] == doc2["name"]:
                if doc1["post1"] == doc2["post1"]:
                    matched += 1

 
    print("matched ", matched)
    print("total ", total)

    acc = (matched/total)*100
    print(acc)
    return acc


def indv_image_accuracy():
    col1 = db["postcode"]
    col2 = db["human_read"]
    col3 = db["acc_per_image"]

    vision_doc = col1.find()

    for doc1 in vision_doc:

        total = 0
        all_doc = col3.find()
        for _ in all_doc:
            total += 1

        match = col2.find_one({"name":doc1["name"]})

        if match == None:
            pass
        else:
            try:
                char = doc1["post1"]
                char2 = match["post1"]
                char3 = doc1["post2"]
                char4 = match["post2"]

                exp1 = calc_img_acc(char, char2)
                exp2 = calc_img_acc(char, char4)
                exp3 = calc_img_acc(char3, char2)
                exp4 = calc_img_acc(char4, char4)

                total = exp1 + exp2 + exp3 + exp4

                acc = int(50 * total)
                if acc > 100:
                    acc = 100

            except:
                char = doc1["post1"]
                char2 = match["post1"]

                exp1 = calc_img_acc(char, char2)


        print(acc)

        post = {"name": doc1["name"], "accuracy":acc}
        col3.insert_one(post)
    
    print("done")


def calc_img_acc(v1, v2):

    if v1 != 0:
        if v2 != 0:
            total = len(v1)
            total2 = len(v2)

            correct = total

            if total != total2:
                img_acc = 0
                return img_acc

            for i in range(total):
                if v1[i] != v2[i]:
                    correct -= 1

            if correct == 0:
                img_acc = 0
                return img_acc
            
            img_acc = correct/total
    else:
        img_acc = 0

    return img_acc


def results():
    acc = accuracy()
    name = "doc-vision"
    
    collection = db["results"]

    total = 0
    all_doc = collection.find()
    for _ in all_doc:
        total += 1

    post = {"_id":total, "system": name, "accuracy":acc}
    collection.insert_one(post)


def sys_time():
    collection = db["timings"]
    other_col = db["results"]

    time = 0

    all_times = collection.find({"name": "translate_text"})
    yesthings = collection.count_documents({"name": "translate_text"})

    for timeObject in all_times:
        pulledTime = timeObject["time"]
        time += pulledTime

    print(f'total time taken per image {time / yesthings}')

    total = other_col.estimated_document_count()

    post = {"_id":total, "system": "vision_v2", "totaltime":(time / yesthings)}
    other_col.insert_one(post)


def all_times():
    collection = db["timings"]
    other_col = db["results"]

    total = other_col.estimated_document_count()

    translate_obj = collection.find({"name": "translate_text"})
    pull_obj = collection.find({"name": "pull_image"})
    text_obj = collection.find({"name": "text_region"})

    tr_time = collection.count_documents({"name": "translate_text"})
    p_time = collection.count_documents({"name": "pull_image"})
    te_time = collection.count_documents({"name": "text_region"})

    time = 0
    for item in pull_obj:
        time += item["time"]
    mean1 = time/p_time
    post1 = {"_id":total, "name": "vision_v2", "section":"image pull time", "time":mean1}
    other_col.insert_one(post1)

    total = other_col.estimated_document_count()

    time = 0
    for item in text_obj:
        time += item["time"]
    mean2 = time/te_time
    post2 = {"_id":total, "name": "vision_v2", "section":"text detect time", "time":mean2 - mean1}
    other_col.insert_one(post2)

    total = other_col.estimated_document_count()
    
    time = 0
    for item in translate_obj:
        time += item["time"]
    mean3 = time/tr_time
    post3 = {"_id":total, "name": "vision_v2", "section":"translate time", "time":mean3 - mean2}
    other_col.insert_one(post3)

