import marcuslion as ml
from marcuslion import *

logger = logging.getLogger('ml_py')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

logger.info('Start marcuslion test')

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 2000)

