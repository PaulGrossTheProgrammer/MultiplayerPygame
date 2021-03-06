import time

import pygame
from common import sounds_folder

# buffer=128 gives less sound delay compared to default of 512
pygame.mixer.init(buffer=128)

# Background music
# pygame.mixer.music.load(sounds_folder + 'DungeonMusic-02.wav')

effects_dict = {}

class Soundeffect():

    def __init__(self, sound, default_volume=1.0):
        self.sound = sound
        self.default_volume = default_volume
        self.sound.set_volume(default_volume)

    def play(self):
        self.sound.play()

def set_global_volume(volume):
    if volume < 0.0:
        volume = 0.0
    if volume > 1.0:
        volume = 1.0

    # TODO - convert to exponential curve

    for effect in effects_dict.values():
        # default_volume = 1.0
        default_volume = effect.default_volume
        new_volume = default_volume * volume
        effect.sound.set_volume(new_volume)


def add_effect(name, sound, default_volume=1.0):
    effect = Soundeffect(sound, default_volume)
    effects_dict[name] = effect


fireball = pygame.mixer.Sound(sounds_folder + "fireball.wav")
add_effect("fireball", fireball)

explosion = pygame.mixer.Sound(sounds_folder + "explosion.wav")
add_effect("explosion", explosion)

painhit = pygame.mixer.Sound(sounds_folder + "paind.wav")
add_effect("painhit", painhit)

monsterkill = pygame.mixer.Sound(sounds_folder + "deathr.wav")
add_effect("monsterkill", monsterkill)

pickup_1 = pygame.mixer.Sound(sounds_folder + "pickup-01.wav")
add_effect("pickup_1", pickup_1, default_volume=0.1)

pickup_2 = pygame.mixer.Sound(sounds_folder + "pickup-02.wav")
add_effect("pickup_2", pickup_2, default_volume=0.1)

pickup_3 = pygame.mixer.Sound(sounds_folder + "pickup-03.wav")
add_effect("pickup_3", pickup_3, default_volume=0.1)

pickup_4 = pygame.mixer.Sound(sounds_folder + "pickup-04.wav")
add_effect("pickup_4", pickup_4, default_volume=0.1)

pickup_5 = pygame.mixer.Sound(sounds_folder + "Item2A.wav")
add_effect("pickup_5", pickup_5, default_volume=0.5)

pickup_6 = pygame.mixer.Sound(sounds_folder + "Menu2A.wav")
add_effect("pickup_6", pickup_6, default_volume=0.5)


def play(name):
    effect_instance = effects_dict.get(name, None)
    if effect_instance is not None:
        effect_instance.sound.play()
    else:
        print("Unknown sound effect [{}]".format(name))

expiry_seconds = 0.200

class SoundEffect():

    def __init__(self, name, expiry, clients_done):
        self.name = name
        self.expiry = expiry
        self.clients_done = clients_done

shared_sound_effects = []  # List of current sound effects

def add_shared(name):
    if name not in effects_dict:
        print("Unknown sound effect [{}]".format(name))
        return

    expiry = time.time() + expiry_seconds
    new_effect = SoundEffect(name, expiry, [])
    shared_sound_effects.append(new_effect)

def remove_expired():
    current_time = time.time()
    for e in shared_sound_effects:
        if e.expiry < current_time:
            shared_sound_effects.remove(e)

def encode_effects(client_socket):
    names = None
    # Look through the list for all sounds not yet encoded for that socket
    for e in shared_sound_effects:
        if client_socket not in e.clients_done:
            e.clients_done.append(client_socket)
            if names is None:
                names = e.name
            else:
                names += ";" + e.name

    if names is not None:
        template = "response:soundeffects,names:{}\n"
        return template.format(names)
    else:
        return ""

def decode_effects(data):
    names = data.get("names", None)
    if names is None:
        print("No Sound effects")
        return

    names_list = names.split(";")
    for name in names_list:
        play(name)