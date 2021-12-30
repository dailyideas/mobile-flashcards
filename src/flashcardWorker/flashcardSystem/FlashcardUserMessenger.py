from __future__ import annotations
import datetime, logging, os, pathlib, sys, time
from os import path

import telegram


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
    from Instruction import InstructionType, Instruction
else:
    from .Flashcard import Flashcard
    from .Instruction import InstructionType, Instruction


#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardUserMessenger:
    """ Characters to escape in Markdown
    
        Reference
        ---- ----
        1. https://www.markdownguide.org/basic-syntax/#characters-you-can-escape
    """
    SpecialCharactersTranslation = str.maketrans( {
        "\\": r"\\",
        "`": r"\`",
        "*":  r"\*",
        "_":  r"\_",
        "{":  r"\{",
        "}":  r"\}",
        "[":  r"\[",
        "]":  r"\]",
        "<":  r"\<",
        ">":  r"\>",
        "(":  r"\(",
        ")":  r"\)",
        "#":  r"\#",
        "+":  r"\+",
        "-":  r"\-",
        ".":  r"\.",
        "!":  r"\!",
        "|":  r"\|"} )
    
    
    def __init__(self, bot:telegram.Bot, chatId:int) -> None:
        ## Pre-condition
        if not isinstance(bot, telegram.Bot):
            log.error("bot must be a telegram.Bot object")
            raise ValueError()
        if not isinstance(chatId, int):
            log.error("chatId must be an int")
            raise ValueError()
        ## Main
        self._bot = bot
        self._chatId = chatId ## int
    
    
    def ShowFlashcard(self, flashcard:Flashcard, infoToShow:list=[],
            prefix:str="", suffix:str=""
        ) -> bool:
        ## Variables initialization
        cls = type(self)
        ## Main
        text = cls._FlashcardToString(flashcard=flashcard, 
            infoToShow=infoToShow)
        text = f"{prefix}{text}{suffix}"
        return self.ShowCustomText(text=text, autoEscape=False)


    def ShowCustomText(self, text:str, autoEscape:bool) -> bool:
        if autoEscape:
            text = text.translate(self.SpecialCharactersTranslation)
        result = self._bot.send_message(text=text, 
            chat_id=self._chatId,
            parse_mode=telegram.constants.PARSEMODE_MARKDOWN_V2,
            disable_notification=True, timeout=10)
        return isinstance(result, telegram.Message)
        
        
    def GetUserInstructions(self, latestInstructionId:int=None) -> list:
        ## Inner functions
        def _GetInstruction(update:telegram.Update) -> Instruction:
            ## Variables intialization
            updateId = update.update_id
            if isinstance(update.message, telegram.Message) and \
                isinstance(update.message.text, str):
                text = update.message.text
            elif isinstance(update.edited_message, telegram.Message) and \
                isinstance(update.edited_message.text, str):
                text = update.edited_message.text
            else:
                text = ""
            log.info( (
                f"Got an update from user. "
                f"\"updateId\": {updateId}, "
                f"\"text\"={text}"
            ) )
            ## Pre-condition
            if not isinstance(updateId, int):
                log.error(f"{self.GetUserInstructions.__name__} got an updateId which is not an int")
                return Instruction(Type=InstructionType.UNKNOWN)
            if not isinstance(text, str):
                log.error(f"{self.GetUserInstructions.__name__} got a text which is not a string")
                return Instruction(Type=InstructionType.UNKNOWN)
            instruction = Instruction(Id=updateId, text=text)
            return instruction
        
        ## Main
        if latestInstructionId is None:
            updates = self._bot.get_updates(timeout=2.)
        else:
            nextUpdateId = latestInstructionId + 1
            updates = self._bot.get_updates(offset=nextUpdateId, timeout=2.)
        instructions = []
        for update in updates:
            newInstruction = _GetInstruction(update=update)
            instructions.append(newInstruction)
        return instructions


    @classmethod
    def _FlashcardToString(cls, flashcard:Flashcard, infoToShow:list=[] ):
        ## Pre-processing
        if not isinstance(infoToShow, list):
            infoToShow = [infoToShow]
        ## Main
        """ Translate strings in Python
        
            Reference
            ---- ----
            1. https://stackoverflow.com/a/18935765
        """
        result = ""
        if Flashcard.KEY_TAG in infoToShow:
            key = flashcard.Key.translate(
                cls.SpecialCharactersTranslation)
            result += f"*{key}*\n\n"
        if Flashcard.VALUE_TAG in infoToShow:
            value = flashcard.Value.translate(
                cls.SpecialCharactersTranslation)
            result += f"{value}\n\n"
        if Flashcard.REMARKS_TAG in infoToShow:
            remarks = flashcard.Remarks.translate(
                cls.SpecialCharactersTranslation)
            result += f"{remarks}\n\n"
        if Flashcard.ID_TAG in infoToShow:
            result += f"{flashcard.Id}\n"
        if Flashcard.PRIORITY_TAG in infoToShow:
            result += f"{flashcard.Priority}\n"
        result = result.rstrip("\n")
        return result
        