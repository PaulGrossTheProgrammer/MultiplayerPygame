# Data and code common to the whole game
import math

import pygame

server_port = 56789

image_folder = "images/"
sounds_folder = "sounds/"
maps_folder = "maps/"

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

frames_per_second = 25

clock = pygame.time.Clock()

def calc_distance(p1, p2):
    ''' Given two points p1 and p2,
    returns the distance between p1 and p2.
    '''
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.sqrt(dx*dx + dy*dy)


def calc_angle(p1, p2):
    ''' Given two points p1 and p2,
    returns the angle from p1 to p2 in radians.
    '''
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.atan2(dy, dx)
    return angle


def calc_endpoint(start, angle, distance):
    ''' Given the start point, and the angle of travel and distance of travel,
    returns the end point.
    '''
    dx = int(math.cos(angle) * distance)
    dy = int(math.sin(angle) * distance)
    end_x = start[0] + dx
    end_y = start[1] + dy
    return (end_x, end_y)
