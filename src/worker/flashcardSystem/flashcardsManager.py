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
    from flashcardDatabaseMessenger import FlashcardDatabaseMessenger
    from flashcardUserMessenger import FlashcardUserMessenger
else:
    from .flashcardDatabaseMessenger import FlashcardDatabaseMessenger
    from .flashcardUserMessenger import FlashcardUserMessenger
from utils.common import TryStringToInt, FlipBiasedCoin
from utils.flashcard import Flashcard
from utils.instruction import InstructionType, Instruction


#### #### #### #### #### 
#### Class #### 
#### #### #### #### #### 
class FlashcardsManager:
    VERSION = "1.0.0"
    LOWEST_TIME_PRIORITY = 0
    HIGHEST_TIME_PRIORITY = 999
    LOWEST_FLASHCARD_SHOWING_FREQUENCY = 0
    HIGHEST_FLASHCARD_SHOWING_FREQUENCY = 999
    
    def __init__(self, numJobsPerHour:int=12) -> None:
        ## Variables initialization
        cls = type(self)
        ## Main
        self._version = self.VERSION
        self._numJobsPerHour = numJobsPerHour
        self._lastUpdateDatetime = None ## datetime.datetime: Renewed whenever "ShowRandomFlashcardsWithPriority" is called
        self._lastInstructionId = -1 ## int
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
    def Version(self) -> str:
        return self._version
    
    
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
        value = min(max(value, self.LOWEST_FLASHCARD_SHOWING_FREQUENCY), 
            self.HIGHEST_FLASHCARD_SHOWING_FREQUENCY)
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
            log.warning(f"{cls.Load.__name__} could not find the cache \"{cachePath}\"")
            return None
        ## Main
        payload = None
        with open(cachePath, "rb") as fhandler:
            payload = pickle.load(fhandler)
        if not isinstance(payload, cls):
            log.error(f"Instance loaded from \"{cachePath}\" is not an \"{cls.__name__}\"")
            return None
        cachedVersion = payload.Version
        cachedVersion_major = cachedVersion.split(".")[0]
        currentVersion = cls.VERSION
        currentVersion_major = currentVersion.split(".")[0]
        if currentVersion_major != cachedVersion_major:
            log.warning( (
                f"Version of instance loaded from \"{cachePath}\": {cachedVersion}, "
                f"which is incompatible to the current version: {currentVersion}") )
            return None
        ## Epilogue
        log.info(f"Loaded a {cls.__name__} instance from \"{cachePath}\"")
        return payload


    def ProcessUserInstructions(self, 
            dbMessenger:FlashcardDatabaseMessenger,
            userMessenger:FlashcardUserMessenger
        ) -> None:
        ## Main
        instructions, latestInstructionsId = \
            userMessenger.GetUserInstructions(
                lastInstructionId=self._lastInstructionId)
        for instruction in instructions:
            self._HandleInstruction(instruction=instruction, 
                dbMessenger=dbMessenger, userMessenger=userMessenger)
        ## Post-processing
        if latestInstructionsId > self._lastInstructionId:
            #### Store latest instruction id for next FlashcardUserMessenger.GetUserInstructions
            self._lastInstructionId = latestInstructionsId
        if len(instructions):
            #### Possible increase of priority at current hour
            currentHour = datetime.datetime.now().hour
            priorityChange = FlipBiasedCoin(pOf1=0.6)
            if priorityChange > 0:
                self._ChangeTimePriority(timeIdx=currentHour, change=1)
            
            
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
                log.error(f"{_ShowFlashcardAndReducePriority.__name__} failed to show flashcard \"{flashcard.Key}\" to user")
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
                log.error(f"{_ShowFlashcardAndReducePriority.__name__} failed to show flashcard \"{flashcard.Key}\" to user")
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
        for flashcard in flashcards:
            _ShowFlashcardAndReducePriority(flashcard=flashcard)


    def _GenerateTimeOfDayShowFlashcardsDistribution(self) -> np.ndarray:
        ## Main
        #### Get weighting of each time session
        timeOfDayPrioritiesSum = np.sum(self._timeOfDayPriorities)
        timeOfDayProbabilities = [i / timeOfDayPrioritiesSum for i in \
            self._timeOfDayPriorities]
        #### Get the distribution of the number of flashcards to be shown at each time session
        showFlashcardMoments = np.random.choice(HOURS_IN_DAY, 
            self._dailyFlashcardShowingFrequency, replace=True, 
            p=timeOfDayProbabilities)
        showFlashcardsDistribution = np.zeros( (HOURS_IN_DAY,), dtype=int)
        for i in showFlashcardMoments:
            showFlashcardsDistribution[i] += 1
        ## Epilogue
        log.info(f"{self._GenerateTimeOfDayShowFlashcardsDistribution.__name__} generated: {showFlashcardsDistribution.tolist() }")
        return showFlashcardsDistribution


    def _GenerateWithinHourShowFlashcardsDistribution(self) -> np.ndarray:
        ## Main
        #### Get the number of flashcards to be shown at current hour
        currentHour = datetime.datetime.now().hour
        flashcardsToShow = \
            self._timeOfDayShowFlashcardsDistribution[currentHour]
        #### Get the distribution of the number of flashcards to be shown at each time session
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
        #### Update timeOfDayShowFlashcardsDistribution at the start of a day
        if self._lastUpdateDatetime.date() != currentDatetime.date():
            self._timeOfDayShowFlashcardsDistribution = \
                self._GenerateTimeOfDayShowFlashcardsDistribution()
        #### Update withinHourShowFlashcardsDistribution at the start of an hour
        if self._lastUpdateDatetime.hour != currentDatetime.hour:
            self._withinHourShowFlashcardsDistribution = \
                self._GenerateWithinHourShowFlashcardsDistribution()
        #### Reset the question to be asked if the question is not answered after a day
        if self._questionToAnswer != -1:
            daysPassedFromLastQuestion = \
                (currentDatetime - self._questionAskedDatetime).days
            if daysPassedFromLastQuestion >= 1:
                self._questionToAnswer = -1
        #### Renew the lastUpdateDatetime
        self._lastUpdateDatetime = currentDatetime


    @classmethod
    def _DisplayCustomTextToUser(cls, userMessenger:FlashcardUserMessenger, 
            text:str
        ) -> bool:
        isSuccess = userMessenger.ShowCustomText(text=text, autoEscape=True)
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
                cls.ShowFlashcard_KeyOnly(
                    userMessenger=userMessenger,
                    flashcard=existingFlashcard, 
                    prefix="Unexpected error occurred when updating: ")
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
                cls.ShowFlashcard_KeyOnly(
                    userMessenger=userMessenger,
                    flashcard=newFlashcard, 
                    prefix="Unexpected error occurred when inserting: ")
                log.error(f"{cls._InsertFlashcard.__name__} found {dbMessenger.InsertFlashcard} failed. \"Key\": {newFlashcard.Key}")
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
            cls.ShowFlashcard_KeyOnly(
                userMessenger=userMessenger,
                flashcard=targetFlashcard, 
                prefix="Unexpected error occurred when deleting: ")
            log.error(f"{cls._DeleteFlashcard.__name__} found {dbMessenger.DeleteFlashcard} failed. \"Key\": {targetFlashcard.Key}")
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
            cls.ShowFlashcard_KeyOnly(
                userMessenger=userMessenger,
                text="Unexpected error occurred when changing the priority of: ")
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
        ## Pre-processing
        if newFrequency < self.LOWEST_FLASHCARD_SHOWING_FREQUENCY:
            newFrequency = self.LOWEST_FLASHCARD_SHOWING_FREQUENCY
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=f"Frequency cannot be smaller than {self.LOWEST_FLASHCARD_SHOWING_FREQUENCY}")
        if newFrequency > self.HIGHEST_FLASHCARD_SHOWING_FREQUENCY:
            newFrequency = self.HIGHEST_FLASHCARD_SHOWING_FREQUENCY
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=f"Frequency cannot be larger than {self.HIGHEST_FLASHCARD_SHOWING_FREQUENCY}")
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
            log.error(f"{self._ShowFlashcardToUser.__name__} failed in showing a flashcard to user")
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
        text = (
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
        isSuccess = userMessenger.ShowCustomText(text=text, autoEscape=False)
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
                cls.HIGHEST_TIME_PRIORITY / 2
            self._timeOfDayPriorities = newPriorities_float.astype(int)
            log.info(f"{self._ChangeTimePriority.__name__} has rescaled the time priorities")
        
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
            log.warning(f"{self._ChangeTimePriority.__name__} could not obtain an integer for time priority change. \"Value\": {instruction.Value}")
            return False
        if change == 0:
            if isinstance(userMessenger, FlashcardUserMessenger):
                self._DisplayCustomTextToUser(
                    userMessenger=userMessenger,
                    text="Time priority is unchanged")
            log.info(f"{self._ChangeTimePriority.__name__} found the change to be 0")
            return True
        ## Pre-processing
        if abs(change) < cls.LOWEST_TIME_PRIORITY:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=f"Time priority change cannot be smaller than {cls.LOWEST_TIME_PRIORITY}")
        if abs(change) > cls.HIGHEST_TIME_PRIORITY:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=f"Time priority change cannot be larger than {cls.HIGHEST_TIME_PRIORITY}")
        ## Main
        change_unsigned = max(cls.LOWEST_TIME_PRIORITY, 
            min( abs(change), cls.HIGHEST_TIME_PRIORITY) )
        change = int(math.copysign(change_unsigned, change) )
        self._timeOfDayPriorities[timeIdx] += change
        self._DisplayCustomTextToUser(
            userMessenger=userMessenger,
            text=f"Time priority at hour {timeIdx} is changed to {self._timeOfDayPriorities[timeIdx] }")
        log.info(f"{self._ChangeTimePriority.__name__} changed the priority at hour {timeIdx} to {self._timeOfDayPriorities[timeIdx] }")
        ## Post-processing
        if self._timeOfDayPriorities[timeIdx] > cls.HIGHEST_TIME_PRIORITY:
            _RescalePriorities()
        return True
    
    
    def _ShowHelpToUser(self, instruction:Instruction, 
            userMessenger:FlashcardUserMessenger
        ) -> bool:
        if instruction.Key == "": ## Default value 
            isSuccess = self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=Instruction.GetHelp() )
        else:
            isSuccess = self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text=Instruction.GetInstructionUsage(instruction.Key) )
        return isSuccess
    
    
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
        elif instruction.Type == InstructionType.SHOW_HELP:
            self._ShowHelpToUser(instruction=instruction, 
                userMessenger=userMessenger)
        else:
            self._DisplayCustomTextToUser(
                userMessenger=userMessenger,
                text="Unknown instruction")
            log.warning(f"{self._HandleInstruction.__name__} found an unknown instruction")
