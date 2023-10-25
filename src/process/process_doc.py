import logging
import pandas as pd
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import certifi
import requests
from pyquery import PyQuery

logger = logging.getLogger('process_doc')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

#init Mongo Client as global
client = None
urlArchives = "https://www.sec.gov/Archives/"
MOZILLA_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'
docType = '10-K'
docDateStart = 20231001
docDateEnd = 20231019

def connectMongo():
    # open Mongo
    logger.info("Connect to Mongo")
    load_dotenv()
    user = os.environ.get('MONGODB_USER')
    pswd = os.environ.get('MONGODB_PASSWORD')
    # mongosh -u nick -p <pswd> mongodb+srv://nick:<pswd>@cluster0.5346qcs.mongodb.net/SEC
    port = 27017 #default
    CONNECTION_STRING = 'mongodb+srv://' + user + ':' + pswd + '@cluster0.5346qcs.mongodb.net/SEC'
    client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())
    return client

def downloadIdx():
    for docDate in range(docDateStart, docDateEnd):
        idx = "company." + str(docDate) + ".idx"
        idx_local = "./data/" + idx
        if not os.path.isfile(idx_local):
            url = urlArchives + "edgar/daily-index/2023/QTR4/" + idx
            logger.info("Downloading " + url + " to " + idx_local)
            headers = {'User-Agent': MOZILLA_AGENT}
            response = requests.get(url, headers=headers)

            # send a HTTP request to the server and save
            with open(idx_local, 'wb') as f:
                f.write(response.content)


def get_docs(idx):
    logger.info("Processing Document Index File " + idx)
    doc_list = []
    with open(idx) as f:
        lines = f.readlines()  # list containing lines of file
        columns = []  # To store column names

        header = True
        for line in lines:
            line = line.strip()  # remove leading/trailing white spaces
            if line:
                if header:
                    if '---' in line:
                        # for now hard code, headers might change
                        columns = ['company_name', 'form_type', 'cik', 'date_filed', 'file_name' ]
                        header = False
                        logger.info("Document Header Found: " + str(columns))
                else:
                    doc = {}  # dictionary to store file data (each line)
                    data = [item.strip() for item in line.split('  ')]
                    index_col = -1
                    for index, elem in enumerate(data):
                        if len(elem) > 0:
                            index_col += 1
                            if index_col < len(columns):
                                doc[columns[index_col]] = data[index]
                    doc_list.append(doc)  # append dictionary to list
                    logger.debug(doc)
    docCount = len(doc_list)
    logger.info("Read " + str(docCount) + " Documents")
    return doc_list

def test_header():
    response = requests.get('http://httpbin.org/headers')
    print(response.status_code)
    print(response.text)

def getIDFromDoc(doc):
    filename = doc['file_name']
    idx_full = filename.split('/')[-1]
    id = idx_full.split('.')[0]
    return id

def saveData(doc, text):
    # get ID
    id = getIDFromDoc(doc)
    logger.info("Save Data: " + str(doc))

    # Getting the database instance
    db = client['SEC']

    # Creating a collection
    colDoc = db['company-doc']
    logger.debug('db: ' + str(db))
    logger.debug('coll: ' + str(colDoc))
    logger.debug("Update Doc")
    filter = {'_id': id}
    docWithText = doc
    docWithText['text'] = text
    vals = {"$set": docWithText}

    # this is always returning None, why?
    result = colDoc.update_one(filter, vals, upsert=True)
    logger.debug("Upserted ID:", str(result.upserted_id))

def request_docs(doc_list):
    # https://stackoverflow.com/questions/11709079/parsing-html-using-python
    logger.info("Requesting " + docType + " Documents")
    for doc in doc_list:
        formType = doc['form_type']
        if docType in formType:
            filename = doc['file_name']
            companyName = doc['company_name']
            id = getIDFromDoc(doc)
            logger.info("Processing " + str(companyName) + ": Document " + str(id))
            #id = "0000320193-22-000108"
            #url = "https://www.sec.gov/Archives/edgar/data/320193/" + id + ".txt"
            url = urlArchives + filename
            headers = {'User-Agent': MOZILLA_AGENT }
            response = requests.get(url, headers=headers)
            logger.debug('Status Code: ' + str(response.status_code))
            html = response.content

            # grab text within spans only
            pq = PyQuery(html)
            tag = pq('span')
            fullText = tag.text()
            if len(fullText) > 10:
                firstLast = 150
                sampleTextHeader = fullText[0:firstLast]
                sampleTextFooter = fullText[-firstLast:]
                sampleText = sampleTextHeader + sampleTextFooter
                logger.debug("Sample Text: " + str(sampleText))
                saveData(doc, str(fullText))

if __name__ == '__main__':
    logger.info('Start MarcusLion Data Process')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    downloadIdx()
    client = connectMongo()

    # process past week
    for docDate in range(docDateStart, docDateEnd):
        idx = ".\data\company." + str(docDate) + ".idx"
        doc_list = get_docs(idx)
        result = request_docs(doc_list)