import datetime, logging, os, random, sys, time, urllib
from dataclasses import dataclass, InitVar
from typing import Collection
from logging.handlers import RotatingFileHandler
from os import path

import numpy as np
import telegram
from telegram import Bot

from b import *


a = np.ones((24,), dtype=int) * 99
a[0] = 100000
b = np.max(a)
c = a / b * 99
d = c.astype(int)
print(a)
print(c, c.dtype)
print(d)
