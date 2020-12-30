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

def random_pos():
    return [random.randrange(100, SCREEN_WIDTH - 100),
            random.randrange(100, SCREEN_HEIGHT - 100)]

def debug_sprite_draw(screen, sprite):
    pygame.draw.rect(screen, WHITE, sprite.rect, 1)
    if hasattr(sprite, 'radius'):
        pygame.draw.circle(screen, WHITE,
                           sprite.rect.center, int(sprite.radius), 1)

def debug_sprites_draw(screen, sprite_group):
    for sprite in sprite_group:
        pygame.draw.rect(screen, WHITE, sprite.rect, 1)
        if hasattr(sprite, 'radius'):
            pygame.draw.circle(screen, WHITE,
                               sprite.rect.center, int(sprite.radius), 1)