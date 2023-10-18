import logging
import pandas as pd
from dotenv import load_dotenv
import os
from pymongo import MongoClient
import certifi

logger = logging.getLogger('ml_py')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

if __name__ == '__main__':
    logger.info('Start marcuslion SEC mongodb')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)

    # load user + pswd from .env
    load_dotenv()
    user = os.environ.get('MONGODB_USER')
    pswd = os.environ.get('MONGODB_PASSWORD')
    # mongosh -u nick -p <pswd> mongodb+srv://nick:<pswd>@cluster0.5346qcs.mongodb.net/SEC
    port = 27017 #default
    CONNECTION_STRING = 'mongodb+srv://' + user + ':' + pswd + '@cluster0.5346qcs.mongodb.net/SEC'
    searchDoc = '10-K'
    searchDate = '2023-10-12'
    client = MongoClient(CONNECTION_STRING, tlsCAFile=certifi.where())

    # Getting the database instance
    db = client['SEC']

    # Creating a collection
    colFacts = db['company-facts']
    colTickers = db['company-tickers']
    logger.info('db: ' + str(db))
    logger.info('coll: ' + str(colFacts))

    #load title to ticker
    allTickers = colTickers.find()
    nameToTicker = {}
    cikToTicker = {}
    first = True
    for x in allTickers:
        for y in range(10850):
            stry = str(y)
            yTicker = x[stry]
            ticker = yTicker['ticker']
            cikStr = yTicker['cik_str']
            cik = int(cikStr)
            title = yTicker['title'].lower().replace(",", "").replace(".", "").replace("company", "co")
            cikToTicker[cik] = ticker
            nameToTicker[title] = ticker
    #print(str(nameToTicker))
    #exit()

    colFactsFilter = colFacts.find({'facts.dei.EntityCommonStockSharesOutstanding.units.shares': {"$elemMatch": {"form": "10-K", "filed": "2023-10-12"}}})
    logger.info('Companies filing 10-K on ' + searchDate)
    for entity in colFactsFilter:
        cikStr = entity['cik']
        cik = int(cikStr)
        entityName = entity['entityName']
        entityNameMatch = entityName.lower().replace(",", "").replace(".", "").replace("company", "co")
        entityNameCik = entityName + " cik: " + str(cik)
        if cik in cikToTicker:
            fullOutput = entityNameCik + " Ticker: " + cikToTicker[cik]
        elif entityNameMatch in nameToTicker:
            fullOutput = entityNameCik + " Ticker: " + nameToTicker[entityNameMatch]
        else:
            fullOutput = entityNameCik
        logger.info(fullOutput)
    logger.info("Done")

    #exit()