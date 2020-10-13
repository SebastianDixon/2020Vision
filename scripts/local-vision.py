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

unverified_pc = []
all_text_bounds = []
mul_address_accuracy = []

s_client = storage.Client()
v_client = vision.ImageAnnotatorClient()
t_client = translate.Client()  

class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5


def download_ordered_image(total):
    client = s_client

    localFolder = os.path.abspath('C:/Users/Sebastian Dixon/Desktop/ImageData')

    bucketName = environ.get('imperial-bucket-1')
    bucketFolder = environ.get('Sample parcel images')
    bucket = client.bucket("imperial-bucket-1")

    blobs = bucket.list_blobs(prefix=bucketFolder)
    blobList = [blob for blob in blobs if blob.size > 0]

    for i in range(total):
        jpeg = blobList[i].download_as_bytes()
        path = blobList[i].name

        fileName = os.path.basename(path)

        fullName = os.path.join(localFolder, fileName)
        with open(fullName, "wb") as fileHandle:
            fileHandle.write(jpeg)



def text_region():
    full_address = ""
    image_path = analyse_text()
    client = v_client

    total_accuracy = 0

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    content_image = types.Image(content=content)
    response = client.document_text_detection(image=content_image)
    document = response.full_text_annotation
    feature = FeatureType.BLOCK
    
    bounds=[]
    for i,page in enumerate(document.pages):
        for block in page.blocks:
            if feature==FeatureType.BLOCK:
                bounds.append(block.bounding_box.vertices)
            for paragraph in block.paragraphs:
                if feature==FeatureType.PARA:
                    bounds.append(paragraph.bounding_box.vertices)
    
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for bound in bounds:
        draw.line([
            bound[0].x, bound[0].y,
            bound[1].x, bound[1].y,
            bound[2].x, bound[2].y,
            bound[3].x, bound[3].y,
            bound[0].x, bound[0].y],fill='red', width=5)

        all_text_bounds.append(bound)

    image.save('C:/Users/Sebastian Dixon/Desktop/ImageData/draw.jpg')

    current_region = []
    for i in range((len(all_text_bounds))):
        current_region.append(all_text_bounds[i])


    for n in range(len(all_text_bounds)):
        possible_post = word_in_region(document, all_text_bounds[n])

        for code in unverified_pc:

            string_post = str(code)
            lower_string_post = string_post.lower()
            lower_possible_post = possible_post.lower()
            no_spaces = lower_possible_post.replace(" ", "")

            if lower_string_post in no_spaces:
                full_address = possible_post
                print("ADDRESS FOUND: ")            

                print(full_address)

    total = 0
    try:
        for acc in mul_address_accuracy:
            total += acc

        print((total / len(mul_address_accuracy), "% = address confidence"))
    except:
        print('no address')


    return full_address


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

    
def analyse_text():
    image_path = download_random_image()

    client = v_client


    image = types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    postcodes = []
    accept_num = ['0','1','2','3','4','5','6','7','8','9','O']

    for i in range(len(texts)):
        if texts._values[i].description[0] == "*":
            if texts._values[i].description[-1] == "*":
                barcode = texts._values[i].description
                print("Barcode value =", barcode)

        elif texts._values[i].description == "kg":
            weight = texts._values[i-1].description
            print("Weight value =", weight, 'kg')


        elif len(texts._values[i].description) == 3:
            if texts._values[i].description[0] in accept_num:
                if len(texts._values[i-1].description) in [3, 4]:
                    unverified_pc.append(texts._values[i-1].description + texts._values[i].description)

    return image_path


def translate_text():
    client = t_client

    all_text = text_region()

    target = 'en'

    n_english = []
    english = []

    for i in range(1, len(all_text)):
        lang = client.detect_language(all_text)
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



download_ordered_image(100)


