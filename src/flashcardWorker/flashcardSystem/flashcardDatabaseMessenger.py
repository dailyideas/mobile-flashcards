from __future__ import annotations
import datetime, logging, os, pathlib, sys, time
import csv
from os import path

import pymongo
from pymongo.collection import Collection
from pymongo.command_cursor import CommandCursor


#### #### #### #### #### 
####  Global constants #### 
#### #### #### #### #### 
SCRIPT_NAME = path.basename(__file__).split(".")[0]
SCRIPT_DIRECTORY = path.dirname(path.abspath(__file__) )
ROOT_DIRECTORY = pathlib.Path(SCRIPT_DIRECTORY).parent.absolute()


#### #### #### #### #### 
#### Global variables #### 
#### #### #### #### #### 
#### Logging
log = logging.getLogger(name=SCRIPT_NAME)


#### #### #### #### #### 
#### Global Setups #### 
#### #### #### #### #### 
#### Paths
sys.path.insert(1, str(ROOT_DIRECTORY) )
#### Import local packages
if __name__ == '__main__' or SCRIPT_DIRECTORY in sys.path:
    from flashcard import Flashcard
else:
    from .flashcard import Flashcard
    
    
#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardDatabaseMessenger:
    def __init__(self, dbCollection:Collection) -> None:
        ## Pre-condition
        if not isinstance(dbCollection, Collection):
            log.error("dbCollection has to be a pymongo.collection.Collection object")
            raise ValueError()
        ## Main
        self._dbCollection = dbCollection
    
    
    def InsertFlashcard(self, flashcard:Flashcard) -> bool:
        ## Pre-condition
        #### Do not allow flashcards with the same key exist in the database
        existingFlashcard = self.GetFlashcardByKey(
            key=flashcard.Key)
        if isinstance(existingFlashcard, Flashcard):
            log.warning(f"{self.InsertFlashcard.__name__} failed as a flashcard with the same key already existed in the database. \"Key\": {flashcard.Key}")
            return False
        ## Pre-processing
        currentTimestamp = int(datetime.datetime.now().timestamp() )
        if flashcard.InsertedTime == 0:
            flashcard.InsertedTime = currentTimestamp
        if flashcard.ModifiedTime == 0:
            flashcard.ModifiedTime = currentTimestamp
        ## Main
        largestFlashcardId = self.GetLargestFlashcardId()
        flashcard.Id = largestFlashcardId + 1
        flashcard_dict = flashcard.ToDict()
        insertedDoc = self._dbCollection.insert_one(flashcard_dict)
        return insertedDoc.inserted_id == flashcard.Id
        
        
    def ReplaceFlashcard(self, flashcard:Flashcard) -> bool:
        ## Pre-processing
        currentTimestamp = int(datetime.datetime.now().timestamp() )
        flashcard.ModifiedTime = currentTimestamp
        ## Main
        docFilter = {Flashcard.ID_TAG: flashcard.Id}
        replacement = flashcard.ToDict()
        result = self._dbCollection.replace_one(docFilter, replacement, 
            upsert=False)
        return result.modified_count == 1
        
        
    def DeleteFlashcard(self, flashcard:Flashcard) -> bool:
        docFilter = {Flashcard.ID_TAG: flashcard.Id}
        result = self._dbCollection.delete_one(docFilter)
        return result.deleted_count == 1


    def GetLargestFlashcardId(self) -> int:
        sortingOrder = [ (Flashcard.ID_TAG, pymongo.DESCENDING) ]
        result = self._dbCollection.find_one(sort=sortingOrder)
        latestFlashcard = Flashcard.FromDict(data=result) if \
            isinstance(result, dict) else None
        return -1 if latestFlashcard is None else latestFlashcard.Id
    
    
    def GetFlashcardById(self, id:int) -> Flashcard:
        docFilter = {Flashcard.ID_TAG: id}
        doc = self._dbCollection.find_one(docFilter)
        return Flashcard.FromDict(data=doc) if isinstance(doc, dict) else None
    
    
    def GetFlashcardByKey(self, key:str) -> Flashcard:
        docFilter = {Flashcard.KEY_TAG: key}
        doc = self._dbCollection.find_one(docFilter)
        return Flashcard.FromDict(data=doc) if isinstance(doc, dict) else None
    
    
    def GetFlashcardsByPriority(self, size:int, minPriority:int=0, maxTimestamp:int=None) -> list:
        ## Pre-condition
        if size < 1:
            return []
        ## Pre-processing
        if maxTimestamp is None:
            maxTimestamp = int(datetime.datetime.now().timestamp() )
        ## Variables initializartion
        cls = type(self)
        docFilter = {
            Flashcard.PRIORITY_TAG: {"$gte": minPriority},
            Flashcard.MODIFIED_TIME_TAG: {"$lte": maxTimestamp} }
        docCursor = self._dbCollection.aggregate( [ {"$match": docFilter},
            {"$sample": {"size": size} } ] )
        ## Pre-condition
        if docCursor is None:
            return []
        ## Main
        flashcards = cls._GetFlashcardsFromDatabaseDocuments(
            docCursor=docCursor)
        ## Post-processing
        #### Remove duplicated flashcards
        unique_flashcards = []
        visited = set()
        for flashcard in flashcards:
            flashcard_id = flashcard.Id
            if not flashcard_id in visited:
                unique_flashcards.append(flashcard)
                visited.add(flashcard_id)
        flashcards = unique_flashcards
        ## Return
        return flashcards
    
    
    def FlashcardCount(self) -> int:
        return self._dbCollection.count_documents( {} )
    
    
    def ExportFlashcardsToFile(self, exportPath:str) -> bool:
        ## Pre-condition
        if not os.path.isdir(os.path.dirname(exportPath) ):
            log.error(f"{self.ExportFlashcardsToFile.__name__} found that \"{exportPath}\" is not a valid path")
            return False
        ## Main
        docCursor = self._dbCollection.find( {} )
        flashcards = self._GetFlashcardsFromDatabaseDocuments(
            docCursor=docCursor)
        exportingData = [card.ToDict() for card in flashcards]
        """ Convert list of dictionaries to a csv file?
        
            Reference
            ---- ----
            1. https://stackoverflow.com/a/3087011
        """
        keys = exportingData[0].keys()
        with open(exportPath, "w", newline="") as f:
            csvDictWriter = csv.DictWriter(f, keys)
            csvDictWriter.writeheader()
            csvDictWriter.writerows(exportingData)
        log.info(f"{self.ExportFlashcardsToFile.__name__} exported the flashcards to \"{exportPath}\"")
        return True


    def ImportFlashcardsFromFile(self, filePath:str) -> bool:
        ## Pre-condition
        if not os.path.isfile(filePath):
            return False
        ## Variables initialization
        """ Read dict from csv file
        
            Reference
            ---- ----
            1. https://stackoverflow.com/a/6740968
        """
        importedDataList = []
        with open(filePath, "r") as f:
            csvReader = csv.reader(f)
            keys = next(csvReader)
            for row in csvReader:
                dictData = {}
                for key, value in zip(keys, row):
                    dictData[key] = value
                importedDataList.append(dictData)
        ## Main
        numInsertedFlashcards = 0
        for item in importedDataList:
            ## Variables initialization
            flashcard = Flashcard.FromDict(data=item)
            ## Pre-condition
            if not isinstance(flashcard, Flashcard):
                log.warning(f"{self.ImportFlashcardsFromFile.__name__} found an item which cannot be converted to a Flashcard object")
                continue
            ## Main
            isSuccess = self.InsertFlashcard(flashcard=flashcard)
            if isSuccess:
                numInsertedFlashcards += 1
            else:
                log.error(f"{self.ImportFlashcardsFromFile.__name__} failed to insert a flashcard. \"Key\": {flashcard.Key}")
        log.info(f"{self.ImportFlashcardsFromFile.__name__} imported {numInsertedFlashcards} flashcards")
        return True


    @classmethod
    def _GetFlashcardsFromDatabaseDocuments(cls, 
            docCursor:CommandCursor
        ) -> list:
        flashcards = []
        for doc in docCursor:
            ## Variables initialization
            newFlashcard = Flashcard.FromDict(data=doc)
            ## Pre-condition
            if newFlashcard is None:
                continue
            ## Main
            flashcards.append(newFlashcard)
        return flashcards
