from __future__ import annotations
import datetime, logging, os, pathlib, sys, time
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
    from Flashcard import Flashcard
else:
    from .Flashcard import Flashcard
    
    
#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardDatabaseMessenger:
    def __init__(self, dbCollection:Collection) -> None:
        ## Pre-condition
        assert isinstance(dbCollection, Collection)
        ## Main
        self._dbCollection = dbCollection
    
    
    def InsertFlashcard(self, flashcard:Flashcard) -> bool:
        ## Pre-processing
        currentTimestamp = int(datetime.datetime.now().timestamp() )
        flashcard.InsertionTime = currentTimestamp
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
        return flashcards
    
    
    def FlashcardCount(self) -> int:
        return self._dbCollection.count_documents( {} )


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
