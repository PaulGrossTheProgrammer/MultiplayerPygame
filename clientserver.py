# Client/Server code to support distributed sprites

import random

import pygame


class SharedSpriteGroup():
    """Sprite Group that handles creating and removing distributed sprites.

    Includes converting all the sprites to/from Strings,
    so that the group's data can be sent across an Internet socket connection.

    Sprites are added to the group using the add() method.

    NOTE: Sprites added to the group MUST declare these methods:
        get_data() -> dict
        set_data(data: dict)

    OPTIONALLY: Sprites can declare an update_server() method that defines
    behaviour that only the server executes.
    """

    update_template = "response:update,group:{}\n"
    update_template_empty = "response:update,group:{},type:EMPTY\n"

    def __init__(self, group_name, class_list):
        self.spritegroup = pygame.sprite.Group()
        self.next_id = 0

        self.group_name = group_name
        self.update_string = self.update_template.format(group_name)
        self.update_string_empty = self.update_template_empty.format(
            group_name)

        self.class_list = class_list
        # Map the names to the classes on the list
        self.class_dict = {}
        for the_class in class_list:
            name_string = the_class.__name__
            self.class_dict[name_string] = the_class

    def encode_update(self):
        """Called by the Server to create an update string
        containing the data needed all sprites in the spritegroup.

        Note: Calls get_data() for each sprite.
        """

        if len(self.spritegroup) == 0:
            return self.update_string_empty

        # Group the sprites by type to reduce the length of the response
        grouped_sprites = {}
        # The sprites of the same class are grouped together
        for sprite in self.spritegroup:
            sprite_type = getattr(sprite, "typename")

            # x, y = sprite.get_position()  # replace with get_data()
            data = sprite.get_data()
            data["sprite_id"] = getattr(sprite, "sprite_id")

            if sprite_type in grouped_sprites:
                # Get the existing group
                group = grouped_sprites[sprite_type]
            else:
                # Create the group and add it
                group = []
                grouped_sprites[sprite_type] = group

            group.append(data)

        # Build the complete response from the grouped sprites
        response = self.update_string
        template_type = "type:{}\n"
        # template_sprite = "id:{},x:{},y:{}\n"
        for name, group in grouped_sprites.items():
            response += template_type.format(name)
            for data in group:
                # Extract the sprite_id
                sprite_id = data.pop("sprite_id")
                line = "id:{}".format(sprite_id)
                # add remaining data elements
                for key in data:
                    encoded_entry = "," + key + ":" + data[key]
                    line += encoded_entry

                response += line + "\n"

        return response

    def decode_update(self, datalines):
        """Called by the Clients to decode an update string
        to decode the data for each sprite.

        Note: Calls set_data() for each sprite.
        """

        id_list = []
        sprite_type = None
        for data in datalines:
            if "type" in data:
                sprite_type = data["type"]
            elif sprite_type is not None:
                # Remove id from the dict
                sprite_id = int(data.pop("id"))
                id_list.append(sprite_id)

                sprite = self.get(sprite_id)
                if sprite is None:
                    self.add(sprite_type, data, sprite_id)
                else:
                    sprite.set_data(data)

        # Remove any sprites not included in the update
        for sprite in self.spritegroup:
            curr_id = sprite.sprite_id
            if curr_id not in id_list:
                self.remove(curr_id)

    def draw(self, screen):
        self.spritegroup.draw(screen)

    def update(self):
        self.spritegroup.update()

    def update_server(self):
        """Any sprite in the spritegroup with an update_server() method
        will call that method, otherwise, the sprite's update() method
        is called instead.
        """

        for sprite in self.spritegroup:
            possible_method = getattr(sprite, "update_server", None)
            if possible_method is not None and callable(possible_method):
                sprite.update_server()
            else:
                sprite.update()

    def empty(self):
        self.spritegroup.empty()
        self.next_id = 1

    def add(self, typename, data=None, sprite_id=None):
        if sprite_id is None:
            sprite_id = self.next_id
            self.next_id += 1

        if data is None:
            data = {}

        # TODO - handle incorrect typenames
        constructor = self.class_dict[typename]
        sprite = constructor()
        sprite.set_data(data)

        setattr(sprite, "sprite_id", sprite_id)
        setattr(sprite, "typename", typename)

        self.spritegroup.add(sprite)

        return sprite

    def get(self, sprite_id):
        for sprite in self.spritegroup:
            curr_sprite_id = getattr(sprite, "sprite_id")
            if curr_sprite_id == sprite_id:
                return sprite
        return None

    def remove(self, sprite_id):
        for sprite in self.spritegroup:
            curr_sprite_id = getattr(sprite, "sprite_id")
            if curr_sprite_id == sprite_id:
                self.spritegroup.remove(sprite)
                return True
        return False

    def has_id(self, sprite_id) -> bool:
        for sprite in self.spritegroup:
            curr_sprite_id = getattr(sprite, "sprite_id")
            if curr_sprite_id == sprite_id:
                return True
        return False

    def collide_sprites(self, point) -> list:
        coll = []
        for sprite in self.spritegroup:
            if sprite.rect.collidepoint(point):
                coll.append(sprite)
        return coll

    def collide_sprites_type(self, point, typename) -> list:
        coll = []
        for sprite in self.spritegroup:
            if sprite.rect.collidepoint(point) and sprite.typename == typename:
                coll.append(sprite)
        return coll

    def collide_sprite(self, point) -> pygame.sprite.Sprite:
        sprites = self.collide_sprites(point)
        if len(sprites) == 0:
            return None
        return sprites[0]

    def collide_sprite_type(self, point, typename) -> pygame.sprite.Sprite:
        sprites = self.collide_sprites_type(point, typename)
        if len(sprites) == 0:
            return None
        return sprites[0]

    def random_typename(self) -> str:
        """ Returns a random type from the class list as a string """

        return random.choice(list(self.class_dict.keys()))


def dict_xy(position) -> dict:
    """Convenient method to turn a position list or tuple into dict values.

    Values take the form x:? and y:?.
    """

    return {"x": position[0], "y": position[1]}