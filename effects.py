# Animated effects

import pygame
import spritesheet
import common
from common import image_folder

# Parent Class for animated sprites that play through only once.
class MomentaryEffect(pygame.sprite.Sprite):

    def __init__(self, position):
        super().__init__()

        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.done = False

        # Animation
        self.frame_curr = 0
        self.frame_change_trigger = int(common.frames_per_second / 20)
        self.frame_change_counter = 0

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

    def scroll_position(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

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