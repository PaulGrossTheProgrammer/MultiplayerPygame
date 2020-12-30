import pygame
from common import sounds_folder

# buffer=128 gives less sound delay compared to default of 512
pygame.mixer.init(buffer=128)

# Background music
# pygame.mixer.music.load(sounds_folder + 'DungeonMusic-02.wav')

fireball = pygame.mixer.Sound(sounds_folder + "fireball.wav")
explosion = pygame.mixer.Sound(sounds_folder + "explosion.wav")

pickup_1 = pygame.mixer.Sound(sounds_folder + "pickup-01.wav")
pickup_1.set_volume(0.1)
pickup_2 = pygame.mixer.Sound(sounds_folder + "pickup-02.wav")
pickup_2.set_volume(0.1)
pickup_3 = pygame.mixer.Sound(sounds_folder + "pickup-03.wav")
pickup_3.set_volume(0.1)
pickup_4 = pygame.mixer.Sound(sounds_folder + "pickup-04.wav")
pickup_4.set_volume(0.1)
pickup_5 = pygame.mixer.Sound(sounds_folder + "Item2A.wav")
pickup_5.set_volume(0.5)
pickup_6 = pygame.mixer.Sound(sounds_folder + "Menu2A.wav")
pickup_6.set_volume(0.5)