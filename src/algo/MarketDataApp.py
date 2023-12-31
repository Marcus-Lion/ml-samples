# STD
import argparse
import logging
import datetime
from decimal import Decimal
import numpy as np
import pandas_ta
from arch import arch_model

# IB
from ibapi import wrapper
from ibapi.common import TickerId, TickAttrib, BarData, ListOfHistoricalSessions, RealTimeBar
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import iswrapper, decimalMaxString, floatMaxString
from ibapi.ticktype import TickType, TickTypeEnum
from TWS_API.source.pythonclient.ibapi.order import Order
from py import config

# global vars
RequestIdToProductHist, RequestIdToProductStreaming, RequestIdToProductMktData = {}, {}, {}


# static methods
def predict_volatility(x):
    best_arch_model = arch_model(
        y=x,
        x=None,
        mean='Constant',
        lags=0,
        vol='GARCH',
        p=2,
        o=0,
        q=2,
        power=2.0,
        dist='normal',
        hold_back=None,
        rescale=True
    )
    # print('best_arch_model ', str(best_arch_model))
    best_arch_model_fit = best_arch_model.fit(
        update_freq=5,
        disp='off'
    )
    # print('best_arch_model_fit ', str(best_arch_model_fit))
    variance_forecast = best_arch_model_fit.forecast(horizon=1).variance.iloc[-1, 0]
    # print(x.index[-1])
    return variance_forecast


class MarketDataApp(EClient, wrapper.EWrapper):

    def __init__(self, products: dict, args: argparse.Namespace):
        EClient.__init__(self, wrapper=self)
        wrapper.EWrapper.__init__(self)
        self.orderId = None
        self.lastOrderId = None
        self.request_id = 0
        self.started = False
        self.products = products
        self.request_contracts = {}
        self.pending_ends = set()
        self.args = args
        logging.getLogger("ibapi.wrapper").setLevel(logging.WARNING)
        logging.getLogger("ibapi.client").setLevel(logging.WARNING)

    @iswrapper
    def process_symbols(self):
        if config.ACTIVE:
            logging.debug("Processing %d symbols", len(self.products))

            for symbol in self.products:
                product = self.products[symbol]
                logging.debug('Symbol %s: Intraday Signal: %s Daily Signal: %s Current Position: %d', symbol,
                              product.lastSignalDaily, product.lastSignalIntraday, product.Position)
                lmtPrice = -1
                action = None
                if product.lastSignalDaily > 0 and product.lastSignalIntraday > 0:
                    logging.info("Buy Signal for %s: Position %d Low %f TRADING_ENABLED=%s", symbol,
                                 product.Position, product.Low, config.TRADING_ENABLED)
                    if product.Position < 1:
                        action = "BUY"
                        lmtPrice = product.Low
                elif product.lastSignalDaily < 0 and product.lastSignalIntraday < 0:
                    logging.info("Sell Signal for %s: Position %d High %f TRADING_ENABLED=%s", symbol,
                                 product.Position, product.High, config.TRADING_ENABLED)
                    if product.Position > 0:
                        action = "SELL"
                        lmtPrice = product.High

                if config.TRADING_ENABLED and lmtPrice > 0 and action:
                    logging.warning("Placing Order")
                    super().nextValidId(self.orderId)
                    # send order
                    self.reqIds(-1)
                    qty = 1
                    orderType = "LMT"
                    if self.lastOrderId is not None:
                        self.orderId = max(self.orderId, self.lastOrderId + 1)
                    order = Order()
                    order.orderId = self.orderId
                    order.orderType = orderType
                    order.action = action
                    order.totalQuantity = qty
                    order.lmtPrice = lmtPrice
                    logging.warning(" Placing Order %d (%s %d %s at %d) ", self.orderId, action, qty,
                                    product.contract.symbol,
                                    lmtPrice)
                    self.placeOrder(self.orderId, product.contract, order)
                    self.lastOrderId = self.orderId
                    product.Position = product.Position + (1 if action == "BUY" else -1)
        else:
            logging.info("Disconnect!")
            self.disconnect()

    def next_request_id(self):
        self.request_id += 1
        return self.request_id

    @iswrapper
    def position(self, account: str, contract: Contract, position: Decimal,
                 avgCost: float):
        super().position(account, contract, position, avgCost)
        logging.debug("Position." + "Account:" + account, "Symbol:" + contract.symbol + "SecType:" +
                      contract.secType + "Currency:" + contract.currency +
                      "Position:" + str(decimalMaxString(position)) + "Avg cost:" + str(floatMaxString(avgCost)))
        symbol = contract.symbol
        if symbol in self.products:
            logging.info("Position " + str(contract.symbol) + " Found in Portfolio, updating!")
            product = self.products[symbol]
            product.Account = account
            product.Position = position
            product.AvgCost = avgCost

    @iswrapper
    def positionEnd(self):
        super().positionEnd()
        logging.info("Positions Ended")
        self.process_symbols()

    @iswrapper
    def realtimeBar(self, reqId: TickerId, time: int, open_: float, high: float, low: float, close: float,
                    volume: Decimal, wap: Decimal, count: int):
        product = RequestIdToProductStreaming[reqId]
        logging.debug("RealTimeBar TickerId:" + str(reqId) + " Symbol " + product.contract.symbol + " low: " +
                      str(low) + " high: " + str(high))
        bar = RealTimeBar(time, -1, open_, high, low, close, volume, wap, count)
        super().realtimeBar(reqId, time, open_, high, low, close, volume, wap, count)
        product.Low = bar.low
        product.High = bar.high
        self.process_symbols()

    @iswrapper
    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib):
        print(f"{reqId} {TickTypeEnum.to_str(tickType)} price: {price} {attrib}")

    @iswrapper
    def tickSize(self, reqId: TickerId, tickType: TickType, size: int):
        print(f"{reqId} {TickTypeEnum.to_str(tickType)} size: {size}")

    @iswrapper
    def tickString(self, reqId: TickerId, tickType: TickType, value: str):
        print(f"{reqId} {TickTypeEnum.to_str(tickType)} string: {value}")

    @iswrapper
    def tickGeneric(self, reqId: TickerId, tickType: TickType, value: float):
        print(f"{reqId} {TickTypeEnum.to_str(tickType)} generic: {value}")

    @iswrapper
    def tickSnapshotEnd(self, reqId: int):
        super().tickSnapshotEnd(reqId)
        self.pending_ends.remove(reqId)
        if self.args.snapshot and len(self.pending_ends) == 0:
            print("All snapshot requests complete.")
            self.done = True

    @iswrapper
    def historicalData(self, reqId: int, bar: BarData):
        product = RequestIdToProductHist[reqId]
        if reqId == product.requestIdIntraday:
            product.dfIntraday.loc[len(product.dfIntraday.index)] = [bar.date, bar.close]
        elif reqId == product.requestIdDaily:
            product.dfDaily.loc[len(product.dfDaily.index)] = [bar.date, bar.close]

    @iswrapper
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)
        product = RequestIdToProductHist[reqId]
        logging.debug(
            product.contract.symbol + " HistoricalDataEnd. ReqId:" + str(reqId) + "from" + str(start) + "to" + str(end))
        if reqId == product.requestIdIntraday:
            logging.debug('Intraday DF Size ' + str(product.dfIntraday.shape))
            rsi_upper = 60 + product.Position
            rsi_lower = 100 - rsi_upper
            product.dfIntraday['rsi'] = pandas_ta.rsi(
                close=product.dfIntraday['Close'],
                length=20)
            product.dfIntraday['signal_intraday'] = product.dfIntraday.apply(
                lambda x: np.nan if x['rsi'] is None
                else 1 if x['rsi'] > rsi_upper
                else -1 if x['rsi'] < rsi_lower
                else np.nan,
                axis=1)
            logging.debug('Intraday Series ' + str(product.dfIntraday))
            dfIntradaySignal = product.dfIntraday[product.dfIntraday['signal_intraday'] < 0]
            # print(dfIntradaySignal)
            product.lastSignalIntraday = product.dfIntraday.iloc[
                -1, product.dfIntraday.columns.get_loc('signal_intraday')]
            logging.debug("Last Intraday Signal: " + str(product.lastSignalIntraday))
        elif reqId == product.requestIdDaily:
            var_rolling = 180
            product.dfDaily['log_ret'] = np.log(product.dfDaily['Close']).diff()
            product.dfDaily['variance'] = product.dfDaily['log_ret'].rolling(var_rolling).var()
            product.dfDaily['predictions'] = (product.dfDaily['log_ret'].rolling(var_rolling)
                                              .apply(lambda x: predict_volatility(x)))

            first_prediction = product.dfDaily.iloc[-1, product.dfDaily.columns.get_loc('predictions')]
            logging.debug('first_prediction ' + str(first_prediction))
            first_variance = product.dfDaily.iloc[-1, product.dfDaily.columns.get_loc('variance')]
            logging.debug('first_variance ' + str(first_variance))
            scale_factor = np.log10(first_prediction / first_variance)
            logging.debug('scale_factor ' + str(scale_factor))
            scale_factor_round = np.round(scale_factor)
            logging.debug('scale_factor_round ' + str(scale_factor_round))
            log10_scale_factor_round = 10 ** -scale_factor_round
            product.dfDaily = product.dfDaily.dropna()
            product.dfDaily['predictions'] = product.dfDaily['predictions'] * log10_scale_factor_round
            product.dfDaily['prediction_premium'] = ((product.dfDaily['predictions'] - product.dfDaily['variance'])
                                                     / product.dfDaily['variance'])
            product.dfDaily['premium_std'] = product.dfDaily['prediction_premium'].rolling(60).std()
            product.dfDaily['signal_daily'] = product.dfDaily.apply(
                lambda x: 1 if (x['prediction_premium'] > x['premium_std'] * config.std_threshold)
                else (-1 if (x['prediction_premium'] < x['premium_std'] * -config.std_threshold) else np.nan),
                axis=1)
            # product.dfDaily['signal_daily'] = product.dfDaily['signal_daily'].shift()
            dfDailySignal = product.dfDaily[product.dfDaily['signal_daily'] < 0]
            dfDailyLastWeek = product.dfDaily.iloc[-14:]
            logging.debug('Daily Series Size ' + str(product.dfDaily.shape))
            logging.debug('Daily Series Last Week')
            logging.debug(dfDailyLastWeek)
            product.lastSignalDaily = product.dfDaily.iloc[-1, product.dfDaily.columns.get_loc('signal_daily')]
            logging.debug("Last Daily Signal: " + str(product.lastSignalDaily))

    @iswrapper
    def historicalDataUpdate(self, reqId: int, bar: BarData):
        print("HistoricalDataUpdate. ReqId:", reqId, "BarData.", bar)

    @iswrapper
    def historicalSchedule(self, reqId: int, startDateTime: str, endDateTime: str, timeZone: str,
                           sessions: ListOfHistoricalSessions):
        super().historicalSchedule(reqId, startDateTime, endDateTime, timeZone, sessions)
        print("HistoricalSchedule. ReqId:", reqId, "Start:", startDateTime, "End:", endDateTime, "TimeZone:", timeZone)
        for session in sessions:
            print("\tSession. Start:", session.startDateTime, "End:", session.endDateTime, "Ref Date:", session.refDate)

    @iswrapper
    def connectAck(self):
        logging.warning("Connected")

    @iswrapper
    def nextValidId(self, orderId: int):
        logging.info(f"Next valid order id: {orderId}")
        self.orderId = orderId
        self.start()

    def start(self):
        if self.started:
            return

        self.started = True
        queryTime = (datetime.datetime.today() + datetime.timedelta(hours=5)).strftime("%Y%m%d-%H:%M:%S")
        # queryTime = datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S")
        logging.info('queryTime ' + queryTime)
        logging.warning("Requesting Data for " + str(len(self.products)) + " symbols.")
        for symbol in self.products:
            product = self.products[symbol]
            rid = self.next_request_id()
            product.requestIdIntraday = rid
            RequestIdToProductHist[rid] = product

            # request intraday
            self.reqHistoricalData(
                rid,
                product.contract,
                queryTime,
                "2 D",
                "5 mins",
                "TRADES",
                1, 1, False, [])
            self.pending_ends.add(rid)
            self.request_contracts[rid] = product.contract

            # request daily
            rid = self.next_request_id()
            product.requestIdDaily = rid
            RequestIdToProductHist[rid] = product
            # queryTime = (datetime.datetime.today() - datetime.timedelta(days=360)).strftime("%Y%m%d-%H:%M:%S")
            self.reqHistoricalData(
                rid,
                product.contract,
                queryTime,
                "1 Y",
                "1 day",
                "TRADES",
                1, 1, False, [])
            self.pending_ends.add(rid)
            self.request_contracts[rid] = product.contract

            # request streaming market data
            rid = self.next_request_id()
            logging.info("Request Realtime Bars for %d - %s", rid, product.contract.symbol)
            RequestIdToProductStreaming[rid] = product
            self.reqRealTimeBars(
                rid,
                product.contract,
                5,
                "MIDPOINT",
                True,
                [])

            # request top of market
            if config.TICK_BY_TICK:
                rid = self.next_request_id()
                logging.info("Request Market Data for %d - %s", rid, product.contract.symbol)
                RequestIdToProductMktData[rid] = product
                self.reqMktData(
                    rid,
                    product.contract,
                    "",
                    False,
                    False,
                    [])

        # request positions
        self.reqPositions()

    @iswrapper
    def error(self, req_id: TickerId, error_code: int, error: str, unnamed):
        super().error(req_id, error_code, error)
        logging.debug("Error. Id:" + str(req_id) + " Code:" + str(error_code) + " Msg:", error)
