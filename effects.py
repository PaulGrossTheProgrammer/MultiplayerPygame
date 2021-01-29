# Animated effects

import pygame
import spritesheet
import common
from common import image_folder

# Parent Class for animated sprites that play through only once.
class MomentaryEffect(pygame.sprite.Sprite):

    def __init__(self, position, sprite_id):
        super().__init__()

        self.sprite_id = sprite_id
        self.typename = None
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

    def set_position(self, position):
        self.rect.center = position

    def get_position(self):
        return self.rect.center

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

# Client/Server code

spritegroup = pygame.sprite.Group()
next_id = 0
# TODO - If next_id is large and the spritegroup is empty, reset the next_id

# Called by the server to encode the sprites as string for sending via Internet
# TODO - handle incremental updates:
# TODO - put complete:incremental or update:complete in response
def encode_update():
    if len(spritegroup) == 0:
        return "response:update,module:effects,type:EMPTY\n"

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
    response = "response:update,module:effects\n"
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
    if typename == "ExplosionRed":
        sprite = ExplosionRed(pos, sprite_id)
        sprite.typename = typename
    elif typename == "ExplosionGreen":
        sprite = ExplosionGreen(pos, sprite_id)
        sprite.typename = typename
    elif typename == "ExplosionBlue":
        sprite = ExplosionBlue(pos, sprite_id)
        sprite.typename = typename
    elif typename == "Vanish":
        sprite = Vanish(pos, sprite_id)
        sprite.typename = typename
    elif typename == "SparkleBlue":
        sprite = SparkleBlue(pos, sprite_id)
        sprite.typename = typename
    elif typename == "SparkleYellow":
        sprite = SparkleYellow(pos, sprite_id)
        sprite.typename = typename
    elif typename == "SparkleWhite":
        sprite = SparkleWhite(pos, sprite_id)
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