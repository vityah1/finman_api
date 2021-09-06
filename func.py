import json, random

JSON_PATH = "/home/vityah1/kt.if.ua/www/finman_api"
with open(f"""{JSON_PATH}/func.json""") as json_file:
    cfg = json.load(json_file)

rand = random.random() * 10000000
