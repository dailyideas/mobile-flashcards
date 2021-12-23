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
    from Instruction import Instruction
else:
    from .Flashcard import Flashcard
    from .Instruction import Instruction


#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardUserMessenger:
    def __init__(self, bot:telegram.Bot, chatId:int) -> None:
        ## Pre-condition
        assert isinstance(bot, telegram.Bot)
        assert isinstance(chatId, int)
        ## Main
        self._bot = bot
        self._chatId = chatId ## int
    
    
    def ShowFlashcard(self, flashcard:Flashcard) -> bool:
        ## Variables initialization
        cls = type(self)
        ## Main
        texts = cls._FlashcardToString(flashcard=flashcard)
        return self.ShowCustomTexts(customTexts=texts)
        
        
    def GetUserInstructions(self, latestUpdateId:int=None) -> list:
        ## Inner functions
        def _GetInstruction(update:telegram.Update) -> None:
            ## Prologue
            log.info( (
                f"Got an update from user. "
                f"\"updateId\": {update.update_id}, "
                f"\"text\"={update.message.text}"
            ) )
            ## Variables intialization
            updateId = update.update_id
            text = update.message.text
            ## Pre-condition
            if not isinstance(updateId, int):
                log.error(f"{self.GetUserInstructions.__name__} got an updateId which is not an int")
                return
            if not isinstance(text, str):
                log.error(f"{self.GetUserInstructions.__name__} got a text which is not a string")
                return
            instruction = Instruction(Id=updateId, text=text)
            return instruction
        ## Main
        if latestUpdateId is None:
            updates = self._bot.get_updates(timeout=2.)
        else:
            nextUpdateId = latestUpdateId + 1
            updates = self._bot.get_updates(offset=nextUpdateId, timeout=2.)
        instructions = []
        for update in updates:
            newInstruction = _GetInstruction(update=update)
            instructions.append(newInstruction)
        return instructions
    
    
    def ShowCustomTexts(self, customTexts:str) -> bool:
        result = self._bot.send_message(text=customTexts, 
            chat_id=self._chatId,
            parse_mode=telegram.constants.PARSEMODE_MARKDOWN_V2,
            disable_notification=True, timeout=10)
        return isinstance(result, telegram.Message)


    @classmethod
    def _FlashcardToString(cls, flashcard:Flashcard):
        """ Characters to escape in Markdown
        
            Reference
            ---- ----
            1. https://www.markdownguide.org/basic-syntax/#characters-you-can-escape
        """
        specialCharactersTranslation = str.maketrans( {
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
        """ Translate strings in Python
        
            Reference
            ---- ----
            1. https://stackoverflow.com/a/18935765
        """
        key = flashcard.Key.translate(specialCharactersTranslation)
        value = flashcard.Value.translate(specialCharactersTranslation)
        remarks = flashcard.Remarks.translate(specialCharactersTranslation)
        return (
            f"*{key}*\n\n"
            f"{value}\n\n"
            f"{remarks}\n\n"
            f"{flashcard.Id}    {flashcard.Priority}")
