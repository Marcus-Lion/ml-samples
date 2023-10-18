from marcuslion import ml_search, ml_help

if __name__ == '__main__':
    try:
        ml_help()

        df = ml_search("bike", "kaggle,usgov")
        print(df.head(3))
        print(df.tail(3))

    except Exception as e:
        print("Exception ", e)
