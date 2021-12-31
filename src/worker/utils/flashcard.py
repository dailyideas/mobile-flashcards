from __future__ import annotations
import datetime, logging, os, pathlib, sys, time
import random
from dataclasses import dataclass, InitVar
from os import path
from typing import ClassVar


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


#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
@dataclass
class Flashcard:
    ID_TAG:ClassVar[str] = "_id"
    KEY_TAG:ClassVar[str] = "key"
    VALUE_TAG:ClassVar[str] = "value"
    REMARKS_TAG:ClassVar[str] = "remarks"
    PRIORITY_TAG:ClassVar[str] = "priority"
    INSERTED_TIME_TAG:ClassVar[str] = "inserted"
    MODIFIED_TIME_TAG:ClassVar[str] = "modified"
    LOWEST_PRIORITY:ClassVar[int] = 0
    HIGHEST_PRIORITY:ClassVar[int] = 99
    Id:int = -1
    Key:str = ""
    Value:str = ""
    Remarks:str = ""
    InsertedTime:int = 0 ## Unix timestamp
    ModifiedTime:int = 0 ## Unix timestamp
    priority:InitVar[int] = HIGHEST_PRIORITY
    
    
    def __post_init__(self, priority:int):
        ## Main
        self._priority = 0
        ## Post-processing
        self.Priority = priority


    @property
    def Priority(self):
        return self._priority
    
    
    @Priority.setter
    def Priority(self, value:int):
        ## Variables initialization
        cls = type(self)
        ## Main
        self._priority = max(cls.LOWEST_PRIORITY, 
            min(value, cls.HIGHEST_PRIORITY) )


    def ToDict(self) -> dict:
        ## Variables initialization
        cls = type(self)
        ## Main
        return {
            cls.ID_TAG: self.Id,
            cls.KEY_TAG: self.Key,
            cls.VALUE_TAG: self.Value,
            cls.REMARKS_TAG: self.Remarks,
            cls.PRIORITY_TAG: self.Priority,
            cls.INSERTED_TIME_TAG: self.InsertedTime,
            cls.MODIFIED_TIME_TAG: self.ModifiedTime
        }
        
        
    @classmethod
    def FromDict(cls, data:dict) -> Flashcard:
        ## Pre-condition
        if not isinstance(data, dict):
            log.error(f"{cls.__name__}.FromDict aborted. Reason: data is not a dict object")
            return None
        for tag in [cls.ID_TAG, cls.KEY_TAG, cls.VALUE_TAG, 
                cls.REMARKS_TAG, cls.PRIORITY_TAG, cls.INSERTED_TIME_TAG,
                cls.MODIFIED_TIME_TAG
            ]:
            if not tag in data:
                log.error(f"{cls.__name__}.FromDict aborted. Reason: Tag \"{tag}\" not found in data")
                return None
        ## Main
        return Flashcard(
            Id=int(data[cls.ID_TAG] ),
            Key=data[cls.KEY_TAG],
            Value=data[cls.VALUE_TAG],
            Remarks=data[cls.REMARKS_TAG],
            InsertedTime=int(data[cls.INSERTED_TIME_TAG] ),
            ModifiedTime=int(data[cls.MODIFIED_TIME_TAG] ),
            priority=int(data[cls.PRIORITY_TAG] )
        )
        
        
    @classmethod
    def GetRandomPriorityValue(cls):
        return random.randint(cls.LOWEST_PRIORITY, cls.HIGHEST_PRIORITY) ## NOTE: Include endpoint
