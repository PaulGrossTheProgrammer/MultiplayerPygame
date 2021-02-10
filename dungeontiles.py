# Dungeon Tiles
import random
import pygame

import common
import clientserver
import spritesheet

# Load the dungeon tiles spritesheets
frames = []
ss_names = "hyptosis_tile-art-batch-{}.png"
for number in range(1, 5):
    ss = spritesheet.Spritesheet(
        30, 30, filename=common.image_folder+ss_names.format(number))
    frames.append(ss.get_frames())

def get_tile_image(sheet, row, col):
    frame_list = frames[sheet-1]
    image = frame_list[row*30+col]
    return image

# determine tile size from first tile
tile_size = get_tile_image(1, 0, 0).get_rect().width

wall_images = []
wall_images.append(get_tile_image(1, 7, 0))
wall_images.append(get_tile_image(1, 7, 1))
wall_images.append(get_tile_image(1, 7, 2))
wall_images.append(get_tile_image(1, 7, 3))
wall_images.append(get_tile_image(1, 7, 4))
wall_images.append(get_tile_image(1, 8, 3))

# Parent Class for all tye of dungeon tiles
class Tile(pygame.sprite.Sprite):

    def __init__(self):
        super().__init__()

    def scroll_position(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def set_position(self, position):
        self.rect.center = position

    def get_position(self):
        return self.rect.center

    def get_data(self) -> dict:
        data = {}
        data["x"] = str(self.rect.center[0])
        data["y"] = str(self.rect.center[1])
        return data

    def set_data(self, data: dict):
        x = int(data.get("x", "0"))
        y = int(data.get("y", "0"))
        self.rect.center = (x, y)


class WallTile(Tile):
    radius = 16

    def __init__(self):
        super().__init__()
        self.image = random.choice(wall_images)
        self.rect = self.image.get_rect()


teleport_source_image = get_tile_image(4, 5, 6)
teleport_target_image = get_tile_image(4, 6, 6)

class TeleportSourceTile(Tile):
    radius = 16

    def __init__(self):
        super().__init__()
        self.image = teleport_source_image
        self.rect = self.image.get_rect()
        # TODO - fix in set_data
        # self.teleportx = teleportx
        # self.teleporty = teleporty

class TeleportTargetTile(Tile):
    radius = 16

    def __init__(self):
        super().__init__()
        self.image = teleport_target_image
        self.rect = self.image.get_rect()


fireball_tower_image = get_tile_image(2, 22, 9)

class FireballTower(Tile):

    def __init__(self):
        super().__init__()
        self.image = fireball_tower_image
        self.rect = self.image.get_rect()


# Client/Server code

class_list = (WallTile, TeleportSourceTile, TeleportTargetTile, FireballTower)
shared = clientserver.SharedSpriteGroup("dungeontiles", class_list)