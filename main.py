import random
import sys
import pygame
from pygame.locals import *
import cv2
import numpy as np
# Global Variables for the game
FPS = 30
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 520
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
GROUNDY = SCREEN_HEIGHT
GAME_SPRITES = {}
GAME_SOUNDS = {}
PLAYER = 'gallery/sprites/PALOMA1.png'
BACKGROUND = 'gallery/sprites/FONDOMURAL.jpg'
PIPE = 'gallery/sprites/columna.png'
captura = cv2.VideoCapture(0)

def welcomeScreen():
    player_x = int(SCREEN_WIDTH / 5)
    player_y = int((SCREEN_HEIGHT - GAME_SPRITES['player'].get_height()) / 2)
    messagey = int(SCREEN_HEIGHT * 0.13)
    # base_x = 0

    while True:
        for event in pygame.event.get():
            # if user clicks on cross button, close the game
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            # If the user presses space or up key, start the game for them
            elif event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP): 
                return
            else:
                SCREEN.blit(GAME_SPRITES['background'], (0, 0))
                SCREEN.blit(GAME_SPRITES['player'], (player_x, player_y))
                pygame.display.update()
                FPSCLOCK.tick(FPS)


def mainGame():
    score = 0
    player_x = int(SCREEN_WIDTH / 5)
    player_y = int(SCREEN_WIDTH / 2)
    base_x = 0

    # Create 2 pipes for blitting on the screen
    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    # my List of upper pipes
    upper_pipes = [
        {'x': SCREEN_WIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREEN_WIDTH + 200 + (SCREEN_WIDTH / 2), 'y': newPipe2[0]['y']}
    ]
    # my List of lower pipes
    lower_pipes = [
        {'x': SCREEN_WIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREEN_WIDTH + 200 + (SCREEN_WIDTH / 2), 'y': newPipe2[1]['y']}
    ]

    pipe_vel_x = -4
    player_vel_y = -9
    player_vel_x = 10
    player_max_vel_y = 10
    player_min_vel_y = -8
    player_acc_y = 1

    playerFlapAccv = -10  # velocity while flapping
    playerFlapped = False  # It is true only when the bird is flapping

    while True:
       
        print(f'X: {player_x}, Y: {player_y}')
        _, imagen = captura.read()
        hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)

    # Establecemos el rango de colores que vamos a detectar
    # En este caso de azul oscuro a azul-azulado claro
        azul_bajos = np.array([105, 155, 20], dtype=np.uint8)
        azul_altos = np.array([123, 255, 255], dtype=np.uint8)

    # Crear una mascara con solo los pixeles dentro del rango de azuls
        mask = cv2.inRange(hsv, azul_bajos, azul_altos)

          # Encontrar el area de los objetos que detecta la camara
        moments = cv2.moments(mask)
        area = moments['m00']
        if(area > 2000000):

        # Buscamos el centro x, y del objeto
            x = int(moments['m10']/moments['m00'])
            player_y = int(moments['m01']/moments['m00'])

        # Mostramos sus coordenadas por pantalla
            print("x = ", x)
            print("y = ", player_y)

        # Dibujamos una marca en el centro del objeto
            cv2.rectangle(imagen, (x, player_y), (x+2, player_y+2), (0, 0, 255), 2)
        
        # cv2.imshow('mask', mask)   
        # cv2.imshow('Camara', imagen)    
        is_crashed = isCollide(player_x, player_y, upper_pipes, lower_pipes)
        if is_crashed:
            return

        # check for score
        playerMidPos = player_x + GAME_SPRITES['player'].get_width() / 2
        for pipe in upper_pipes:
            pipeMidPos = pipe['x'] + GAME_SPRITES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                GAME_SOUNDS['point'].play()
        if player_vel_y < player_max_vel_y and not playerFlapped:
            player_vel_y += player_acc_y
        if playerFlapped:
            playerFlapped = False
        playerHeight = GAME_SPRITES['player'].get_height()
        # player_y = player_y + min(player_vel_y, GROUNDY - player_y - playerHeight)

        # move pipes to the left
        for upper_pipe, lower_pipe in zip(upper_pipes, lower_pipes):
            upper_pipe['x'] += pipe_vel_x
            lower_pipe['x'] += pipe_vel_x

        # Add a new pipe when the first is about to cross the leftmost part of the screen
        if 0 < upper_pipes[0]['x'] < 5:
            newpipe = getRandomPipe()
            upper_pipes.append(newpipe[0])
            lower_pipes.append(newpipe[1])

        # if the pipe is out of the screen, remove it
        if upper_pipes[0]['x'] < -GAME_SPRITES['pipe'][0].get_width():
            upper_pipes.pop(0)
            lower_pipes.pop(0)

        # Lets blit our sprites now
        SCREEN.blit(GAME_SPRITES['background'], (0, 0))
        for upper_pipe, lower_pipe in zip(upper_pipes, lower_pipes):
            SCREEN.blit(GAME_SPRITES['pipe'][0],
                        (upper_pipe['x'], upper_pipe['y']))
            SCREEN.blit(GAME_SPRITES['pipe'][1],
                        (lower_pipe['x'], lower_pipe['y']))

        # SCREEN.blit(GAME_SPRITES['base'], (base_x, GROUNDY))
        SCREEN.blit(GAME_SPRITES['player'], (player_x, player_y))
        myDigits = [int(x) for x in list(str(score))]
        width = 0
        for digit in myDigits:
            width += GAME_SPRITES['numbers'][digit].get_width()
        x_offset = (SCREEN_WIDTH - width) / 2

        for digit in myDigits:
            SCREEN.blit(GAME_SPRITES['numbers'][digit],
                        (x_offset, SCREEN_HEIGHT * 0.12))
            x_offset += GAME_SPRITES['numbers'][digit].get_width()
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def isCollide(player_x, player_y, upper_pipes, lower_pipes):
    if player_y >= GROUNDY - 25 or player_y < 0:
        GAME_SOUNDS['hit'].play()
        return True
    for pipe in upper_pipes:
        pipe_height = GAME_SPRITES['pipe'][0].get_height()
        if(player_y < pipe_height + pipe['y'] and abs(player_x - pipe['x']) < GAME_SPRITES['pipe'][0].get_width()):
            GAME_SOUNDS['hit'].play()
            return True
    for pipe in lower_pipes:
        if (player_y + GAME_SPRITES['player'].get_height() > pipe['y']) and abs(player_x - pipe['x']) < GAME_SPRITES['pipe'][0].get_width():
            GAME_SOUNDS['hit'].play()
            return True
    return False


def getRandomPipe():
    pipe_height = GAME_SPRITES['pipe'][0].get_height()
    offset = SCREEN_HEIGHT / 3
    y2 = offset + random.randrange(0, int(SCREEN_HEIGHT - 1.2 * offset))
    pipe_x = SCREEN_WIDTH + 10
    y1 = pipe_height - y2 + offset
    pipe = [
        {'x': pipe_x, 'y': -y1},  # upper Pipe
        {'x': pipe_x, 'y': y2}  # lower Pipe
    ]
    return pipe


if __name__ == "__main__":
    # This will be the main point from where our game will start
    pygame.init()  # Initialize all pygame's modules
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_caption('Flappy Dove UdeA')
    GAME_SPRITES['numbers'] = (
        pygame.image.load('gallery/sprites/0.png').convert_alpha(),
        pygame.image.load('gallery/sprites/1.png').convert_alpha(),
        pygame.image.load('gallery/sprites/2.png').convert_alpha(),
        pygame.image.load('gallery/sprites/3.png').convert_alpha(),
        pygame.image.load('gallery/sprites/4.png').convert_alpha(),
        pygame.image.load('gallery/sprites/5.png').convert_alpha(),
        pygame.image.load('gallery/sprites/6.png').convert_alpha(),
        pygame.image.load('gallery/sprites/7.png').convert_alpha(),
        pygame.image.load('gallery/sprites/8.png').convert_alpha(),
        pygame.image.load('gallery/sprites/9.png').convert_alpha())

    GAME_SPRITES['pipe'] = (pygame.transform.rotate(pygame.image.load(PIPE).convert_alpha(), 180), pygame.image.load(PIPE).convert_alpha())
    GAME_SOUNDS['die'] = pygame.mixer.Sound('gallery/audio/die.wav')
    GAME_SOUNDS['hit'] = pygame.mixer.Sound('gallery/audio/hit.wav')
    GAME_SOUNDS['point'] = pygame.mixer.Sound('gallery/audio/point.wav')
    GAME_SOUNDS['swoosh'] = pygame.mixer.Sound('gallery/audio/swoosh.wav')
    GAME_SPRITES['background'] = pygame.image.load(BACKGROUND).convert()
    GAME_SPRITES['player'] = pygame.image.load(PLAYER).convert_alpha()

    while True:
        welcomeScreen()  # Shows welcome screen to the user until he presses a button
        mainGame()  # This is the main game function
