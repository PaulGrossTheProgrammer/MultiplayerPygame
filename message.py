def decode_dictionary(line):
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