import io
import os
import os.path
import time
from enum import Enum
from io import StringIO
from os import environ
from random import randint

import pandas as pd
from google.cloud import storage
from google.cloud import translate_v2 as translate
from google.cloud import vision
from google.cloud.vision import types
from PIL import Image, ImageDraw, ImageFont

import re
import timing

mul_address_accuracy = []

s_client = storage.Client()
v_client = vision.ImageAnnotatorClient()
t_client = translate.Client()  

current_image = ""

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5

@timing.timeit("pull_image")
def pull_image():
    client = s_client

    bucketFolder = environ.get('Sample parcel images')
    bucket = client.bucket("imperial-bucket-1")

    blobs = bucket.list_blobs(prefix=bucketFolder)
    blobList = [blob for blob in blobs if blob.size > 0]

    rand = randint(0, len(blobList)-1)
    bucketName = blobList[rand].bucket.name

    image = vision.types.Image()
    file_name = blobList[rand].name
    blob_uri = f'gs://{bucketName}/{file_name}'
    blob_source = {'source': {'image_uri': blob_uri}}

    tuple_val = (blob_source, file_name)
    return tuple_val


@timing.timeit("ordered_pull")
def ordered_pull(num):
    client = s_client

    bucketFolder = environ.get('Sample parcel images')
    bucket = client.bucket("imperial-bucket-1")

    blobs = bucket.list_blobs(prefix=bucketFolder)
    blobList = [blob for blob in blobs if blob.size > 0]

    bucketName = blobList[num].bucket.name

    image = vision.types.Image()
    file_name = blobList[num].name
    blob_uri = f'gs://{bucketName}/{file_name}'
    blob_source = {'source': {'image_uri': blob_uri}}

    tuple_val = (blob_source, file_name)
    return tuple_val


def test_image():
    client = s_client

    localFolder = os.path.abspath('C:/Users/Sebastian Dixon/Desktop/ImageData')

    bucketFolder = environ.get('Sample parcel images')
    bucket = client.bucket("imperial-bucket-1")

    blobs = bucket.list_blobs(prefix=bucketFolder)
    blobList = [blob for blob in blobs if blob.size > 0]

    bucketName = blobList[0].bucket.name

    image = vision.types.Image()
    
    file_name = 'Sample parcel images/04147.jpg'

    blob_uri = f'gs://{bucketName}/{file_name}'
    blob_source = {'source': {'image_uri': blob_uri}}

    client2 = v_client

    response = client2.document_text_detection(blob_source)
    document = response.full_text_annotation
    full_text = (document.text.replace("\n", " ")).upper()

    print(full_text)


@timing.timeit("text_region")
def text_region():
    full_address = ""
    full_text = ""

    pull_return = pull_image()
    image_path = pull_return[0]
    file_path = pull_return[1]

    parts = file_path.split("/")
    image_name = parts[1]
    print(image_name)


    client = v_client

    response = client.document_text_detection(image_path)

    print(response)

    document = response.full_text_annotation
    feature = FeatureType.BLOCK

    full_text = (document.text.replace("\n", " ")).upper()

    postcodes = []
    post_regex = re.compile("([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})")
    
    bounds=[]
    for i,page in enumerate(document.pages):
        for block in page.blocks:
            if feature==FeatureType.BLOCK:
                bounds.append(block.bounding_box.vertices)
            for paragraph in block.paragraphs:
                if feature==FeatureType.PARA:
                    bounds.append(paragraph.bounding_box.vertices)


    for n in range(len(bounds)):
        possible_post = word_in_region(document, bounds[n])
        possible_post = (possible_post.replace("\n", " ")).upper()

        check = re.search(post_regex, possible_post)
        if check != None:
            full_address += check.string

            print("ADDRESS:")
            print(check.string)
            no_space = (check[0]).replace(" ", "")
            postcodes.append(no_space)

    output_tuple = (postcodes, image_name)

    return output_tuple


def word_in_region(document, coords):
    coord1 = (coords[0].x, coords[0].y)
    coord2 = (coords[1].x, coords[1].y)
    coord3 = (coords[2].x, coords[2].y)
    coord4 = (coords[3].x, coords[3].y)

    text = ""

    box_confidence = 0
    count = 0

    coordinates = extremeties(coord1, coord2, coord3, coord4)

    x1, y1 = coordinates[0]
    x2, y2 = coordinates[3]

    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:

                        min_x=min(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
                        max_x=max(symbol.bounding_box.vertices[0].x,symbol.bounding_box.vertices[1].x,symbol.bounding_box.vertices[2].x,symbol.bounding_box.vertices[3].x)
                        min_y=min(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)
                        max_y=max(symbol.bounding_box.vertices[0].y,symbol.bounding_box.vertices[1].y,symbol.bounding_box.vertices[2].y,symbol.bounding_box.vertices[3].y)

                        if(min_x >= x1 and max_x <= x2 and min_y >= y1 and max_y <= y2):
                            text += symbol.text
                            box_confidence += symbol.confidence
                            count += 1 
                            
                            if(symbol.property.detected_break.type==1 or 
                                symbol.property.detected_break.type==3):
                                text+=' '

                            if(symbol.property.detected_break.type==2):
                                text+='\t'

                            if(symbol.property.detected_break.type==5):
                                text+='\n'
    if count > 0:
        mul_address_accuracy.append((box_confidence / count)*100)

    return text
                            

def extremeties(*coordinates):

    import functools

    def extreme(index, fn):
        return fn(c[index] for c in coordinates)

    x_extreme = functools.partial(extreme, 0)
    y_extreme = functools.partial(extreme, 1)

    return([(x_extreme(min), y_extreme(min)),(x_extreme(min), y_extreme(max)), (x_extreme(max), y_extreme(min)), (x_extreme(max), y_extreme(max))])



@timing.timeit("translate_text")
def translate_text():
    client = t_client

    tuple_return = text_region()
    all_text = tuple_return[0]

    target = 'en'

    n_english = []
    english = []

    for post in all_text:
        lang = client.detect_language(post)
        if lang['language'] == 'zh':
            n_english.append(lang['input'])
        elif lang['language'] == 'zh-CN':
            n_english.append(lang['input'])
        elif lang['language'] == 'zh-TW':
            n_english.append(lang['input'])

    for i in range(len(n_english)):
        output = client.translate(
            n_english[i],
            target_language=target
        )
        english.append(output["translatedText"])

    if len(n_english) > 0:
        try:
            del n_english['Wei']
        except:
            print(u"Language found: {}".format(n_english))
            print(u"Translation: {}".format(english))


test_image()
#text_region()