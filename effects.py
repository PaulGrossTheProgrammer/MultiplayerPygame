# Animated effects

import pygame

from common import image_folder
import spritesheet
import common
import clientserver


class Effect(pygame.sprite.Sprite):
    """Parent Class for animated effect sprites
    that play a sequence of images.

    NOTE: Subclass either ContinuousEffect or MomentaryEffect.

    Each subclass needs to create a list of images to play though
    in a variable called frames.
    """

    frame_change_trigger = int(common.frames_per_second / 20)

    def __init__(self):
        super().__init__()

        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.done = False

        # Animation
        self.frame_curr = 0
        self.frame_change_counter = 0

    def get_data(self) -> dict:
        data = {}
        data["x"] = str(self.rect.center[0])
        data["y"] = str(self.rect.center[1])
        return data

    def set_data(self, data: dict):
        x = int(data.get("x", "0"))
        y = int(data.get("y", "0"))
        self.rect.center = (x, y)

    def set_position(self, position: tuple):
        self.rect.center = position

    def get_position(self) -> tuple:
        return self.rect.center

    def scroll_position(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

class ContinuousEffect(Effect):
    """Parent Class for animated sprites that replay continually.

    Each subclass needs to create a list of images to play though
    in a variable called frames.
    """

    def update(self):
        self.frame_change_counter += 1
        if self.frame_change_counter >= self.frame_change_trigger:
            self.frame_change_counter = 0
            self.frame_curr += 1  # Change frame
            if self.frame_curr >= len(self.frames):
                self.frame_curr = 0
            self.image = self.frames[self.frame_curr]


class MomentaryEffect(Effect):
    """Parent Class for animated sprites that play through only once.

    Each subclass needs to create a list of images to play though
    in a variable called frames.
    """

    def update(self):
        self.frame_change_counter += 1
        if self.frame_change_counter >= self.frame_change_trigger:
            self.frame_change_counter = 0
            self.frame_curr += 1  # Change frame
            if self.frame_curr < len(self.frames):
                self.image = self.frames[self.frame_curr]
            else:
                self.done = True
                self.kill()


class FireCircle(ContinuousEffect):
    sheet = spritesheet.Spritesheet(
        8, 8, filename=image_folder+"FireCircle.png", scale=1.5)
    frames = sheet.get_frames()
    frames = frames[:31]

class ExplosionRed(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        4, 4, filename=image_folder+"Explosion-01.png")
    frames = sheet.get_frames()

class ExplosionGreen(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        4, 4, filename=image_folder+"Explosion-Green.png")
    frames = sheet.get_frames()

class ExplosionBlue(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        4, 4, filename=image_folder+"Explosion-Blue.png")
    frames = sheet.get_frames()

class Vanish(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        4, 4, filename=image_folder+"Effect95.png")
    frames = sheet.get_frames()

class SparkleBlue(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        35, 1, filename=image_folder+"Sparkle-Blue.png")
    frames = sheet.get_frames()

class SparkleYellow(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        8, 4, filename=image_folder+"sparkle.png")
    all_frames = sheet.get_frames()
    frames = all_frames[0:4] + all_frames[8:12] + \
        all_frames[16:20] + all_frames[24:28]

class SparkleWhite(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        8, 4, filename=image_folder+"sparkle.png")
    all_frames = sheet.get_frames()
    frames = all_frames[4:8] + all_frames[12:16] + \
        all_frames[20:24] + all_frames[28:32]

class BloodHit(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        4, 4, filename=image_folder+"BloodHit-1-small.png")
    frames = sheet.get_frames()
    frame_change_trigger = 2

class BloodKill(MomentaryEffect):
    sheet = spritesheet.Spritesheet(
        15, 1, filename=image_folder+"bloodsplat3_strip15-small.png")
    frames = sheet.get_frames()
    frame_change_trigger = 2


# Client/Server code

class_list = (FireCircle, ExplosionRed, ExplosionGreen, ExplosionBlue, Vanish,
              SparkleBlue, SparkleYellow, SparkleWhite,
              BloodHit, BloodKill)
shared = clientserver.SharedSpriteGroup("effects", class_list)