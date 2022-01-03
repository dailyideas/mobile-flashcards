#!/usr/bin/env python
import datetime, logging, os, pathlib, sys, time
import math, signal
from functools import partial
from logging.handlers import RotatingFileHandler

from flashcardSystem.flashcardDatabaseMessenger import FlashcardDatabaseMessenger
from flashcardSystem.flashcardUserMessenger import FlashcardUserMessenger
from flashcardSystem.flashcardsManager import FlashcardsManager


#### #### #### #### #### 
####  Global constants #### 
#### #### #### #### ####
DB_NAME = os.environ.get("APP_DB_NAME")
DB_USERNAME = os.environ.get("APP_DB_USERNAME")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD")
DB_FLASHCARD_COLLECTION_NAME = os.environ.get(
    "APP_DB_FLASHCARD_COLLECTION_NAME")
TG_FLASHCARD_BOT_TOKEN = os.environ.get("APP_TG_FLASHCARD_BOT_TOKEN")
TG_FLASHCARD_BOT_CHAT_ID = int(os.environ.get(
    "APP_TG_FLASHCARD_BOT_CHAT_ID") )
FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR = int(os.environ.get(
    "APP_FLASHCARDS_MANAGER_NUM_JOBS_PER_HOUR") )
RELEASE_MODE = os.environ.get("APP_RELEASE_MODE")

SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__) )
ROOT_DIRECTORY = SCRIPT_DIRECTORY
CACHE_DIRECTORY = os.path.join(ROOT_DIRECTORY, "caches/", SCRIPT_NAME)
LOG_DIRECTORY = os.path.join(ROOT_DIRECTORY, "logs/", SCRIPT_NAME)
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
logPath = os.path.join(LOG_DIRECTORY, SCRIPT_NAME + ".log")
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
def CreateFlashcardDatabaseMessenger(username:str, password:str, 
        dbName:str, flashcardCollectionName:str
    ) -> FlashcardDatabaseMessenger:
    try:
        flashcardDatabaseMessenger = FlashcardDatabaseMessenger(
            username=username, password=password, 
            dbName=dbName, flashcardCollectionName=flashcardCollectionName)
    except:
        log.exception("Error message: ")
        log.critical( (
            f"{CreateFlashcardDatabaseMessenger.__name__} encountered exception "
            f"when creating {FlashcardDatabaseMessenger.__name__}") )
        sys.exit(1)
    return flashcardDatabaseMessenger


def CreateFlashcardUserMessenger(token:str, 
        chatId:int
    ) -> FlashcardUserMessenger:
    try:
        flashcardUserMessenger = FlashcardUserMessenger(token=token, 
            chatId=chatId)
    except:
        log.exception("Error message: ")
        log.critical( (
            f"{CreateFlashcardUserMessenger.__name__} encountered exception "
            f"when creating {FlashcardUserMessenger.__name__}") )
        sys.exit(1)
    return flashcardUserMessenger


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

## Pre-processing
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
cachePath = os.path.join(CACHE_DIRECTORY, "flashcardsManager.pickle")
flashcardUserMessenger = CreateFlashcardUserMessenger(
    token=TG_FLASHCARD_BOT_TOKEN, 
    chatId=TG_FLASHCARD_BOT_CHAT_ID)
flashcardDatabaseMessenger = CreateFlashcardDatabaseMessenger(
    username=DB_USERNAME, password=DB_PASSWORD, dbName=DB_NAME, 
    flashcardCollectionName=DB_FLASHCARD_COLLECTION_NAME)

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
