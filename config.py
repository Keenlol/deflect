import pygame

class Config:
    # Window Settings
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (25, 25, 25)
    RED = (255,0,0)
    BLUE = (0,0,255)

    # Player Physics
    GRAVITY = 0.5
    JUMP_FORCE = -15
    MOVE_SPEED = 5
    GROUND_FRICTION = 0.85
    AIR_RESISTANCE = 0

    # Game Settings
    FLOOR_HEIGHT = 100  # Height from bottom of screen 
    # New game settings
    FLOOR_HEIGHT = FLOOR_HEIGHT 