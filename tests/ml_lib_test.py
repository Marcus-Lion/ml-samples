import pandas as pd

from src.marcuslion.main import ml_search

if __name__ == '__main__':
    try:
        df = ml_search("bike", "kaggle,usgov")
        print(df.head(3))
        print(df.tail(3))

    except Exception as e:
        # print(e, '|', e.errno, '|', e.value, '|', e.args)
        print("Exception ", e)
