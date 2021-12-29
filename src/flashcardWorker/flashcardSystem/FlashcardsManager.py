from __future__ import annotations
import datetime, logging, os, pathlib, sys, time
import math, pickle
from os import path

import numpy as np


#### #### #### #### #### 
####  Global constants #### 
#### #### #### #### #### 
SCRIPT_NAME = path.basename(__file__).split(".")[0]
SCRIPT_DIRECTORY = path.dirname(path.abspath(__file__) )
ROOT_DIRECTORY = pathlib.Path(SCRIPT_DIRECTORY).parent.absolute()
HOURS_IN_DAY = 24


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
    from Common import TryStringToInt, FlipBiasedCoin
    from Flashcard import Flashcard
    from FlashcardDatabaseMessenger import FlashcardDatabaseMessenger
    from FlashcardUserMessenger import FlashcardUserMessenger
    from Instruction import InstructionType, Instruction
else:
    from .Common import TryStringToInt, FlipBiasedCoin
    from .Flashcard import Flashcard
    from .FlashcardDatabaseMessenger import FlashcardDatabaseMessenger
    from .FlashcardUserMessenger import FlashcardUserMessenger
    from .Instruction import InstructionType, Instruction


#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardsManager:
    LOWEST_TIME_PRIORITY = 0
    HIGHEST_TIME_PRIORITY = 999
    
    def __init__(self, numJobsPerHour:int=12) -> None:
        ## Variables initialization
        cls = type(self)
        ## Main
        self._numJobsPerHour = numJobsPerHour
        self._lastUpdateDatetime = None
        self._bot_latestUpdateId = None ## int
        self._questionToAnswer = -1
        self._questionAskedDatetime = datetime.datetime.now()
        self._dailyFlashcardShowingFrequency = 10
        self._timeOfDayPriorities = np.array( [
                0, 0, 0, 0, 0, 0,
                1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1,
                1, 1, 1, 1, 1, 1
            ], dtype=int) * cls.HIGHEST_TIME_PRIORITY // 2
        self._timeOfDayShowFlashcardsDistribution = \
            self._GenerateTimeOfDayShowFlashcardsDistribution()
        self._withinHourShowFlashcardsDistribution = \
            self._GenerateWithinHourShowFlashcardsDistribution()
        ## Post-processing
        self._lastUpdateDatetime = datetime.datetime.now()


    @property
    def NumJobsPerHour(self) -> int:
        return self._numJobsPerHour
    
    
    @NumJobsPerHour.setter
    def NumJobsPerHour(self, value:int):
        if self._numJobsPerHour != value:
            self._numJobsPerHour = value
            self._withinHourShowFlashcardsDistribution = \
                self._GenerateWithinHourShowFlashcardsDistribution()
                
                
    @property
    def FlashcardShowingFrequency(self) -> int:
        return self._dailyFlashcardShowingFrequency
    
    
    @FlashcardShowingFrequency.setter
    def FlashcardShowingFrequency(self, value:int):
        if self._dailyFlashcardShowingFrequency != value:
            ## Only reset the variables below if the value is changed
            self._dailyFlashcardShowingFrequency = value
            self._timeOfDayShowFlashcardsDistribution = \
                self._GenerateTimeOfDayShowFlashcardsDistribution()
            self._withinHourShowFlashcardsDistribution = \
                self._GenerateWithinHourShowFlashcardsDistribution()
        
        
    def Save(self, cachePath:str) -> None:
        ## Variables initialization
        cls = type(self)
        ## Main
        with open(cachePath, "wb") as fhandler:
            pickle.dump(self, fhandler)
        ## Epilogue
        log.info(f"Stored a {cls.__name__} at {cachePath}")
        
        
    @classmethod
    def Load(cls, cachePath:str) -> FlashcardsManager:
        ## Pre-condition
        if not path.isfile(cachePath):
            log.warning(f"{cls.__name__}.Load cannot find the cache \"{cachePath}\"")
            return None
        ## Main
        payload = None
        with open(cachePath, "rb") as fhandler:
            payload = pickle.load(fhandler)
        if not isinstance(payload, cls):
            log.error(f"Instance loaded from \"{cachePath}\" is not an \"{cls.__name__}\"")
            return None
        ## Epilogue
        log.info(f"Loaded a {cls.__name__} instance from \"{cachePath}\"")
        return payload


    def ProcessUserInstructions(self, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> None:
        instructions = userMessenger.GetUserInstructions(
            latestUpdateId=self._bot_latestUpdateId)
        for instruction in instructions:
            self._HandleInstruction(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        ## Post-processing
        if len(instructions):
            #### Store latest update_id for next telegram.Bot.get_updates
            self._bot_latestUpdateId = instructions[-1].Id
            #### Possible increase of priority at current hour
            currentHour = datetime.datetime.now().hour
            priorityChange = FlipBiasedCoin(pOf1=0.6)
            self._ChangeTimePriority(timeIdx=currentHour, 
                change=priorityChange)
            
            
    def ShowRandomFlashcardsWithPriority(self,
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> None:    
        ## Inner functions
        def _ShowFlashcardAndReducePriority(flashcard:Flashcard) -> bool:
            ## Main
            isSuccess = self.ShowFlashcard_MajorFields(
                userMessenger=userMessenger,
                flashcard=flashcard)
            ## Post-processing
            if isSuccess:
                log.info(f"{_ShowFlashcardAndReducePriority.__name__} showed flashcard \"{flashcard.Key}\" to user")
                #### Update the priority of the flashcard
                flashcard.Priority -= 1
                isSuccess = dbMessenger.ReplaceFlashcard(flashcard=flashcard)
                if isSuccess is False:
                    log.error(f"{_ShowFlashcardAndReducePriority.__name__} found {dbMessenger.ReplaceFlashcard} failed")
            else:
                log.warning(f"{_ShowFlashcardAndReducePriority.__name__} failed to show flashcard \"{flashcard.Key}\" to user")
            return isSuccess
        
        def _ShowFlashcardAsQuiz(flashcard:Flashcard) -> bool:
            ## Main
            isSuccess = self.ShowFlashcard_ValueOnly(
                userMessenger=userMessenger,
                flashcard=flashcard, 
                prefix="What is the key of value: ")
            ## Post-processing
            if isSuccess:
                log.info(f"{_ShowFlashcardAndReducePriority.__name__} showed flashcard \"{flashcard.Key}\" to user, as quiz")
                #### Record the question being asked
                self._questionToAnswer = flashcard.Id
                self._questionAskedDatetime = datetime.datetime.now()
            else:
                log.warning(f"{_ShowFlashcardAndReducePriority.__name__} failed to show flashcard \"{flashcard.Key}\" to user")
            return isSuccess
        
        ## Pre-processing
        self._UpdateMetadata()
        ## Main
        currentTime = datetime.datetime.now()
        currentIdxInHour = currentTime.minute * self._numJobsPerHour // 60
        numCardsToShow = int(
            self._withinHourShowFlashcardsDistribution[currentIdxInHour] )
        minPriority = Flashcard.GetRandomPriorityValue()
        maxTimestamp = (currentTime - datetime.timedelta(days=1) ).timestamp()
        maxTimestamp = int(maxTimestamp)
        flashcards = dbMessenger.GetFlashcardsByPriority(
            size=numCardsToShow, minPriority=minPriority,
            maxTimestamp=maxTimestamp)
        if numCardsToShow > 0 and len(flashcards) == 0:
            log.warning(f"{self.ShowRandomFlashcardsWithPriority.__name__} found no valid flashcard to be shown")
            return
        showedFlashcardsId = []
        for flashcard in flashcards:
            ## Pre-condition
            if flashcard.Id in showedFlashcardsId:
                continue
            ## Main
            _ShowFlashcardAndReducePriority(flashcard=flashcard)
            ## Post-processing
            showedFlashcardsId.append(flashcard.Id)


    def _GenerateTimeOfDayShowFlashcardsDistribution(self) -> np.ndarray:
        timeOfDayPrioritiesSum = np.sum(self._timeOfDayPriorities)
        timeOfDayProbabilities = [i / timeOfDayPrioritiesSum for i in \
            self._timeOfDayPriorities]
        showFlashcardMoments = np.random.choice(HOURS_IN_DAY, 
            self._dailyFlashcardShowingFrequency, replace=True, 
            p=timeOfDayProbabilities)
        showFlashcardsDistribution = np.zeros( (HOURS_IN_DAY,), dtype=int)
        for i in showFlashcardMoments:
            showFlashcardsDistribution[i] += 1
        ## Epilogue
        log.info(f"TimeOfDayShowFlashcardsDistribution: {showFlashcardsDistribution.tolist() }")
        return showFlashcardsDistribution


    def _GenerateWithinHourShowFlashcardsDistribution(self) -> np.ndarray:
        currentHour = datetime.datetime.now().hour
        flashcardsToShow = \
            self._timeOfDayShowFlashcardsDistribution[currentHour]
        showFlashcardMoments = np.random.choice(self._numJobsPerHour, flashcardsToShow, 
            replace=True)
        showFlashcardsDistribution = np.zeros( (self._numJobsPerHour,), dtype=int)
        for i in showFlashcardMoments:
            showFlashcardsDistribution[i] += 1
        ## Epilogue
        log.info(f"WithinHourShowFlashcardsDistribution: {showFlashcardsDistribution.tolist() }")
        return showFlashcardsDistribution
        
        
    def _UpdateMetadata(self) -> None:
        currentDatetime = datetime.datetime.now()
        if self._lastUpdateDatetime.date() != currentDatetime.date():
            self._timeOfDayShowFlashcardsDistribution = \
                self._GenerateTimeOfDayShowFlashcardsDistribution()
        if self._lastUpdateDatetime.hour != currentDatetime.hour:
            self._withinHourShowFlashcardsDistribution = \
                self._GenerateWithinHourShowFlashcardsDistribution()
        if self._questionToAnswer != -1:
            daysPassedFromLastQuestion = \
                (currentDatetime - self._questionAskedDatetime).days
            if daysPassedFromLastQuestion >= 1:
                self._questionToAnswer = -1
        self._lastUpdateDatetime = currentDatetime
        
        
    @classmethod
    def _DisplayCustomTextToUser(cls, userMessenger:FlashcardUserMessenger, 
            text:str
        ) -> bool:
        isSuccess = userMessenger.ShowCustomTexts(customTexts=text)
        if isSuccess is False:
            log.error(f"{cls._DisplayCustomTextToUser.__name__} failed to show custom text to user")
        return isSuccess


    @classmethod
    def ShowFlashcard_MajorFields(cls, userMessenger:FlashcardUserMessenger,
            flashcard:Flashcard, prefix:str="", suffix:str=""
        ) -> bool:
        infoToShow = [
            Flashcard.KEY_TAG,
            Flashcard.VALUE_TAG,
            Flashcard.ID_TAG,
            Flashcard.PRIORITY_TAG,
        ]
        if isinstance(flashcard.Remarks, str) and len(flashcard.Remarks):
            infoToShow.append(Flashcard.REMARKS_TAG)
        isSuccess = userMessenger.ShowFlashcard(flashcard=flashcard, 
            infoToShow=infoToShow, prefix=prefix, suffix=suffix)
        if isSuccess is False:
            log.error(f"{cls.ShowFlashcard_MajorFields.__name__} found {userMessenger.ShowFlashcard.__name__} failed")
        return isSuccess


    @classmethod
    def ShowFlashcard_KeyOnly(cls, userMessenger:FlashcardUserMessenger, 
            flashcard:Flashcard, prefix:str="", suffix:str=""
        ) -> bool:
        infoToShow = [Flashcard.KEY_TAG]
        isSuccess = userMessenger.ShowFlashcard(flashcard=flashcard, 
            infoToShow=infoToShow, prefix=prefix, suffix=suffix)
        if isSuccess is False:
            log.error(f"{cls.ShowFlashcard_KeyOnly.__name__} found {userMessenger.ShowFlashcard.__name__} failed")
        return isSuccess
        
        
    @classmethod
    def ShowFlashcard_ValueOnly(cls, userMessenger:FlashcardUserMessenger, 
            flashcard:Flashcard, prefix:str="", suffix:str=""
        ) -> bool:
        infoToShow = [Flashcard.VALUE_TAG]
        isSuccess = userMessenger.ShowFlashcard(flashcard=flashcard, 
            infoToShow=infoToShow, prefix=prefix, suffix=suffix)
        if isSuccess is False:
            log.error(f"{cls.ShowFlashcard_ValueOnly.__name__} found {userMessenger.ShowFlashcard.__name__} failed")
        return isSuccess
        
        
    @classmethod
    def _GetFlashcardFromDatabase(cls, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger
        ) -> Flashcard:
        key = TryStringToInt(s=instruction.Key)
        if isinstance(key, int):
            return dbMessenger.GetFlashcardById(id=key)
        else:
            return dbMessenger.GetFlashcardByKey(key=key)


    @classmethod
    def _InsertFlashcard(cls, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        existingFlashcard = dbMessenger.GetFlashcardByKey(
            key=instruction.Key)
        if isinstance(existingFlashcard, Flashcard):
            #### Update value & remarks, and restore priority to the highest
            existingFlashcard.Value = instruction.Value
            existingFlashcard.Priority = Flashcard.HIGHEST_PRIORITY
            if not instruction.Remarks is None:
                existingFlashcard.Remarks = instruction.Remarks
            isSuccess = dbMessenger.ReplaceFlashcard(
                flashcard=existingFlashcard)
            if isSuccess:
                cls.ShowFlashcard_MajorFields(
                    userMessenger=userMessenger,
                    flashcard=existingFlashcard, 
                    prefix="Updated existing:\n")
                log.info(f"{cls._InsertFlashcard.__name__} updated a flashcard. \"Key\": {existingFlashcard.Key}")
            else:
                log.error(f"{cls._InsertFlashcard.__name__} found {dbMessenger.ReplaceFlashcard} failed. \"Key\": {existingFlashcard.Key}")
        else:
            newFlashcard = Flashcard(
                Key=instruction.Key,
                Value=instruction.Value,
                Remarks=instruction.Remarks,
                priority=Flashcard.HIGHEST_PRIORITY
            )
            isSuccess = dbMessenger.InsertFlashcard(flashcard=newFlashcard)
            if isSuccess:
                cls.ShowFlashcard_MajorFields(
                    userMessenger=userMessenger,
                    flashcard=newFlashcard, 
                    prefix="Inserted new:\n")
                log.info(f"{cls._InsertFlashcard.__name__} inserted a flashcard. \"Key\": {newFlashcard.Key}")
            else:
                log.warning(f"{cls._InsertFlashcard.__name__} found {dbMessenger.InsertFlashcard} failed. \"Key\": {newFlashcard.Key}")
        return isSuccess


    @classmethod
    def _DeleteFlashcard(cls, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        ## Variables initialization
        targetFlashcard = cls._GetFlashcardFromDatabase(
            instruction=instruction, dbMessenger=dbMessenger)
        ## Pre-condition
        if targetFlashcard is None:
            cls._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot find the flashcard to delete")
            log.warning(f"{cls._DeleteFlashcard.__name__} could not find the flashcard to delete. \"Key\": {instruction.Key}")
            return False
        ## Main
        isSuccess = dbMessenger.DeleteFlashcard(flashcard=targetFlashcard)
        ## Epilogue
        if isSuccess:
            cls.ShowFlashcard_KeyOnly(
                userMessenger=userMessenger,
                flashcard=targetFlashcard, 
                prefix="Deleted: ")
            log.info(f"{cls._DeleteFlashcard.__name__} deleted a flashcard. \"Key\": {targetFlashcard.Key}")
        else:
            log.warning(f"{cls._DeleteFlashcard.__name__} found {dbMessenger.DeleteFlashcard} failed. \"Key\": {targetFlashcard.Key}")
        return isSuccess
    
    
    @classmethod
    def _ChangeFlashcardPriority(cls, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        ## Variables initialization
        targetFlashcard = cls._GetFlashcardFromDatabase(
            instruction=instruction, dbMessenger=dbMessenger)
        change = TryStringToInt(instruction.Value)
        ## Pre-condition
        if targetFlashcard is None:
            cls._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot find the flashcard for priority change")
            log.warning(f"{cls._ChangeFlashcardPriority.__name__} could not find the target flashcard. \"Key\": {instruction.Key}")
            return False
        if not isinstance(change, int):
            cls._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot obtain an integer for priority change")
            log.warning(f"{cls._ChangeFlashcardPriority.__name__} could not obtain an integer for priority change. \"Value\": {instruction.Value}")
            return False
        ## Main
        #### Early escape
        if change == 0:
            cls._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Flashcard priority is unchanged")
            return True
        #### Normal track
        targetFlashcard.Priority += change
        isSuccess = dbMessenger.ReplaceFlashcard(flashcard=targetFlashcard)
        if isSuccess:
            cls.ShowFlashcard_KeyOnly(
                userMessenger=userMessenger,
                flashcard=targetFlashcard, 
                prefix="Priority changed: ")
            log.info(f"{cls._ChangeFlashcardPriority.__name__} changed the priority of flashcard. \"Key\": {targetFlashcard.Key}")
        else:
            log.error(f"{cls._ChangeFlashcardPriority.__name__} failed to change flashcard's priority. \"Key\": {targetFlashcard.Key}")
        return isSuccess
    
    
    def _RespondToQuestion(self, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        """ Under construction
        """
        ## Pre-condition
        if self._questionToAnswer == -1:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="There is no question to be answered")
            log.warning(f"{self._RespondToQuestion.__name__} found no question to be answered")
            return False
        ## Variables initialization
        targetFlashcard = dbMessenger.GetFlashcardById(
            id=self._questionToAnswer)
        ## Pre-condition
        if targetFlashcard is None:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot find the flashcard for the quiz (Maybe it is deleted)")
            log.warning(f"{self._RespondToQuestion.__name__} could not find the target flashcard. \"Id\": {self._questionToAnswer}")
            self._questionToAnswer = -1
            return False
        ## Main
        answerIsCorrect = instruction.Value == targetFlashcard.Key
        targetFlashcard.Priority -= 1 if answerIsCorrect else -1
        #### Reset the question
        self._questionToAnswer = -1
        ## Post-processing
        #### Show answer to the question
        if answerIsCorrect:
            self.ShowFlashcard_MajorFields(
                userMessenger=userMessenger,
                flashcard=targetFlashcard, 
                prefix="*Correct*\n\n")
        else:
            self.ShowFlashcard_MajorFields(
                userMessenger=userMessenger,
                flashcard=targetFlashcard, 
                prefix="*Wrong*\n\n")
        return True
    
    
    def _ChangeFlashcardShowingFrequency(self, instruction:Instruction, 
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        ## Variables initialization
        newFrequency = TryStringToInt(s=instruction.Value)
        ## Pre-condition
        if not isinstance(newFrequency, int):
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot obtain an integer for frequency change")
            log.warning(f"{self._ChangeFlashcardShowingFrequency.__name__} did not obtain a valid frequency value")
            return False
        ## Main
        self.FlashcardShowingFrequency = newFrequency
        self._DisplayCustomTextToUser(
            userMessenger=userMessenger,
            text=f"New frequency: {self.FlashcardShowingFrequency}")
        log.info(f"{self._ChangeFlashcardShowingFrequency.__name__} changed flashcard showing frequency to \"{newFrequency}\"")
        return True
    

    def _ShowFlashcardToUser(self, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger, 
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        ## Variables initialization
        targetFlashcard = self._GetFlashcardFromDatabase(
            instruction=instruction, dbMessenger=dbMessenger)
        ## Pre-condition
        if targetFlashcard is None:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Cannot find the flashcard to show")
            log.warning(f"{self._ShowFlashcardToUser.__name__} could not find the flashcard to be shown. \"Key\": {instruction.Key}")
            return False
        ## Main
        isSuccess = self.ShowFlashcard_MajorFields(
            userMessenger=userMessenger,
            flashcard=targetFlashcard)
        if isSuccess:
            log.info(f"{self._ShowFlashcardToUser.__name__} showed a flashcard to user: \"Key\": {targetFlashcard.Key}")
        else:
            log.warning(f"{self._ShowFlashcardToUser.__name__} failed in showing a flashcard to user")
        return isSuccess
    
    
    def _ShowInfoToUser(self, dbMessenger:FlashcardDatabaseMessenger, 
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        ## Inner function
        def _NumpyArrayToMultiLineString(arr:np.ndarray, 
                numElementsPerLine:int
            ):
            result = ""
            for i in range(len(arr) // numElementsPerLine):
                startIdx = i * numElementsPerLine
                endIdx = (i + 1) * numElementsPerLine
                strSegment = np.array2string(arr[startIdx:endIdx], 
                    separator=" ", 
                    formatter={"int": lambda x: str(x).zfill(3) } )
                strSegment = strSegment.replace("[", "").replace("]", "")
                result += f"  {strSegment}\n"
            result = result.rstrip("\n")
            return result
        
        ## Main
        lastUpdateDatetime_str = self._lastUpdateDatetime.strftime(
            "%Y/%m/%d %H:%M:%S")
        timeOfDayPriorities_str = _NumpyArrayToMultiLineString(
            arr=self._timeOfDayPriorities, numElementsPerLine=6)
        timeOfDayShowFlashcardsDistribution_str = \
            _NumpyArrayToMultiLineString(
                arr=self._timeOfDayShowFlashcardsDistribution,
                numElementsPerLine=6)
        withinHourShowFlashcardsDistribution_str = \
            _NumpyArrayToMultiLineString(
                arr=self._withinHourShowFlashcardsDistribution,
                numElementsPerLine=6)
        flashcardCount = dbMessenger.FlashcardCount()
        texts = (
            f"*Last update*: {lastUpdateDatetime_str}\n"
            f"*Flashcard showing freq*: {self._dailyFlashcardShowingFrequency}\n"
            f"*Time of day priorities*:\n{timeOfDayPriorities_str}\n"
            f"*Flashcard showing distribution*:\n"
            f"_Day_:\n"
            f"{timeOfDayShowFlashcardsDistribution_str}\n"
            f"_Hour_:\n"
            f"{withinHourShowFlashcardsDistribution_str}\n"
            f"*Flashcard count*: {flashcardCount}"
        )
        isSuccess = userMessenger.ShowCustomTexts(customTexts=texts)
        if isSuccess:
            log.info(f"{self._ShowInfoToUser.__name__} showed flashcard system information to user")
        else:
            log.error(f"{self._ShowInfoToUser.__name__} failed to show flashcard system info")
        return isSuccess
    
    
    def _ChangeTimePriority(self, instruction:Instruction=None, 
            timeIdx:int=None, change:int=None, 
            userMessenger:FlashcardUserMessenger=None
        ) -> bool:
        ## Variables initialization
        cls = type(self)
        
        ## Inner functions
        def _RescalePriorities():
            maxPriority = np.max(self._timeOfDayPriorities)
            newPriorities_float = self._timeOfDayPriorities / maxPriority * \
                cls.HIGHEST_TIME_PRIORITY
            self._timeOfDayPriorities = newPriorities_float.astype(int)
        
        ## Variables initialization
        if isinstance(instruction, Instruction):
            timeIdx = TryStringToInt(instruction.Key)
            change = TryStringToInt(instruction.Value)
        ## Pre-condition
        if not isinstance(timeIdx, int) or timeIdx < 0 or \
            timeIdx >= len(self._timeOfDayPriorities):
            if isinstance(userMessenger, FlashcardUserMessenger):
                self._DisplayCustomTextToUser(
                    userMessenger=userMessenger,
                    text="Cannot obtain a valid time index for time priority change (Range: [0, 23])")
            log.warning(f"{self._ChangeTimePriority.__name__} cannot obtain a valid time index for time priority change. \"Key\": {instruction.Key}")
            return False
        if not isinstance(change, int):
            if isinstance(userMessenger, FlashcardUserMessenger):
                self._DisplayCustomTextToUser(
                    userMessenger=userMessenger,
                    text="Cannot obtain an integer for time priority change")
            log.warning(f"{self._ChangeTimePriority.__name__} could not obtain a valid value for the change. \"Value\": {instruction.Value}")
            return False
        if change == 0:
            if isinstance(userMessenger, FlashcardUserMessenger):
                self._DisplayCustomTextToUser(
                    userMessenger=userMessenger,
                    text="Time priority is unchanged")
            return True
        ## Main
        change_unsigned = max(cls.LOWEST_TIME_PRIORITY, 
            min( abs(change), cls.HIGHEST_TIME_PRIORITY) )
        change = int(math.copysign(change_unsigned, change) )
        self._timeOfDayPriorities[timeIdx] += change
        ## Post-processing
        if self._timeOfDayPriorities[timeIdx] > cls.HIGHEST_TIME_PRIORITY:
            _RescalePriorities()
        return True
    
    
    def _HandleInstruction(self, instruction:Instruction, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> None:
        if instruction.Type == InstructionType.ADD:
            self._InsertFlashcard(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        elif instruction.Type == InstructionType.DELETE:
            self._DeleteFlashcard(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        elif instruction.Type == InstructionType.CHANGE_FLASHCARD_PRIORITY:
            self._ChangeFlashcardPriority(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        elif instruction.Type == InstructionType.RESPOND_TO_QUESTION:
            self._RespondToQuestion(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        elif instruction.Type == \
            InstructionType.CHANGE_FLASHCARD_SHOWING_FREQUENCY:
            self._ChangeFlashcardShowingFrequency(instruction=instruction,
                userMessenger=userMessenger)
        elif instruction.Type == InstructionType.SHOW_FLASHCARD:
            self._ShowFlashcardToUser(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        elif instruction.Type == InstructionType.SHOW_INFO:
            self._ShowInfoToUser(dbMessenger=dbMessenger, 
                userMessenger=userMessenger)
        elif instruction.Type == InstructionType.CHANGE_TIME_PRIORITY:
            self._ChangeTimePriority(instruction=instruction,
                userMessenger=userMessenger)
        else:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Unknown instruction")
            log.warning(f"{self._HandleInstruction.__name__} found an unknown instruction")
