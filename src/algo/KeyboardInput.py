import logging
from py import config


def KeyboardInput(name):
    logging.info("Thread %s: starting", name)
    last_input = ''
    while not last_input.startswith("Q"):
        last_input = input('Accepting Keyboard Input\n')
        logging.info('Input Received: %s', last_input)

        if last_input.startswith("TE"):
            config.TRADING_ENABLED = True
        elif last_input.startswith("TD"):
            config.TRADING_ENABLED = False
        logging.info('TRADING_ENABLED = %s', config.TRADING_ENABLED)
    logging.info("Thread %s: finishing", name)
    config.ACTIVE = False
    logging.info("ACTIVE = %s", config.ACTIVE)
