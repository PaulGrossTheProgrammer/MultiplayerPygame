# Gemstone sprites
import random
import pygame
import spritesheet
import soundeffects
from common import image_folder

spritegroup = pygame.sprite.Group()
next_id = 1

def clear_gems():
    global next_id

    spritegroup.clear()
    next_id = 1

def add_gem(typename, pos, sprite_id=None):
    global next_id

    if sprite_id is None:
        sprite_id = next_id
        next_id += 1

    sprite = None
    if typename == "gemstones.GemGreen":
        sprite = GemGreen(pos, sprite_id)
        sprite.typename = typename

    if sprite is not None:
        spritegroup.add(sprite)

    return sprite

def get_gem(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            return sprite
    return None

def remove_gem(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            spritegroup.remove(sprite)

def has_id(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            return True
    return False

class Gemstone(pygame.sprite.Sprite):
    sound = None

    radius = 16  # Collsion radius

    def __init__(self, position, sprite_id):
        super().__init__()

        self.sprite_id = sprite_id
        self.typename = None
        self.frame_curr = 0
        self.image = self.image_list[self.frame_curr]
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.frame_change_counter = 0
        self.frame_change = 5

    def update(self):
        self.frame_change_counter += 1
        if self.frame_change_counter >= self.frame_change:
            self.frame_change_counter = 0
            self.frame_curr += 1  # Change frame
            if self.frame_curr >= len(self.image_list):
                self.frame_curr = 0
        self.image = self.image_list[self.frame_curr]

    def play_sound(self):
        if self.sound is not None:
            self.sound.play()

    def set_position(self, position):
        self.rect.center = position

    def get_position(self):
        return self.rect.center

    def scroll_position(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

class GemDiamond(Gemstone):
    sheet = spritesheet.Spritesheet(
        7, 6, filename=image_folder+"diamondspinning.png")
    image_list = sheet.get_frames(end_frame=38)
    sound = soundeffects.pickup_4

class GemGreen(Gemstone):
    sheet = spritesheet.Spritesheet(
        32, 1, filename=image_folder+"gem-green.png")
    image_list = sheet.get_frames()
    sound = soundeffects.pickup_1

class GemRed(Gemstone):
    sheet = spritesheet.Spritesheet(
        32, 1, filename=image_folder+"gem-red.png")
    image_list = sheet.get_frames()
    sound = soundeffects.pickup_2

class GemPink(Gemstone):
    sheet = spritesheet.Spritesheet(
        32, 1, filename=image_folder + "gem-pink.png")
    image_list = sheet.get_frames()
    sound = soundeffects.pickup_3

randomgemtypes = [GemGreen, GemRed, GemPink]

def random_gem(position):
    gemtype = random.choice(randomgemtypes)
    gem = gemtype(position)
    return gem