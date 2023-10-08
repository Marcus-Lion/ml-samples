# ml-samples
Marcus Lion Samples

https://www.google.com/search?q=youtube+pypi&rlz=1C1JSBI_enUS1066US1066&oq=youtube+pypi&gs_lcrp=EgZjaHJvbWUyBggAEEUYOTIICAEQABgWGB4yCAgCEAAYFhgeMgoIAxAAGA8YFhgeMggIBBAAGBYYHjIICAUQABgWGB4yCAgGEAAYFhgeMgoIBxAAGIYDGIoFMgoICBAAGIYDGIoFMgoICRAAGIYDGIoF0gEINTE1OWowajeoAgCwAgA&sourceid=chrome&ie=UTF-8#fpstate=ive&vld=cid:882dd603,vid:v4bkJef4W94,st:0

https://packaging.python.org/en/latest/tutorials/packaging-projects/

````
py -m pip install --upgrade pip
py -m pip install --upgrade build
py -m build
````

# py-ml-lib Test
````
py -m twine upload --repository testpypi -u __token__ --skip-existing dist/*
````

# Release
````
py -m twine upload -u __token__ --skip-existing dist/*
````

# Local Install 
````
pip install -i https://test.pypi.org/simple/ py-ml-lib --upgrade
````

