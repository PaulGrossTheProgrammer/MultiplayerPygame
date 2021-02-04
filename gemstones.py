# Gemstone sprites

import pygame

import spritesheet
import soundeffects
from common import image_folder
import clientserver


class Gemstone(pygame.sprite.Sprite):
    sound = None

    radius = 16  # Collsion radius

    def __init__(self):
        super().__init__()

        self.frame_curr = 0
        self.image = self.image_list[self.frame_curr]
        self.rect = self.image.get_rect()
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

    def get_data(self) -> dict:
        data = {}
        data["x"] = str(self.rect.center[0])
        data["y"] = str(self.rect.center[1])
        return data

    def set_data(self, data: dict):
        pos = [int(data["x"]), int(data["y"])]
        self.rect.center = pos


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


# Client/Server code

class_list = (GemGreen, GemGreen, GemRed, GemPink, GemDiamond)
shared = clientserver.SharedSpriteGroup("gemstones", class_list)