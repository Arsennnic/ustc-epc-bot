import json
from epc_bot import EPCBot

with open("config.json", "r", encoding="utf-8") as config:
    config = json.load(config)
sid = config["sid"]
passwd = config["passwd"]
filtr = config["filter"]
email_addr = config["email_addr"]
email_pwd = config["email_pwd"]

bot = EPCBot(sid, passwd, filtr, email_addr, email_pwd)
bot.start()
