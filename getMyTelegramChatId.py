import datetime, logging, os, pathlib, sys, time

import telegram


#### #### #### #### #### 
#### Prologue #### 
#### #### #### #### #### 
def EarlyExit(msg:str=None, status:int=0):
    if isinstance(msg, str):
        print(msg)
    status = status if isinstance(status, int) else 0
    sys.exit(status)


#### #### #### #### #### 
#### Main #### 
#### #### #### #### ####
## Variables initialization
envFilePath = "./.env"
assert os.path.isfile(envFilePath), f"File \".env\" cannot be found. Make sure you have copied \".env.example\" and renamed it as \".env\"."

env = {}
with open(envFilePath, "r") as f:
    ## Variables initialization
    lines = f.readlines()
    ## Main
    for line in lines:
        keyValuePair = line.split("=")
        if len(keyValuePair) == 2:
            env[keyValuePair[0] ] = keyValuePair[1].strip("\n")

tg_flashcard_bot_token = env.get("TG_FLASHCARD_BOT_TOKEN", None)
if tg_flashcard_bot_token is None:
    EarlyExit(
        msg=f"Make sure there is a line with \"TG_FLASHCARD_BOT_TOKEN\" as the key in \".env\"",
        status=1)
if tg_flashcard_bot_token == "":
    EarlyExit(
        msg=f"Make sure you have created a new Telegram bot, obtained the bot's token and pasted the token after \"TG_FLASHCARD_BOT_TOKEN=\" in \".env\"",
        status=1)

## Main
try:
    bot = telegram.Bot(token=tg_flashcard_bot_token)
except telegram.error.InvalidToken:
    EarlyExit(
        msg="Token for accessing the Telegram bot is invalid",
        status=1)
except:
    EarlyExit(
        msg="Encounter an unexpected error",
        status=1)

updates = bot.get_updates()
for update in updates:
    messageInfo = update.message
    if not isinstance(messageInfo, telegram.Message):
        continue
    chatInfo = messageInfo.chat
    if not isinstance(chatInfo, telegram.Chat):
        continue
    chatMemberId = chatInfo.id
    chatMemberLastName = chatInfo.last_name
    chatMemberFirstName = chatInfo.first_name
    print(f"Obtained a message from \"{chatMemberFirstName} {chatMemberLastName}\" with chat id: {chatMemberId}")
