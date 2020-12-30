import pygame

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
screen = pygame.display.get_surface()

frames_per_second = 30
clock = pygame.time.Clock()

pause_text = "Press P to Resume, X to exit"
gameover_text = "GAMEOVER: Press R to Restart, X to exit"
levelcomplete_text = "LEVEL COMPLETE: Press R to Restart, X to exit"

message_font_50 = pygame.font.SysFont(pygame.font.get_default_font(), 50)

pause = message_font_50.render(pause_text, True, WHITE)
gameover = message_font_50.render(gameover_text, True, WHITE)
levelcomplete = message_font_50.render(levelcomplete_text, True, WHITE)

def draw(screen, image, position=None):
    rect = image.get_rect()
    if position is None:
        # TODO: Cetnter on the screen's current dimensions
        # rect.center = [SCREEN_WIDTH/2, SCREEN_HEIGHT/2]
        rect.center = [screen.get_width()/2, screen.get_height()/2]

    screen.blit(image, rect)

def drawtext(screen, text, size=None, color=None, position=None):
    global message_font_50

    if size is None:
        font = message_font_50
    else:
        font = pygame.font.SysFont(pygame.font.get_default_font(), size)

    if color is None:
        color = WHITE

    image = font.render(text, True, color)

    draw(screen, image, position)

game_on = True
while game_on:
    # Check for mouse and keyboard events
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            print("User closed the window")
            game_on = False

    pygame.display.flip()

    clock.tick(frames_per_second)

pygame.quit()
quit()