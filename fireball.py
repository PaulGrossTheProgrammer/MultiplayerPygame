# Fireball sprites
import math
import pygame

import common
import spritesheet
from common import image_folder

class DirectedSprite(pygame.sprite.Sprite):
    speed = 4

    def __init__(self, position, distance, angle, sprite_id):
        super().__init__()

        self.sprite_id = sprite_id
        self.typename = None
        self.angle = angle
        self.angle_frames = self.sheet.get_angled_image_list(angle)

        # Track position as float values for better accuracy
        self.position_x = float(position[0])
        self.position_y = float(position[1])

        self.speed *= 60.0/common.frames_per_second
        self.frame_curr = 0
        self.image = self.angle_frames[self.frame_curr]
        self.rect = self.image.get_rect()
        self.rect.center = position
        # self.frame_change_trigger = 5
        self.frame_change_trigger = int(common.frames_per_second / 12)
        self.frame_change_counter = 0
        self.delta_x = math.cos(angle) * self.speed
        self.delta_y = math.sin(angle) * self.speed
        self.distance_end = distance
        self.distance_acc = 0
        self.done = False

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

    def update_server(self):
        self.update()

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

spritegroup = pygame.sprite.Group()
next_id = 0
# TODO - If next_id is large and the spritegroup is empty, reset the next_id

# Called by the server to encode the sprites as string for sending via Internet
# TODO - handle incremental updates:
# TODO - put complete:incremental or update:complete in response
def encode_update():
    if len(spritegroup) == 0:
        return "response:update,module:fireball,type:EMPTY\n"

    # Group the sprites by type to reduce the length of the response
    grouped_sprites = {}
    # The sprites of the same class are grouped together
    for sprite in spritegroup:
        sprite_id = sprite.sprite_id
        sprite_type = sprite.typename
        x, y = sprite.get_position()
        angle = sprite.angle

        if sprite_type in grouped_sprites:
            group = grouped_sprites[sprite_type]
        else:
            group = []
            grouped_sprites[sprite_type] = group

        group.append([sprite_id, x, y, angle])

    # Build the complete response from the grouped sprites
    response = "response:update,module:fireball\n"
    template_type = "type:{}\n"
    template_sprite = "id:{},x:{},y:{},angle:{}\n"
    for name, group in grouped_sprites.items():
        response += template_type.format(name)
        for data in group:
            sprite_id = data[0]
            x = data[1]
            y = data[2]
            angle = data[3]
            response += template_sprite.format(sprite_id, x, y, angle)

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
            id_list.append(sprite_id)
            x = float(data["x"])
            y = float(data["y"])
            angle = float(data["angle"])

            sprite = get(sprite_id)
            if sprite is None:
                add(sprite_type, [x, y], 500, angle, sprite_id)
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
    for sprite in spritegroup:
        sprite.update_server()

def clear():
    global next_id

    spritegroup.clear()
    next_id = 1

def add(typename, pos, distance, angle, sprite_id=None):
    global next_id

    if sprite_id is None:
        sprite_id = next_id
        next_id += 1

    sprite = None
    if typename == "FireballRed":
        sprite = FireballRed(pos, distance, angle, sprite_id)
        sprite.typename = typename
    elif typename == "FireballGreen":
        sprite = FireballGreen(pos, distance, angle, sprite_id)
        sprite.typename = typename
    elif typename == "FireballBlue":
        sprite = FireballBlue(pos, distance, angle, sprite_id)
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