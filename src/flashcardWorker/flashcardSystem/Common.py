import datetime, logging, os, pathlib, sys, time
import re
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
#### Functions #### 
#### #### #### #### #### 
def TryWholeNumberStringToInt(s:str):
    """ Regex to match all whole numbers
    
    
        Reference
        ---- ----
        1. https://stackoverflow.com/questions/736043/checking-if-a-string-can-be-converted-to-float-in-python
        2. https://stackoverflow.com/questions/9043551/regex-that-matches-integers-in-between-whitespace-or-start-end-of-string-only
    """
    ## Pre-condition
    if not isinstance(s, str):
        return s
    ## Main
    if re.match(r"^\d+$", s) is None:
        return s
    return int(s)
