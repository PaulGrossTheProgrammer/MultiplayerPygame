# Gemstone sprites
import random
import pygame
import spritesheet
import soundeffects
from common import image_folder


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


# Client/Server code

# Called by the server to encode the sprites as string for sending via Internet
# TODO - handle incremental updates:
# TODO - put complete:incremental or update:complete in response
def encode_update():
    if len(spritegroup) == 0:
        return "response:update,module:gemstones,type:EMPTY\n"

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
    response = "response:update,module:gemstones\n"
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

            sprite = get_gem(sprite_id)
            if sprite is None:
                add_gem(sprite_type, [x, y], sprite_id)
            else:
                sprite.set_position([x, y])

    # Remove any gems not included in the update
    for sprite in spritegroup:
        curr_id = sprite.sprite_id
        if curr_id not in id_list:
            remove_gem(curr_id)

spritegroup = pygame.sprite.Group()
next_id = 0
# TODO - If next_id is large and the spritegroup is empty, reset the next_id

def draw(screen):
    spritegroup.draw(screen)

def update():
    spritegroup.update()

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
    if typename == "GemGreen":
        sprite = GemGreen(pos, sprite_id)
        sprite.typename = typename
    elif typename == "GemRed":
        sprite = GemRed(pos, sprite_id)
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
            return True
    return False

def has_id(sprite_id):
    for sprite in spritegroup:
        if sprite.sprite_id == sprite_id:
            return True
    return False