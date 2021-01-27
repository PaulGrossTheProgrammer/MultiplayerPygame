# Monsters
import math
import random
import pygame
import spritesheet
import common
from common import image_folder

class Monster(pygame.sprite.Sprite):

    player = None  # Set this so that the monster can react to the player
    radius = 20
    speed = 1.0
    frame_change_trigger = 18

    def __init__(self, position, sprite_id):
        super().__init__()

        self.sprite_id = sprite_id
        self.typename = None
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        self.rect.center = position

        self.speed *= 60.0/common.frames_per_second

        # Track position as float values for better accuracy
        self.position_x = float(position[0])
        self.position_y = float(position[1])
        self.delta_x = 0.0
        self.delta_y = 0.0

        # Spritesheet animation
        # Start the monster on a random frame
        self.frame_curr = random.randrange(len(self.frames) - 1)
        self.frame_change_counter = 0

        # The monster makes decsions when triggered
        self.decision_trigger = 15
        self.decision_counter = 0

    def update(self):
        self.frame_change_counter += 1
        if self.frame_change_counter >= self.frame_change_trigger:
            self.frame_change_counter = 0
            self.frame_curr += 1  # Change frame
            if self.frame_curr >= len(self.frames):
                self.frame_curr = 0
        self.image = self.frames[self.frame_curr]

        # Update float postion values for better accuracy
        self.position_x += self.delta_x
        self.position_y += self.delta_y
        self.rect.center = [int(self.position_x), int(self.position_y)]

    def update_server(self):
        # If the player is set, attack the player
        if self.player is not None:
            # Periodically trigger decisions
            self.decision_counter += 1
            if self.decision_counter >= self.decision_trigger:
                self.decision_counter = 0

                # ---MONSTER ARTIFICAL INTELLIGENCE ---
                dx = self.player.rect.center[0] - self.rect.center[0]
                dy = self.player.rect.center[1] - self.rect.center[1]
                action = random.choice(["DIRECT", "XAXIS", "YAXIS"])
                if action == "DIRECT":
                    angle = math.atan2(dy, dx)
                    self.delta_x = math.cos(angle) * self.speed
                    self.delta_y = math.sin(angle) * self.speed
                elif action == "XAXIS":
                    self.delta_x = self.speed
                    self.delta_y = 0
                    if dx < 0:
                        self.delta_x = -self.delta_x
                elif action == "YAXIS":
                    self.delta_x = 0
                    self.delta_y = self.speed
                    if dy < 0:
                        self.delta_y = -self.delta_y

    def set_player(self, player):
        self.player = player

    def stop(self):
        self.delta_x = 0
        self.delta_y = 0

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

class PurplePeopleEater(Monster):
    sheet = spritesheet.Spritesheet(
        4, 1, filename=image_folder+"PurplePeopleEater-02.png")
    frames = sheet.get_frames()

    radius = 20
    speed = 1.3

class GreenZombie(Monster):
    sheet = spritesheet.Spritesheet(
        3, 1, filename=image_folder+"Zombie.png")
    frames = sheet.get_frames()

    radius = 12
    speed = 0.5

class BlueGhost(Monster):
    sheet = spritesheet.Spritesheet(
        28, 1, filename=image_folder+"sGhost_strip28.png")
    frames = sheet.get_frames()

    radius = 10
    speed = 1.8
    frame_change_trigger = 3


random_list = [PurplePeopleEater, GreenZombie, BlueGhost]

def random_monster(position):
    return random.choice(random_list)(position)

# Client/Server code

spritegroup = pygame.sprite.Group()
next_id = 0
# TODO - If next_id is large and the spritegroup is empty, reset the next_id

# Called by the server to encode the sprites as string for sending via Internet
# TODO - handle incremental updates:
# TODO - put complete:incremental or update:complete in response
def encode_update():
    if len(spritegroup) == 0:
        return "response:update,module:monsters,type:EMPTY\n"

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
    response = "response:update,module:monsters\n"
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
            x = float(data["x"])
            y = float(data["y"])
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
    for sprite in spritegroup:
        sprite.update_server()

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
    if typename == "PurplePeopleEater":
        sprite = PurplePeopleEater(pos, sprite_id)
        sprite.typename = typename
    elif typename == "GreenZombie":
        sprite = GreenZombie(pos, sprite_id)
        sprite.typename = typename
    elif typename == "BlueGhost":
        sprite = BlueGhost(pos, sprite_id)
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