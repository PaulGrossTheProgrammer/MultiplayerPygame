# Data and code common to the whole game
import random
import pygame

server_port = 56789

image_folder = "images/"
sounds_folder = "sounds/"
maps_folder = "maps/"

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

frames_per_second = 30

clock = pygame.time.Clock()