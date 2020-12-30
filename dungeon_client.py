# Pygame Internet Client
import pygame

from common import frames_per_second, SCREEN_WIDTH, SCREEN_HEIGHT

server_ip = input("Enter Server IP: ")
if len(server_ip) == 0:
    server_ip = "localhost"

pygame.init()

screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])

# The clock manages how fast the game updates
clock = pygame.time.Clock()

pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption('Player Test')

all_sprites = pygame.sprite.Group()
# Note: Need to attacj an ID from the server to each sprite so that changes can be copied.
# New sprites can be added if they are not already on the client,
# and sprites not on the server can be deleted from the client.

# Reads the locations of all the game sprites from the server
def request_server_update():
    return pygame.sprite.Group()

game_on = True
while game_on:
    # Check for mouse and keyboard events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("User closed the game window")
            game_on = False
        print(event)

    # Read each sprite location and velocity from server

    # Update sprites
    all_sprites = all_sprites.update()

    # Draw
    screen.fill(0)
    all_sprites.draw(screen)

    pygame.display.flip()

    clock.tick(frames_per_second)

pygame.quit()
quit()