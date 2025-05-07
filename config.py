import pygame

class Config:
    # Window Settings
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60

    # Colors
    BACKGROUND_COLOR = (12, 12, 15)
    FLOOR_COLOR = (45, 49, 61)
    TTK_BLACK = '#0c0c0f'

    # Game Settings
    FLOOR_HEIGHT = 100

    # UI
    TITLE_FONT_SIZE = 80
    BUTTON_FONT_SIZE = 60
    BUTTON_IDLE_COLOR = (154, 160, 175)
    BUTTON_HOVER_COLOR = {'blue':(94, 175, 255),
                          'yellow':(255, 205, 120),
                          'red':(224, 79, 74)}