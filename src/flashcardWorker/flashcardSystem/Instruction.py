import datetime, logging, os, pathlib, sys, time
import enum
from dataclasses import dataclass, InitVar
from enum import Enum
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
class InstructionType(Enum):
    UNKNOWN = enum.auto()
    ADD = enum.auto()
    DELETE = enum.auto()
    CHANGE_FLASHCARD_PRIORITY = enum.auto()
    RESPOND_TO_QUESTION = enum.auto()
    CHANGE_FLASHCARD_SHOWING_FREQUENCY = enum.auto()
    SHOW_FLASHCARD = enum.auto()
    SHOW_INFO = enum.auto()
    CHANGE_TIME_PRIORITY = enum.auto()


@dataclass
class Instruction:
    StringToTypeMap:ClassVar[dict] = {
        "add": InstructionType.ADD,
        "del": InstructionType.DELETE,
        "pri": InstructionType.CHANGE_FLASHCARD_PRIORITY,
        "re": InstructionType.RESPOND_TO_QUESTION,
        "freq": InstructionType.CHANGE_FLASHCARD_SHOWING_FREQUENCY,
        "show": InstructionType.SHOW_FLASHCARD,
        "info": InstructionType.SHOW_INFO,
        "time": InstructionType.CHANGE_TIME_PRIORITY
    }

    Type:InstructionType = InstructionType.UNKNOWN
    Id:int = None
    Key:str = ""
    Value:str = ""
    Remarks:str = None
    text:InitVar[str] = ""
    
    
    def __post_init__(self, text:str) -> None:
        ## Variables initialization
        cls = type(self)
        ## Pre-condition
        if not isinstance(text, str):
            self.Type = InstructionType.UNKNOWN
            return
        
        ## Main
        textSplitted = text.split(";")
        #### To allow the use of ; in textSplitted[3]
        if len(textSplitted) > 4:
            textSplitted[3] = ";".join(textSplitted[3:] )
            del textSplitted[4:]
        #### Remove leading and trailing whitespaces
        textSplitted = [t.strip() for t in textSplitted]
        #### Handle exceptional case
        if not len(textSplitted):
            log.error("Should be unreachable!")
            self.Type = InstructionType.UNKNOWN
            return
        #### Get the instruction type from textSplitted[0]
        userInputTypeStr = textSplitted[0].lower()
        self.Type = cls.StringToTypeMap.get(userInputTypeStr, 
            InstructionType.UNKNOWN)
        #### Case when len(textSplitted) == 1
        if len(textSplitted) == 1:
            if not self.Type == InstructionType.SHOW_INFO:
                self.Type = InstructionType.UNKNOWN
            return
        #### Case when len(textSplitted) in range [2, 4]
        if self.Type == InstructionType.ADD:
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else ""
            self.Remarks = textSplitted[3] if len(textSplitted) == 4 else ""
        elif self.Type == InstructionType.DELETE:
            self.Key = textSplitted[1]
        elif self.Type == InstructionType.CHANGE_FLASHCARD_PRIORITY:
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else "1"
        elif self.Type == InstructionType.RESPOND_TO_QUESTION:
            self.Value = textSplitted[1]
        elif self.Type == InstructionType.CHANGE_FLASHCARD_SHOWING_FREQUENCY:
            self.Value = textSplitted[1]
        elif self.Type == InstructionType.SHOW_FLASHCARD:
            self.Key = textSplitted[1]
        elif self.Type == InstructionType.CHANGE_TIME_PRIORITY:
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else "1"
    
    
if __name__ == "__main__":    
    x = Instruction(text="add;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="del;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="pri;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="re;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="freq;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="show;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="info;x;x explanation;x remarks")
    print(x)
    x = Instruction(text="time;x;x explanation;x remarks")
    print(x)
    
    x = Instruction(Id=1, text=" add  ;  x ; x  explanation;x  remarks   ")
    print(x)
    x = Instruction(Id=1, text="hi;x;x  explanation;x remarks")
    print(x)
