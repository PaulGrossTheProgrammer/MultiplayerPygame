# Client/Server code to support distributed sprites

import random
import time

import pygame

import soundeffects

# Dictinaries for looking up group names to get a SharedSpriteGroup
groups_all = {}
groups_full_update = {}
groups_delta_update = {}

MAX_RESPONSE_BYTES = 8192
# MAX_RESPONSE_BYTES = 1024

class delta_entry():

    def __init__(self, delta_id, change):
        self.delta_id = delta_id
        self.change = change

        self.time_s = time.time()

delta_request_template = ",{}:{}"

def client_request_all_updates():
    updates = "request:update"

    # Any groups with non-zero delta_ids will request that value.
    for group in groups_all.values():
        if group.curr_delta_id != 0:
            req = delta_request_template.format(group.group_name, group.curr_delta_id)
            updates += req

    updates += "\n"

    return updates

def server_encode_all_responses(data, socket_thread):
    ''' Updates are progressively encoded, stopping before the total response
    exceeds the maximum number of bytes allowed.
    '''

    total_response = ""

    for group in groups_delta_update.values():
        # TODO - pass remaing bytes to encode_delta_response()
        # to allow partial delta updates
        bytes_remaining = MAX_RESPONSE_BYTES - len(total_response)
        delta_response = group.server_encode_delta_response(data, socket_thread,
                                                            bytes_remaining)
        if len(total_response) + len(delta_response) <= MAX_RESPONSE_BYTES:
            total_response += delta_response

    for group in groups_full_update.values():
        full_response = group.server_encode_full_response()
        if len(total_response) + len(full_response) <= MAX_RESPONSE_BYTES:
            total_response += full_response

    sound_response = soundeffects.encode_effects(socket_thread)
    if len(total_response) + len(sound_response) <= MAX_RESPONSE_BYTES:
        total_response += sound_response

    return total_response


def client_decode_all_updates(datalines):
    '''
    Returns True if the data included sprites, including EMPTY updates and deltas
    '''

    was_an_update = False

    module_updates = {}
    group_update = False

    for data in datalines:
        if "response" in data:
            response_type = data["response"]
            if response_type == "delta":
                group_name = data["group"]
                # group = groups_delta_update[group_name]
                group = groups_all[group_name]
                group.client_decode_delta_response(data)
                was_an_update = True

            if response_type == "update":
                group_update = True
                module = data["group"]
                module_group = []
                module_updates[module] = module_group
                was_an_update = True

            else:
                group_update = False

            if response_type == "soundeffects":
                soundeffects.decode_effects(data)
                group_update = False

        elif group_update is True:
            module_group.append(data)

    # FIXME - rename module_updates variable to group_updates
    for group_name, datalines in module_updates.items():
        group = groups_all[group_name]
        group.client_decode_full_response(datalines)

    return was_an_update


def set_position(sprite, pos):
    group = getattr(sprite, "group")
    group.set_position(sprite, pos)


class SharedSpriteGroup():
    '''Sprite Group that handles creating and removing distributed sprites.

    Includes converting all the sprites to/from Strings,
    so that the group's data can be sent across an Internet socket connection.

    Sprites are added to the group using the add() method.

    NOTE: Sprites added to the group MUST declare these methods:
        get_data() -> dict
        set_data(data: dict)

    OPTIONALLY: Sprites can declare an update_server() method that defines
    behaviour that only the server executes.
    '''

    update_template = "response:update,group:{}\n"
    update_template_empty = "response:update,group:{},type:EMPTY\n"

    def __init__(self, group_name, class_list):
        self.spritegroup = pygame.sprite.Group()
        self.next_id = 0

        self.group_name = group_name
        groups_all[group_name] = self
        self.curr_delta_id = 0

        self.update_string = self.update_template.format(group_name)
        self.update_string_empty = self.update_template_empty.format(
            group_name)

        self.class_list = class_list
        # Map the names to the classes on the list
        self.class_dict = {}
        for the_class in class_list:
            name_string = the_class.__name__
            self.class_dict[name_string] = the_class

        self.server = False
        self.enable_delta = False

    def set_as_server(self, enable_delta=False, delta_timeout_s=-1):
        self.server = True

        self.enable_delta = enable_delta
        if enable_delta is False:
            groups_full_update[self.group_name] = self
        else:
            groups_delta_update[self.group_name] = self
            self.enable_delta = True
            self.delta_list = []
            self.client_catchups = {}

            # The max seconds to keep old delta entries.
            # When set to -1, delta entries are never deleted.
            self.delta_timeout_s = delta_timeout_s

    def server_encode_full_response(self, delta_id=0):
        '''Called by the Server to create an update string
        containing the data needed all sprites in the spritegroup.

        Note: Calls get_data() for each sprite.
        '''

        if len(self.spritegroup) == 0:
            return self.update_string_empty

        # Group the sprites by type to reduce the length of the response
        grouped_sprites = {}
        # The sprites of the same class are grouped together
        for sprite in self.spritegroup:
            sprite_type = getattr(sprite, "typename")

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

    def client_decode_full_response(self, datalines):
        '''Called by the Clients to decode an update string
        to decode the data for each sprite.

        Note: Calls set_data() for each sprite.
        '''

        # TODO Add check for NOT server mode

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
                self.remove(sprite)

    def server_encode_delta_response(self, data, client_thread, bytes_remaining):
        if self.group_name in data:
            client_delta_id = int(data[self.group_name])
        else:
            client_delta_id = 0  # A blank delta id means zero.

        template = "response:delta,group:{},delta_id:{},{}\n"
        delta_new = ""

        if client_delta_id >= 0:
            # print("Number of delta entries = {}".format(len(self.delta_list)))
            # print("Server delta_id = {}".format(self.curr_delta_id))

            # Exit if both client and server match current deltas.
            if self.curr_delta_id == client_delta_id:
                # TODO - build response in __init__() instead
                return "response:delta,group:{},type:EMPTY\n".format(self.group_name)

            # Encode the entries after the current entry
            # print("Server scanning list...")
            found_start = False
            for entry in self.delta_list:
                curr_did = entry.delta_id
                # print(str(curr_did))

                if found_start is False and curr_did == client_delta_id + 1:
                    found_start = True
                    # print("Found start")

                if found_start is True and curr_did > client_delta_id:
                    change = entry.change
                    message = template.format(self.group_name, curr_did, change)

                    # Stop adding messages if bytes_remaining would be exceeded
                    if len(delta_new) + len(message) > bytes_remaining:
                        print("WARNING: message size exceeded")
                        print("Stopping before {}".format(curr_did))
                        break

                    delta_new += message

            if len(delta_new) > 0:
                return delta_new
            else:
                # FIXME - if there are no matching entries, create a catchup list
                # print("WARNING - no delta entries found for client")
                self.server_create_catchup(client_thread)
                client_delta_id = 0

        print("TODO - handling client catchup...")

        # Get the catchup for the client thread
        curr_did = None
        found_start = False
        catchup_complete = False

        # FIXME - the catchup doesn't work properly when the message size is exceeded.

        catchup_list = self.client_catchups[client_thread]
        for entry in catchup_list:
            curr_did = entry.delta_id

            if found_start is False and curr_did == (client_delta_id - 1):
                found_start = True
                print("Found CATCHUP start")

            if found_start is True and curr_did < client_delta_id:
                change = entry.change
                message = template.format(self.group_name, curr_did, change)

                # Stop adding messages if bytes_remaining would be exceeded
                if len(delta_new) + len(message) > bytes_remaining:
                    print("WARNING: message size exceeded")
                    print("Stopping before {}".format(curr_did))
                    break

                if change.startswith("new_delta_id:"):
                    catchup_complete = True

            delta_new += message

        # When the last catchup entry is encoded, remove the whole catchup list
        if catchup_complete is True:
            self.client_catchups.pop(client_thread)

        return delta_new

    def server_create_catchup(self, client_thread):
        # Create a new catchup list
        print("Building new catchup list for client.")
        catchup_list = []
        self.client_catchups[client_thread] = catchup_list

        catchup_id = 0

        # Encode an "add" entry for each sprite.
        for sprite in self.spritegroup:
            sprite_id = getattr(sprite, "sprite_id")
            typename = getattr(sprite, "typename")

            line = "add_id:{},typename:{}".format(sprite_id, typename)
            # add remaining data elements
            data = sprite.get_data()
            for key in data:
                encoded_entry = "," + key + ":" + str(data[key])
                line += encoded_entry

            # Count backwards from zero. A negative number is the flag for catchup ids.
            catchup_id -= 1

            print(catchup_id)
            print("CATCHUP: " + line)
            entry = delta_entry(catchup_id, line)
            catchup_list.append(entry)

        # The last catchup entry is a special command that points the client back to
        # the main delta list.
        catchup_id -= 1
        entry = delta_entry(catchup_id,
                            "new_delta_id:{}".format(self.curr_delta_id))
        catchup_list.append(entry)

    def client_decode_delta_response(self, data):

        if data["group"] == self.group_name:
            if "type" in data and data["type"] == "EMPTY":
                # Client is up-to-date, so nothing to change!
                return

            data_delta_id = int(data.pop("delta_id"))

            self.curr_delta_id = data_delta_id
            print("{}: Latest delta = {}".format(self.group_name, self.curr_delta_id))
            if self.curr_delta_id < 0:
                print("CATCHUP MODE:")

                # A delta_id of -1 forces all sprites in the group to be deleted
                # Because a catchup has just begun.
                if self.curr_delta_id == -1:
                    print("Removing all sprites in " + self.group_name)
                    self.empty()

                print(data)

            # Maybe if rem_id=-1, all sprites in group are cleared?
            if "add_id" in data:
                sprite_id = int(data["add_id"])
                typename = data["typename"]
                self.add(typename, data, sprite_id)
            elif "rem_id" in data:
                sprite_id = int(data["rem_id"])
                # TODO - check for -1 and clear if found
                self.remove_with_id(sprite_id)
            elif "pos_id" in data:
                sprite_id = int(data["pos_id"])
                sprite = self.get(sprite_id)
                if sprite is None:
                    print("ERROR: No Client Sprite")
                else:
                    sprite.set_data(data)
            elif "new_delta_id" in data:
                self.curr_delta_id = int(data["new_delta_id"])

    def clear_old_delta_entries(self):
        if self.delta_timeout_s < 0:
            # Timeout disabled
            return

        # don't delete old delta entries if there are still clients catching up.
        if len(self.client_catchups) > 0:
            return

        now_s = time.time()
        delete_s = now_s - self.delta_timeout_s

        for entry in self.delta_list:
            if entry.time_s < delete_s:
                self.delta_list.remove(entry)

    def draw(self, screen):
        self.spritegroup.draw(screen)

    def update(self):
        self.spritegroup.update()

    def update_server(self):
        '''Any sprite in the spritegroup with an update_server() method
        will call that method, otherwise, the sprite's update() method
        is called instead.
        '''

        for sprite in self.spritegroup:
            possible_method = getattr(sprite, "update_server", None)
            if possible_method is not None and callable(possible_method):
                sprite.update_server()
            else:
                sprite.update()

    def empty(self):
        # FIXME - if used by server, track delta.
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
        setattr(sprite, "group", self)

        self.spritegroup.add(sprite)

        # Only encode new delta entries on the server
        if self.enable_delta is True and self.server is True:
            self.clear_old_delta_entries()

            line = "add_id:{},typename:{}".format(sprite_id, typename)
            # add remaining data elements
            for key in data:
                encoded_entry = "," + key + ":" + str(data[key])
                line += encoded_entry

            self.curr_delta_id += 1
            entry = delta_entry(self.curr_delta_id, line)
            self.delta_list.append(entry)
            # print("DEBUG: Added sprite id = {}".format(sprite_id))

        return sprite

    def set_position(self, sprite, pos):
        sprite.set_position(pos)
        sprite_id = getattr(sprite, "sprite_id")

        # Only encode new delta entries on the server
        if self.enable_delta is True:
            self.clear_old_delta_entries()

            line = "pos_id:{},x:{},y:{}".format(sprite_id, pos[0], pos[1])
            self.curr_delta_id += 1
            entry = delta_entry(self.curr_delta_id, line)
            self.delta_list.append(entry)
            # print("DEBUG: Moves sprite id = {}".format(sprite_id))

    def get(self, sprite_id):
        for sprite in self.spritegroup:
            curr_sprite_id = getattr(sprite, "sprite_id")
            if curr_sprite_id == sprite_id:
                return sprite
        return None

    def remove(self, sprite):
        if getattr(sprite, "group") is not self:
            print("ERROR: {} is not in {}".format(sprite, self))
            return False

        self.spritegroup.remove(sprite)

        # Only encode new delta entries on the server
        if self.enable_delta is True and self.server is True:
            self.clear_old_delta_entries()

            line = "rem_id:{}".format(getattr(sprite, "sprite_id"))

            self.curr_delta_id += 1
            de = delta_entry(self.curr_delta_id, line)
            self.delta_list.append(de)

        return True

    def remove_with_id(self, sprite_id):
        for sprite in self.spritegroup:
            curr_sprite_id = getattr(sprite, "sprite_id")
            if curr_sprite_id == sprite_id:
                self.remove(sprite)
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


def data_xy(position) -> dict:
    """Convenient method to turn a position list or tuple into dict {} values
    suitable for creating and moving sprites.

    Values take the form x:? and y:?.
    """

    return {"x": position[0], "y": position[1]}


def decode_dictionary(line) -> dict:
    dictionary = {}
    kv_list = line.split(",")  # break in to key-value pairs
    for entry in kv_list:
        pair = entry.split(":")
        dictionary[pair[0]] = pair[1]

    return dictionary

def decode_line(line):
    line = line.rstrip()  # Remove the end of line codes
    name_end = line.find(" ")
    if name_end == -1:
        # There are no key-value pairs. Just return the name
        return [line, None]

    name = line[:name_end]
    line = line[name_end+1:]

    dict = {}
    kv_list = line.split(",")  # break in to key-value pairs
    for entry in kv_list:
        pair = entry.split(":")
        dict[pair[0]] = pair[1]

    return [name, dict]

def decode_lines(lines):
    # Split into separate lines, discarding end of line codes
    lines_list = lines.splitlines(False)
    decoded_list = []
    for line in lines_list:
        decoded_list.append(decode_line(line))

    return decoded_list
