import boto3
import sys
import re
import json
from collections import defaultdict
from PIL import Image
import requests
from io import BytesIO

import os
from dotenv import load_dotenv


load_dotenv()

AWS_CONFIG_FILE = os.getenv('AWS_CONFIG_FILE')
AWS_SHARED_CREDENTIALS_FILE = os.getenv('AWS_SHARED_CREDENTIALS_FILE')

def get_kv_map(url):
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        bytes_test = response.content

    # process using image bytes
    session = boto3.Session()
    client = session.client('textract', region_name='ap-southeast-1')
    response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['FORMS'])

    # Get the text blocks
    blocks = response['Blocks']

    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map


def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '

    return text


def print_kvs(kvs):
    for key, value in kvs.items():
        print(key, ":", value)


def search_value(kvs, search_key):
    for key, value in kvs.items():
        if re.search(search_key, key, re.IGNORECASE):
            return value

def getInfor(file_url):
    key_map, value_map, block_map = get_kv_map(file_url)

    # Get Key Value relationship
    result = {
    "Passport number":"",
    "Surname":"",
    "Given name":"",
    "Date of birth":"",
    "Place of birth":"",
    "Current nationality":"",
    "Sex":"",
    "ID card number":"",
    "Date of issue":"",
    "Expiry date":"",
    "Issuing Authority/Place of issue":""
    }
    data = get_kv_relationship(key_map, value_map, block_map)
    for k, v in data.items():
        k = k.lower()
        if k.find("passport no") != -1:
            result["Passport number"] = v[0].strip()
        elif k.find("surname") != -1:
            result["Surname"] = v[0].strip()
        elif k.find("given name") != -1:
            result["Given name"] = v[0].strip()
        elif k.find("date of birth") != -1:
            result["Date of birth"] = v[0].strip()
        elif k.find("nationality") != -1:
            result["Current nationality"] = v[0].strip()
        elif k.find("place of birth") != -1:
            result["Place of birth"] = v[0].strip()
        elif k.find("sex") != -1:
            result["Sex"] = v[0].strip()
        elif k.find("personal") != -1:
            result["ID card number"] = v[0].strip()
        elif k.find("date of issue") != -1:
            result["Date of issue"] = v[0].strip()
        elif k.find("expiry") != -1:
            result["Expiry date"] = v[0].strip()
        elif k.find("authority") != -1:
            result["Issuing Authority/Place of issue"] = v[0].strip()
    return result
