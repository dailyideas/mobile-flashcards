import datetime, logging, os, random, sys, time, urllib
from dataclasses import dataclass, InitVar
from typing import Collection
from logging.handlers import RotatingFileHandler
from os import path

import numpy as np
import telegram
from telegram import Bot

from b import *


a = np.ones((24,), dtype=int)
b = (
    f"{a[0:6]}\n"
    f"{a[6:12]}\n"
    f"{a[12:18]}\n"
    f"{a[18:24]}\n"
)
print(b)
