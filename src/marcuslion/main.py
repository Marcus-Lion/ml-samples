import webbrowser
import urllib3
import pandas as pd
import ssl
import io
import logging

logger = logging.getLogger()

def ml_open():
    url = "https://qa-marcuslion.web.app/"
    webbrowser.open(url)


def ml_addone(number):
    return number + 1


def ml_help():
    print(" .openml() or .add_one()")


def ml_search(key, providers):
    # $ curl 'https://qa1.marcuslion.com/core/datasets/search?providers=kaggle,usgov&title=bike'
    baseUrl = "https://qa1.marcuslion.com"
    url = 'core/datasets/search'
    baseParams = "providers="+providers+"&title=" + key
    fullUrl = baseUrl + "/" + url + "?" + baseParams

    logger.info(fullUrl)

    # Creating a PoolManager instance for sending requests.
    http = urllib3.PoolManager()

    # Sending a GET request and getting back response as HTTPResponse object.
    # this required downgrading requests library to urllib3-1.24.3 to avoid SSL cert error
    ssl._create_default_https_context = ssl._create_unverified_context
    resp = http.request("GET", fullUrl)

    # converting
    allData = resp.data.decode()
    return pd.read_json(io.StringIO(allData))
