# Dungeon Tiles
import random
import pygame

import common
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

    def __init__(self, sprite_id):
        super().__init__()
        self.sprite_id = sprite_id
        self.typename = None

    def scroll_position(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def set_position(self, position):
        self.rect.center = position

    def get_position(self):
        return self.rect.center

class WallTile(Tile):
    radius = 16

    def __init__(self, position, sprite_id):
        super().__init__(sprite_id)
        self.image = random.choice(wall_images)
        self.rect = self.image.get_rect()
        self.rect.center = position


teleport_source_image = get_tile_image(4, 5, 6)
teleport_target_image = get_tile_image(4, 6, 6)

class TeleportSourceTile(Tile):
    radius = 16

    def __init__(self, position, teleportx, teleporty, sprite_id):
        super().__init__(sprite_id)
        self.image = teleport_source_image
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.teleportx = teleportx
        self.teleporty = teleporty

class TeleportTargetTile(Tile):
    radius = 16

    def __init__(self, position, sprite_id):
        super().__init__(sprite_id)
        self.image = teleport_target_image
        self.rect = self.image.get_rect()
        self.rect.center = position


fireball_tower_image = get_tile_image(2, 22, 9)

class FireballTower(Tile):

    def __init__(self, position, sprite_id):
        super().__init__(sprite_id)
        self.image = fireball_tower_image
        self.rect = self.image.get_rect()
        self.rect.center = position

# Client/Server code

spritegroup = pygame.sprite.Group()
next_id = 0
# TODO - If next_id is large and the spritegroup is empty, reset the next_id

# Called by the server to encode the sprites as string for sending via Internet
# TODO - handle incremental updates:
# TODO - put complete:incremental or update:complete in response
def encode_update():
    if len(spritegroup) == 0:
        return "response:update,module:dungeontiles,type:EMPTY\n"

    # Group the sprites by type to reduce the length of the response
    grouped_sprites = {}
    # The sprites of the same class are grouped together
    for sprite in spritegroup:
        sprite_id = sprite.sprite_id
        sprite_type = sprite.typename
        x, y = sprite.get_position()

        if sprite_type in grouped_sprites:
            group = grouped_sprites[sprite_type]
        else:
            group = []
            grouped_sprites[sprite_type] = group

        group.append([sprite_id, x, y])

    # Build the complete response from the grouped sprites
    response = "response:update,module:dungeontiles\n"
    template_type = "type:{}\n"
    template_sprite = "id:{},x:{},y:{}\n"
    for name, group in grouped_sprites.items():
        response += template_type.format(name)
        for data in group:
            sprite_id = data[0]
            x = data[1]
            y = data[2]
            response += template_sprite.format(sprite_id, x, y)

    return response

# Called by the Clients when an update is received
def decode_update(datalines):
    id_list = []
    sprite_type = None
    for data in datalines:
        if "type" in data:
            sprite_type = data["type"]
        elif sprite_type is not None:
            sprite_id = int(data["id"])
            x = int(data["x"])
            y = int(data["y"])
            id_list.append(sprite_id)

            sprite = get(sprite_id)
            if sprite is None:
                add(sprite_type, [x, y], sprite_id)
            else:
                sprite.set_position([x, y])

    # Remove any sprites not included in the update
    for sprite in spritegroup:
        curr_id = sprite.sprite_id
        if curr_id not in id_list:
            remove(curr_id)


def draw(screen):
    spritegroup.draw(screen)

def update():
    spritegroup.update()

def update_server():
    update()

def clear():
    global next_id

    spritegroup.clear()
    next_id = 1

def add(typename, pos, sprite_id=None):
    global next_id

    if sprite_id is None:
        sprite_id = next_id
        next_id += 1

    sprite = None
    if typename == "WallTile":
        sprite = WallTile(pos, sprite_id)
        sprite.typename = typename
    elif typename == "TeleportSourceTile":
        sprite = TeleportSourceTile(pos, sprite_id)
        sprite.typename = typename
    elif typename == "TeleportTargetTile":
        sprite = TeleportTargetTile(pos, sprite_id)
        sprite.typename = typename
    elif typename == "FireballTower":
        sprite = FireballTower(pos, sprite_id)
        sprite.typename = typename

    if sprite is not None:
        spritegroup.add(sprite)

    return sprite

def get(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            return sprite
    return None

def remove(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            spritegroup.remove(sprite)
            return True
    return False

def has_id(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            return True
    return False

def collide_point_all(point):
    coll = []
    for sprite in spritegroup:
        if sprite.rect.collidepoint(point):
            coll.append(sprite)
    return coll

def collide_point_all_type(point, typename):
    coll = []
    for sprite in spritegroup:
        if sprite.rect.collidepoint(point) and sprite.typename == typename:
            coll.append(sprite)
    return coll

def collide_point_first(point):
    sprites = collide_point_all(point)
    if len(sprites) == 0:
        return None
    return sprites[0]

def collide_point_first_type(point, typename):
    sprites = collide_point_all_type(point, typename)
    if len(sprites) == 0:
        return None
    return sprites[0]
