import sys
import logging
import importlib
import urllib3
import ssl
import pandas as pd
import io

# sys.path.append("C:\\dev\\ml\\ml-py\\venv\\Lib\\site-packages")

logger = logging.getLogger('ml_py')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# import marcuslion
from marcuslion import main


# import py-ml-lib
# from py_ml_lib import main

def mlDataGov(url, key, **kwargs):
    # $ curl 'https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.csv?limit=1&api_key=DEMO_KEY&status=E&access=public&fuel_type=ELEC&location=Scarsdale'
    baseUrl = 'https://developer.nrel.gov/api'
    baseParams = "limit=1&api_key=" + key
    fullUrl = baseUrl + "/" + url + "?" + baseParams
    for key in kwargs:
        fullUrl += "&" + key + "=" + kwargs[key]
    logger.info(fullUrl)

    # Creating a PoolManager instance for sending requests.
    http = urllib3.PoolManager()

    # Sending a GET request and getting back response as HTTPResponse object.
    # this required downgrading requests library to urllib3-1.24.3 to avoid SSL cert error
    ssl._create_default_https_context = ssl._create_unverified_context
    resp = http.request("GET", fullUrl)

    # converting
    allData = resp.data.decode()
    return pd.read_csv(io.StringIO(allData), sep=",")


if __name__ == '__main__':
    logger.info('Start marcuslion test')
    df = mlDataGov('alt-fuel-stations/v1/nearest.csv', 'DEMO_KEY', status="E", access="public", fuel_type='ELEC',
                   location="Rochester%20NY")
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    print(df.tail(5))
    exit()
    try:
        # pathToModules = "C:\\dev\\py\\mainbloq\\venv\\Lib\\site-packages\\"
        # sys.path.append(pathToModules)
        # py_ml_lib = __import__("py-ml-lib")
        # foobar = importlib.import_module("py-ml-lib")
        # mod = importlib.import_module(pathToModules + "py-ml-lib")
        # import py-ml-lib

        a = main.add_one(5)
        print("call add one ", a)

        main.openml()
    except Exception as e:
        # print(e, '|', e.errno, '|', e.value, '|', e.args)
        print("Exception ", e)
