import datetime, logging, os, pathlib, sys, time
import math, signal, urllib
from functools import partial
from logging.handlers import RotatingFileHandler
from os import path

import pymongo
import telegram

from flashcardSystem.flashcardDatabaseMessenger import FlashcardDatabaseMessenger
from flashcardSystem.flashcardsManager import FlashcardsManager
from flashcardSystem.flashcardUserMessenger import FlashcardUserMessenger


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
    
    
def ExitHandler(flashcardsManager:FlashcardsManager, cachePath:str, 
        signum, frame
    ) -> None:
    flashcardsManager.Save(cachePath=cachePath)
    log.info(f"Program exits on the receipt of signal {signum}")


#### #### #### #### #### 
#### Main #### 
#### #### #### #### #### 
## Prologue
log.info("Program starts")

## Pre-condition
#### Ensure both username and password exist for database accessing 
if (DB_USERNAME is None) or (DB_PASSWORD is None):
    log.error("Database username or password is undefined")
    sys.exit(1)

## Pre-processing
#### Connects to the database
escaped_password = urllib.parse.quote_plus(DB_PASSWORD)
host = f"mongodb://{DB_USERNAME}:{escaped_password}@database/{DB_NAME}"
client = pymongo.MongoClient(host)
db = client[DB_NAME]
flashcardCollection = db["flashcardCollection"]
#### Initialize Telegram bot
try:
    bot = telegram.Bot(token=TG_FLASHCARD_BOT_TOKEN)
except telegram.error.InvalidToken:
    log.error("Token for accessing the Telegram bot is invalid")
    sys.exit(1)
except:
    log.error("Encounter an unexpected error")
    sys.exit(1)
#### Ensure number of jobs per hour is valid
if FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR < 1:
    FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR = 1
    log.warning("Number of jobs per hour must >= 1. It is now set to 1")
if FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR > 60:
    FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR = 60
    log.warning("Number of jobs per hour must <= 60. It is now set to 60")
if 60 % FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR != 0:
    FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR = \
        60 // math.ceil(60 / FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR)
    log.warning(f"60 must be divisible by the number of jobs. It is now set to {FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR}")

## Variables initialization
cachePath = path.join(CACHE_DIRECTORY, "flashcardsManager.pickle")
flashcardUserMessenger = FlashcardUserMessenger(bot=bot, 
    chatId=TG_FLASHCARD_BOT_CHAT_ID)
flashcardDatabaseMessenger = FlashcardDatabaseMessenger(
    dbCollection=flashcardCollection)

## Main
#### Obtain FlashcardsManager
flashcardsManager = LoadFlashcardsManager(cachePath=cachePath, 
    numJobsPerHour=FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR)
#### Add signal handling
signal.signal(signal.SIGTERM, 
    partial(ExitHandler, flashcardsManager, cachePath) )
#### Endless loop
minuteStepsPerJob = 60 // FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR
lastLoopDatetime = datetime.datetime.now()
while True:
    ## Variables initialization
    lastLoopMinute = lastLoopDatetime.minute
    currentDatetime = datetime.datetime.now()
    currentMinute = currentDatetime.minute
    ## Main
    #### Periodically run FlashcardsManager.ShowRandomFlashcardsWithPriority
    if currentMinute != lastLoopMinute and currentMinute % minuteStepsPerJob == 0:
        flashcardsManager.ShowRandomFlashcardsWithPriority(
            dbMessenger=flashcardDatabaseMessenger,
            userMessenger=flashcardUserMessenger)
    #### Save the settings of FlashcardsManager at the start of each day
    if currentDatetime.date() != lastLoopDatetime.date():
        flashcardsManager.Save(cachePath=cachePath)
    #### Check for user inputs
    flashcardsManager.ProcessUserInstructions(
        dbMessenger=flashcardDatabaseMessenger,
        userMessenger=flashcardUserMessenger)
    ## Post-processing
    lastLoopDatetime = currentDatetime
    #### Useless short sleep
    time.sleep(1)

## Epilogue
log.info("Program ends")
