#!/usr/bin/env python

# TODO: subscribe to streaming data
# TODO: subscribe to order updates
# TODO: Modularize. Create Order, Position classes in separate files
# TODO: limit orders, buy at bid, sell at ask
# TODO: input tickers as input file not args
# TODO: schedule position, market updates
# TODO: keyboard input


import argparse
import logging
import pandas as pd
import numpy as np
import threading
from ibapi.contract import Contract

from py.MarketDataApp import MarketDataApp
from py.KeyboardInput import KeyboardInput
from py import config


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class ProductData:
    def __init__(self, contract: Contract):
        self.contract = contract
        self.dfIntraday = pd.DataFrame(columns=['Date', 'Close'])
        self.dfDaily = pd.DataFrame(columns=['Date', 'Close'])
        self.requestIdIntraday = -1
        self.requestIdDaily = -1
        self.requestIdStreaming = -1
        self.lastSignalDaily = np.NaN
        self.lastSignalIntraday = np.NaN
        self.Account = None
        self.Position = 0
        self.AvgCost = -1
        self.Low = -1
        self.High = -1


pd.set_option('display.width', 1000)
pd.set_option('display.max_columns', None)

# logging.basicConfig(level=logging.INFO)
# create logger with 'spam_application'
logger = logging.getLogger("Trading_Signals")
logger.setLevel(logging.INFO)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

loggerRoot = logging.getLogger("root")
loggerRoot.setLevel(logging.INFO)
loggerRoot.addHandler(ch)


def make_contract(symbol: str, sec_type: str, currency: str, exchange: str):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract


def create_product(symbol: str, sec_type: str, currency: str, exchange: str):
    contract = make_contract(symbol, sec_type, currency, exchange)
    product = ProductData(contract)
    return product


def main():
    argp = argparse.ArgumentParser()
    # argp.add_argument("symbol", action="append")
    argp.add_argument("-s", "--symbol", nargs='+')
    argp.add_argument(
        "-d", "--debug", action="store_true", help="turn on debug logging"
    )
    argp.add_argument(
        "-p", "--port", type=int, default=7496, help="local port for TWS connection"
    )
    argp.add_argument(
        "--currency", type=str, default="USD", help="currency for symbols"
    )
    argp.add_argument(
        "--exchange", type=str, default="SMART", help="exchange for symbols"
    )
    argp.add_argument(
        "--security-type", type=str, default="STK", help="security type for symbols"
    )
    argp.add_argument(
        "--snapshot", action="store_true", help="return snapshots and exit"
    )
    argp.add_argument(
        "-t", "--tickers", type=str, default="./data/tickers.csv", help="input tickers"
    )
    args = argp.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    ticker_file = args.tickers
    Products = {}
    if args.symbol:
        for s in args.symbol:
            product = create_product(s, args.security_type, args.currency, args.exchange)
            Products[s] = product
    else:
        dfTickers = pd.read_csv(ticker_file)
        logging.warning("Processing " + str(len(dfTickers)) + " symbols.")
        for index, row in dfTickers.iterrows():
            symbol = row['ticker']
            product = create_product(symbol, args.security_type, args.currency, args.exchange)
            Products[symbol] = product

    # keyboard input
    thread_name = "KeyboardInput"
    logging.info("Creating " + thread_name + " thread")
    x = threading.Thread(target=KeyboardInput, args=(thread_name,))
    logging.info("Running " + thread_name + " thread")
    x.start()
    logging.debug("Main    : wait for the thread to finish")
    # x.join()
    logging.debug("Main    : all done")

    # run IB client
    app = MarketDataApp(Products, args)
    app.connect("127.0.0.1", args.port, clientId=0)
    app.run()


if __name__ == "__main__":
    main()
