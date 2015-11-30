import os
import pygame
import sqlite3 as sql
import threading
from time import sleep

session = { "IMAGES": None, "CONTROL": None, "PIANOBAR": None, "ACTIVE": True,
            "VOLUME_CONTROL": None, "VOLUME": 100, "MUSIC_PLAYING": False,
            "CURRENT_TRACK": None, "DEBUG": False, 'PANEL': 0, 'SCREEN': None,
            'PAGE': 2 }
screen = pygame.display.set_mode((320, 240))
pitft = 0

# EVENTS - thread control
NEW_TRACK_EV = threading.Event()
RENDER_EV = threading.Event()

# COLORS
BG_COLOR = (23, 148, 207)
INFO_COLOR = (32, 85, 134)
HEADER_COLOR = (19, 52, 82)

# IS: Info Surface
IS_WIDTHWIDTH = 283
IS_WIDTHHEIGHT = 58
IS_WIDTHPOS = (19, 161)
# SS: Status Surface
SS_WIDTH = 283
SS_HEIGHT = 20
SS_POS = (19, 7)

def enum(**enums):
    return type('Enum', (), enums)

PANELS = enum(MEDIA=0, VOLUME=1, PAGES=2)
SCREENS = enum(NOWPLAYING=0, HOME=1, STATIONS=2)

def debug(message):
    global session
    if session['DEBUG']:
        print message
