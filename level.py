
import common
import clientserver
import dungeontiles


def create_dungeon(text):

    lines = text.split("\n")
    reading_map = False
    reading_key = False
    key_dict = {}
    map_row = 0

    for line in lines:
        if reading_key is False and line.startswith("KEY START"):
            reading_key = True
            continue  # Go to next line

        if reading_key is True:
            if line.startswith("KEY END"):
                reading_key = False
                continue

            # Split the key from the values
            key = line[0]
            values = line[2:]  # FIXME - to end
            value_pairs = values.split(",")
            values_dict = {}
            for pair in value_pairs:
                pair_list = pair.split(":")
                values_dict[pair_list[0]] = pair_list[1]

            key_dict[key] = values_dict

        if reading_map is False and line.startswith("MAP START"):
            reading_map = True
            continue  # Go to next line

        if reading_map is True:
            if line.startswith("MAP END"):
                reading_map = False
                continue

            map_col = 0
            for curr_char in line:

                x = int(map_col * dungeontiles.tile_size + dungeontiles.tile_size/2)
                y = int(map_row * dungeontiles.tile_size + dungeontiles.tile_size/2)

                # Lookup char in key_dict
                if curr_char in key_dict:
                    values_dict = key_dict[curr_char]
                    if values_dict is not None:
                        name = values_dict["name"]
                        if name == "wall":
                            # wall_group.add(dungeontiles.WallTile([x, y]))
                            data = clientserver.data_xy([x, y])
                            dungeontiles.shared.add("WallTile", data)

                map_col += 1

            map_row += 1

def start_level(mapname=""):

    # mapname = common.maps_folder+"map_amelie.txt"
    with open(common.maps_folder+mapname) as f:
        mapdata = f.read()

    create_dungeon(mapdata)
