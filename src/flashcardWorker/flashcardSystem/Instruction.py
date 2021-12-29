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
    SHOW_HELP = enum.auto()


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
        "time": InstructionType.CHANGE_TIME_PRIORITY,
        "help": InstructionType.SHOW_HELP
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
            validTypes = [InstructionType.SHOW_HELP, 
                InstructionType.SHOW_INFO]
            if not self.Type in validTypes:
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
        elif self.Type == InstructionType.SHOW_HELP:
            self.Key = textSplitted[1]


    @classmethod
    def GetHelp(cls):
        return (
            f"List of available instructions:\n"
            f"add :  add flashcard\n"
            f"del :  delete flashcard\n"
            f"pri :  increase/decrease the priority of flashcard\n"
            f"freq :  set the flashcard showing frequency per day\n"
            f"show :  show a specific flashcard\n"
            f"info :  display basic information of the flashcard system\n"
            f"time :  increase/decrease the time of day priority for flashcard showing\n"
        )
        
        
    @classmethod
    def GetInstructionUsage(cls, key:str):
        instructionType = cls.StringToTypeMap.get(key, 
            InstructionType.UNKNOWN)
        if instructionType == InstructionType.ADD:
            return r"add ; <key> ; <value> ; <remarks>"
        elif instructionType == InstructionType.DELETE:
            return r"del ; <id / key of flashcard>"
        elif instructionType == InstructionType.CHANGE_FLASHCARD_PRIORITY:
            return r"pri ; <id / key of flashcard> ; <change>"
        elif instructionType == InstructionType.RESPOND_TO_QUESTION:
            return r"This command is not availavle yet"
        elif instructionType == InstructionType.CHANGE_FLASHCARD_SHOWING_FREQUENCY:
            return r"freq ; <value>"
        elif instructionType == InstructionType.SHOW_FLASHCARD:
            return r"show ; <id / key of flashcard>"
        elif instructionType == InstructionType.SHOW_INFO:
            return r"info"
        elif instructionType == InstructionType.CHANGE_TIME_PRIORITY:
            return r"time ; <hour in range [0, 23]> ; <change>"
        else:
            return f"{key} is not an available command"
    
    
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
