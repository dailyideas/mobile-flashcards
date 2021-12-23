import datetime, logging, os, pathlib, sys, time
import urllib
from logging.handlers import RotatingFileHandler
from os import path

import pymongo
import telegram

from flashcardSystem.FlashcardDatabaseMessenger import FlashcardDatabaseMessenger
from flashcardSystem.FlashcardsManager import FlashcardsManager
from flashcardSystem.FlashcardUserMessenger import FlashcardUserMessenger


#### #### #### #### #### 
####  Global constants #### 
#### #### #### #### ####
DB_NAME = os.environ.get("APP_DB_NAME")
DB_USERNAME = os.environ.get("APP_DB_USERNAME")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD")
TG_FLASHCARD_BOT_TOKEN = os.environ.get("APP_TG_FLASHCARD_BOT_TOKEN")
TG_FLASHCARD_BOT_CHAT_ID = int(os.environ.get(
    "APP_TG_FLASHCARD_BOT_CHAT_ID") )
FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR = int(os.environ.get(
    "APP_FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR") )
RELEASE_MODE = os.environ.get("APP_RELEASE_MODE")

SCRIPT_NAME = path.basename(__file__).split(".")[0]
SCRIPT_DIRECTORY = path.dirname(path.abspath(__file__) )
ROOT_DIRECTORY = SCRIPT_DIRECTORY
CACHE_DIRECTORY = path.join(ROOT_DIRECTORY, "caches/", SCRIPT_NAME)
LOG_DIRECTORY = path.join(ROOT_DIRECTORY, "logs/", SCRIPT_NAME)
LOG_LEVEL = logging.INFO


#### #### #### #### #### 
#### Global variables #### 
#### #### #### #### #### 
#### Logging
log = logging.getLogger()


#### #### #### #### #### 
#### Global Setups #### 
#### #### #### #### #### 
#### Paths
os.makedirs(CACHE_DIRECTORY, exist_ok=True)
os.makedirs(LOG_DIRECTORY, exist_ok=True)
#### Logging
formatter = logging.Formatter(
    "%(asctime)s-%(name)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S")
logPath = path.join(LOG_DIRECTORY, SCRIPT_NAME + ".log")
rotating_file = RotatingFileHandler(logPath, mode='a', maxBytes=2e6, 
    backupCount=10)
rotating_file.setFormatter(formatter)
log.addHandler(rotating_file)
log.setLevel(LOG_LEVEL)
loggers = [logging.getLogger(name) for name in \
    logging.root.manager.loggerDict]
for logger in loggers:
    logger.setLevel(LOG_LEVEL)


#### #### #### #### #### 
#### Prologue #### 
#### #### #### #### #### 
log.debug("Python version: %s", sys.version.split(" ")[0] )


#### #### #### #### #### 
#### Functions #### 
#### #### #### #### #### 
def LoadFlashcardsManager(cachePath:str, 
        numJobsPerHour:int
    ) -> FlashcardsManager:
    flashcardsManager = FlashcardsManager.Load(cachePath=cachePath)
    if flashcardsManager is None:
        return FlashcardsManager(numJobsPerHour=numJobsPerHour)
    else:
        flashcardsManager.NumJobsPerHour = numJobsPerHour
        return flashcardsManager


#### #### #### #### #### 
#### Main #### 
#### #### #### #### #### 
## Prologue
log.info("Program starts")

## Pre-condition
if (DB_USERNAME is None) or (DB_PASSWORD is None):
    log.error("Database username or password is undefined")
    sys.exit(1)

## Pre-processing
#### Connects to the database
escaped_password = urllib.parse.quote_plus(DB_PASSWORD)
host = f"mongodb://{DB_USERNAME}:{escaped_password}@database/{DB_NAME}"
client = pymongo.MongoClient(host)
db = client[DB_NAME]
htmlDataContainer_collection = db["cache.HtmlDataContainer"]
#### Initialize Telegram bot
try:
    bot = telegram.Bot(token=TG_FLASHCARD_BOT_TOKEN)
except telegram.error.InvalidToken:
    log.error("Token for accessing the Telegram bot is invalid")
    sys.exit(1)
except:
    log.error("Encounter an unexpected error")
    sys.exit(1)

## Variables initialization
cachePath = path.join(CACHE_DIRECTORY, "flashcardsManager.pickle")
flashcardUserMessenger = FlashcardUserMessenger(bot=bot, 
    chatId=TG_FLASHCARD_BOT_CHAT_ID)
flashcardDatabaseMessenger = FlashcardDatabaseMessenger(
    dbCollection=htmlDataContainer_collection)

## Main
flashcardsManager = LoadFlashcardsManager(cachePath=cachePath, 
    numJobsPerHour=FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR)
flashcardsManager.ProcessUserInstructions(
    dbMessenger=flashcardDatabaseMessenger,
    userMessenger=flashcardUserMessenger)
flashcardsManager.ShowRandomFlashcardsWithPriority(
    dbMessenger=flashcardDatabaseMessenger,
    userMessenger=flashcardUserMessenger)

## Post-processing
flashcardsManager.Save(cachePath=cachePath)

## Epilogue
log.info("Program ends")
