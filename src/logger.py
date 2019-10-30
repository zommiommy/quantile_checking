
import sys
import logging

default_level = logging.ERROR

logger = logging.getLogger()
logger.setLevel(default_level)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(default_level)
formatter = logging.Formatter('%(levelname)s:%(filename)s:%(funcName)s:%(lineno)d:%(message)s') # %(asctime)s:
handler.setFormatter(formatter)
logger.addHandler(handler)

def setLevel(level):
    global handler
    global logger
    handler.setLevel(level=level)
    logger.setLevel(level=level)