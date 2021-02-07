# Fireball sprites
import math
import pygame

import common
import clientserver
import spritesheet
from common import image_folder

class DirectedSprite(pygame.sprite.Sprite):
    speed = 4
    distance = 500

    def __init__(self):
        super().__init__()

        self.angle = None

        # Track position as float values for better accuracy
        self.position_x = 0.0
        self.position_y = 0.0

        self.speed *= 60.0/common.frames_per_second
        self.frame_curr = 0
        self.frame_change_trigger = int(common.frames_per_second / 12)
        self.frame_change_counter = 0
        self.delta_x = 0.0
        self.delta_y = 0.0
        self.distance_end = self.distance
        self.distance_acc = 0
        self.done = False

    def set_angle_frames(self, angle):
        self.angle = angle
        self.angle_frames = self.sheet.get_angled_image_list(angle)

        self.image = self.angle_frames[self.frame_curr]
        self.rect = self.image.get_rect()

        self.delta_x = math.cos(angle) * self.speed
        self.delta_y = math.sin(angle) * self.speed

    def update(self):
        if self.done is True:
            return

        self.frame_change_counter += 1
        if self.frame_change_counter >= self.frame_change_trigger:
            self.frame_change_counter = 0
            self.frame_curr += 1  # Change frame
            if self.frame_curr >= len(self.angle_frames):
                self.frame_curr = 0

        # Update float postion values for better accuracy
        self.position_x += self.delta_x
        self.position_y += self.delta_y

        self.rect.center = [int(self.position_x), int(self.position_y)]
        self.distance_acc += self.speed
        if self.distance_acc >= self.distance_end:
            self.done = True
            # self.kill()

        self.image = self.angle_frames[self.frame_curr]

    def set_position(self, position):
        self.position_x = position[0]
        self.position_y = position[1]
        self.rect.center = position

    def get_position(self):
        return [self.position_x, self.position_y]

    def scroll_position(self, dx, dy):
        self.position_x += dx
        self.position_y += dy
        self.rect.center = [int(self.position_x), int(self.position_y)]

    def get_data(self) -> dict:
        """Needed by DistributedSpriteGroup.encode_update()"""

        data = {}
        data["x"] = str(self.position_x)
        data["y"] = str(self.position_y)
        data["dx"] = str(self.delta_x)
        data["dy"] = str(self.delta_y)
        data["angle"] = str(self.angle)
        return data

    def set_data(self, data: dict):
        """Needed by DistributedSpriteGroup.decode_update()"""

        self.position_x = float(data["x"])
        self.position_y = float(data["y"])
        if self.angle is None:
            angle = float(data["angle"])
            self.set_angle_frames(angle)
        else:
            if "dx" in data and "dy" in data:
                self.delta_x = float(data["dx"])
                self.delta_y = float(data["dy"])
        self.rect.center = (int(self.position_x), int(self.position_y))


class FireballRed(DirectedSprite):
    sheet = spritesheet.Spritesheet(
        3, 2, filename=image_folder+"fireball-red.png")
    image_list = sheet.get_frames()
    sheet.create_angled_image_lists(image_list, 32)
    radius = 16

class FireballGreen(DirectedSprite):
    sheet = spritesheet.Spritesheet(
        3, 2, filename=image_folder+"fireball-green.png")
    image_list = sheet.get_frames()
    sheet.create_angled_image_lists(image_list, 32)
    radius = 16

class FireballBlue(DirectedSprite):
    sheet = spritesheet.Spritesheet(
        3, 2, filename=image_folder+"fireball-blue.png")
    image_list = sheet.get_frames()
    sheet.create_angled_image_lists(image_list, 32)
    radius = 16

# Client/Server code

class_list = (FireballRed, FireballGreen, FireballBlue)
shared = clientserver.SharedSpriteGroup("fireball", class_list)