import datetime, logging, os, pathlib, sys, time
from os import path

import numpy as np


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
def TryStringToInt(s):
    """ Alternative: regex to match all whole numbers
    
    
        Reference
        ---- ----
        1. https://stackoverflow.com/questions/736043/checking-if-a-string-can-be-converted-to-float-in-python
        2. https://stackoverflow.com/questions/9043551/regex-that-matches-integers-in-between-whitespace-or-start-end-of-string-only
    """
    ## Pre-condition
    if not isinstance(s, str):
        return s
    ## Main
    try:
        result = int(s)
    except:
        result = s
    return result


def FlipBiasedCoin(pOf1:float):
    pOf1 = max(0, min(pOf1, 1) )
    return int(np.random.choice(2, 1, p=[ (1 - pOf1), pOf1] ) )


if __name__ == "__main__":
    print(TryStringToInt("1") )
