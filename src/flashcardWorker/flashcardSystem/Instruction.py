import datetime, logging, os, pathlib, sys, time
import enum
from dataclasses import dataclass, InitVar
from enum import Enum
from os import path


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
    Type:InstructionType = InstructionType.UNKNOWN
    Id:int = None
    Key:str = ""
    Value:str = ""
    Remarks:str = None
    text:InitVar[str] = ""
    
    
    def __post_init__(self, text:str) -> None:
        ## Pre-condition
        if not isinstance(text, str):
            self.Type = InstructionType.UNKNOWN
            return
        
        ## Main
        textSplitted = text.split(";")
        if len(textSplitted) > 4:
            textSplitted[3] = ";".join(textSplitted[3:] )
            del textSplitted[4:]
        textSplitted = [t.strip() for t in textSplitted]
        
        if len(textSplitted) == 1:
            if textSplitted[0] == "info":
                self.Type = InstructionType.SHOW_INFO
            else:
                self.Type = InstructionType.UNKNOWN
            return
        
        if textSplitted[0] == "add":
            self.Type = InstructionType.ADD
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else ""
            self.Remarks = textSplitted[3] if len(textSplitted) == 4 else ""
        elif textSplitted[0] == "del":
            self.Type = InstructionType.DELETE
            self.Key = textSplitted[1]
        elif textSplitted[0] == "pri":
            self.Type = InstructionType.CHANGE_FLASHCARD_PRIORITY
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else "1"
        elif textSplitted[0] == "re":
            self.Type = InstructionType.RESPOND_TO_QUESTION
            self.Value = textSplitted[1]
        elif textSplitted[0] == "freq":
            self.Type = InstructionType.CHANGE_FLASHCARD_SHOWING_FREQUENCY
            self.Value = textSplitted[1]
        elif textSplitted[0] == "show":
            self.Type = InstructionType.SHOW_FLASHCARD
            self.Key = textSplitted[1]
        elif textSplitted[0] == "time":
            self.Type = InstructionType.CHANGE_TIME_PRIORITY
            self.Key = textSplitted[1]
            self.Value = textSplitted[2] if len(textSplitted) >= 3 else "1"
    
    
if __name__ == "__main__":
    x = Instruction(Id=1, text="add;x;Explanation of x;Remarks of x")
    print(x)
    y = Instruction(Id=1, text="Add;y;Explanation of y;Remarks of y")
    print(y)
