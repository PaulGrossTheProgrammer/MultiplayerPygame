# Cursor sprites
import pygame
from common import image_folder

class PlayerCursor(pygame.sprite.Sprite):

    image_white = pygame.image.load(image_folder+"cursor_white.png")
    image_red = pygame.image.load(image_folder+"cursor_red.png")
    image_green = pygame.image.load(image_folder+"cursor_green.png")

    modename = "MOVE"

    def __init__(self):
        super().__init__()

        self.image = self.image_green
        self.rect = self.image.get_rect()

    def set_pos(self, position):
        self.rect.center = position

    def set_mode(self, modename):
        self.modename = modename
        if self.modename == "MOVE":
            self.image = self.image_green
            self.rect = self.image.get_rect()
        elif self.modename == "FIREBALL":
            self.image = self.image_red
            self.rect = self.image.get_rect()
        else:
            self.image = self.image_green
            self.rect = self.image.get_rect()