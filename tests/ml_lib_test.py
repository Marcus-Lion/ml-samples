import sys
import logging
import importlib
#sys.path.append("C:\\dev\\ml\\ml-py\\venv\\Lib\\site-packages")

logger = logging.getLogger('ml_py')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

#import marcuslion
from marcuslion import main
#import py-ml-lib
#from py_ml_lib import main

if __name__ == '__main__':
    logger.info('Start marcuslion test')
    try:
        #pathToModules = "C:\\dev\\py\\mainbloq\\venv\\Lib\\site-packages\\"
        #sys.path.append(pathToModules)
        #py_ml_lib = __import__("py-ml-lib")
        #foobar = importlib.import_module("py-ml-lib")
        #mod = importlib.import_module(pathToModules + "py-ml-lib")
        #import py-ml-lib

        a = main.add_one(5)
        print("call add one ", a)

        main.openml()
    except Exception as e:
        #print(e, '|', e.errno, '|', e.value, '|', e.args)
        print("Exception ", e)