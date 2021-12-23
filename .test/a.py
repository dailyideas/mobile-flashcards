import datetime, logging, os, random, sys, time, urllib
from dataclasses import dataclass, InitVar
from typing import Collection
from logging.handlers import RotatingFileHandler
from os import path

import numpy as np
import telegram
from telegram import Bot

from b import *


a = np.random.choice(2, 1, p=[0.9, 0.1] )
print(a, type(a) )
print(a[0], type(a[0]) )
print(int(a), type(int(a)))
