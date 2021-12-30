import datetime, logging, os, sys, time
import urllib
from logging.handlers import RotatingFileHandler

import pymongo

from flashcardSystem.FlashcardDatabaseMessenger import FlashcardDatabaseMessenger


#### #### #### #### #### 
####  Global constants #### 
#### #### #### #### ####
DB_NAME = os.environ.get("APP_DB_NAME")
DB_USERNAME = os.environ.get("APP_DB_USERNAME")
DB_PASSWORD = os.environ.get("APP_DB_PASSWORD")
RELEASE_MODE = os.environ.get("APP_RELEASE_MODE")

SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__) )
ROOT_DIRECTORY = SCRIPT_DIRECTORY
LOG_DIRECTORY = os.path.join(ROOT_DIRECTORY, "logs/", SCRIPT_NAME)
EXPORT_DIRECTORY = os.path.join(ROOT_DIRECTORY, "exports/", SCRIPT_NAME)
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
os.makedirs(LOG_DIRECTORY, exist_ok=True)
os.makedirs(EXPORT_DIRECTORY, exist_ok=True)
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

## Variables initialization
flashcardDatabaseMessenger = FlashcardDatabaseMessenger(
    dbCollection=flashcardCollection)

currentDatetime_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
exportFileName = f"ExportedFlashcards_{currentDatetime_str}.csv"
exportPath = os.path.join(EXPORT_DIRECTORY, exportFileName)
flashcardDatabaseMessenger.ExportFlashcardsToFile(exportPath=exportPath)

## Epilogue
log.info("Program ends")
