#Importación de librerías necesarias

import random #Se uliza random para generar un numero aleatorio
import sys #Se utiliza para cerrar el programa
import pygame #Se utiliza pygame para toda la funcionalidad del juego
from pygame.locals import *
import cv2 #Se utiliza openCV para el reconocimiento de la imagen mediante la cámara
import numpy as np #Se utiliza numpy para apoyar el trabajo de openCV mediante las estructuras de datos

# Variables globales del juego
FPS = 60
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 500
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
GROUNDY = SCREEN_HEIGHT
GAME_SPRITES = {}
GAME_SOUNDS = {}
PLAYER = 'assets/sprites/PALOMA1.png'
BACKGROUND = 'assets/sprites/FONDOMURAL.jpg'
COLUMN = 'assets/sprites/columna.png'
captura = cv2.VideoCapture(0)

#Función que muestra la pantalla inicial
def welcome_screen():
    player_x = int(SCREEN_WIDTH / 5)
    player_y = int((SCREEN_HEIGHT - GAME_SPRITES['player'].get_height()) / 2)

    while True:
        for event in pygame.event.get():
            # Eventos para cerrar el juego, tecla ESC
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            # Barra espaciadora para iniciar el juego
            elif event.type == KEYDOWN and event.key == K_SPACE:
                return
            else:
                SCREEN.blit(GAME_SPRITES['background'], (0, 0))
                SCREEN.blit(GAME_SPRITES['player'], (player_x, player_y))
                pygame.display.update()
                FPSCLOCK.tick(FPS)

#Función loop que ejecuta el juego
def main_game():
    #Se inicializan las variables de cada partida
    score = 0 #Puntuación inical
    column_vel_x = -9 #Velocidad de las columnas del mapa (las columnas son los obstáculos)
    player_vel_y = 5 #Velocidad con la que cae el jugador
    player_x = int(SCREEN_WIDTH / 5) #Posición inicial del jugador en X
    player_y = int(SCREEN_WIDTH / 2) #Posición inicial del jugador en Y
    new_column1 = get_random_column() #Generador de la primera columna
    new_column2 = get_random_column() #Generador de la segunda columna

    #upper_columns y lower_columns son objetos que indican las posiciones de las primeras columnas
    upper_columns = [
        {'x': SCREEN_WIDTH + 150, 'y': new_column1[0]['y']},
        {'x': SCREEN_WIDTH + 150 + (SCREEN_WIDTH / 2), 'y': new_column2[0]['y']}
    ]
    lower_columns = [
        {'x': SCREEN_WIDTH + 150, 'y': new_column1[1]['y']},
        {'x': SCREEN_WIDTH + 150 + (SCREEN_WIDTH / 2), 'y': new_column2[1]['y']}
    ]

    while True:
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
            y = int(moments['m01']/moments['m00'])
            player_y = y
            # Dibujamos una marca en el centro del objeto
            cv2.rectangle(imagen, (x, player_y), (x+2, player_y+2), (0, 0, 255), 2)
        #is_crashed es un valor booleano que indica si el jugador colisionó
        is_crashed = check_collide(player_x, player_y, upper_columns, lower_columns)
        if is_crashed:
            return

        # Verifica la posición del jugador y la de la columna
        player_mid_pos = player_x + GAME_SPRITES['player'].get_width() / 3
        for column in upper_columns:
            column_mid_pos = column['x'] + GAME_SPRITES['column'][0].get_width() / 3
            #Si el jugador pasa la columna se actualiza el puntaje y se reproduce un sonido
            if column_mid_pos <= player_mid_pos < column_mid_pos + 10:
                score += 1
                GAME_SOUNDS['point'].play()
        player_height = GAME_SPRITES['player'].get_height()
        #Actualización de la posición y del jugador si no se detecta movimiento
        player_y = player_y + player_vel_y

        # Movimiento de columnas las columnas hacia la izquierda
        for upper_column, lower_column in zip(upper_columns, lower_columns):
            upper_column['x'] += column_vel_x
            lower_column['x'] += column_vel_x

        # Agrega una nueva columna cunado la primera se está ocultando
        if 0 < upper_columns[0]['x'] < abs(column_vel_x) + 1:
            newcolumn = get_random_column()
            upper_columns.append(newcolumn[0])
            lower_columns.append(newcolumn[1])

        # Si la columna está fuera de la ventana, se remueve del arreglo de columnas
        if upper_columns[0]['x'] < -GAME_SPRITES['column'][0].get_width():
            upper_columns.pop(0)
            lower_columns.pop(0)

        SCREEN.blit(GAME_SPRITES['background'], (0, 0))
        for upper_column, lower_column in zip(upper_columns, lower_columns):
            SCREEN.blit(GAME_SPRITES['column'][0],
                        (upper_column['x'], upper_column['y']))
            SCREEN.blit(GAME_SPRITES['column'][1],
                        (lower_column['x'], lower_column['y']))

        SCREEN.blit(GAME_SPRITES['player'], (player_x, player_y))
        #Actualización de puntaje en pantalla
        my_digits = [int(x) for x in list(str(score))]
        width = 0
        for digit in my_digits:
            width += GAME_SPRITES['numbers'][digit].get_width()
        x_offset = (SCREEN_WIDTH - width) / 2

        for digit in my_digits:
            SCREEN.blit(GAME_SPRITES['numbers'][digit],
                        (x_offset, SCREEN_HEIGHT * 0.12))
            x_offset += GAME_SPRITES['numbers'][digit].get_width()
        pygame.display.update()
        FPSCLOCK.tick(FPS)

#Esta función se encarga de verificar si el jugador no ha colisionado con algún elemento
def check_collide(player_x, player_y, upper_columns, lower_columns):
    #Verifica la colisión con el piso o el techo
    if player_y >= GROUNDY - 40 or player_y < 0:
        GAME_SOUNDS['hit'].play()
        return True
    for column in upper_columns:
        column_height = GAME_SPRITES['column'][0].get_height()
        #Verifica la colisión con las columnas de la parte alta
        if(player_y < column_height + column['y'] and abs(player_x - column['x']) < GAME_SPRITES['column'][0].get_width()):
            GAME_SOUNDS['hit'].play()
            return True
    for column in lower_columns:
        #Verifica la colisión con las columnas de la parte baja
        if (player_y + GAME_SPRITES['player'].get_height() > column['y']) and abs(player_x - column['x']) < GAME_SPRITES['column'][0].get_width():
            GAME_SOUNDS['hit'].play()
            return True
    return False

#Esta función se encarga de generar nuevas columnas en posiciones aleatorias
def get_random_column():
    column_height = GAME_SPRITES['column'][0].get_height()
    offset = SCREEN_HEIGHT / 5
    y2 = offset + random.randrange(0, int(SCREEN_HEIGHT - 1.2 * offset))
    column_x = SCREEN_WIDTH + 10
    y1 = column_height - y2 + offset
    column = [
        {'x': column_x, 'y': -y1},  # columna parte alta
        {'x': column_x, 'y': y2}  # columna parte baja
    ]
    return column


if __name__ == "__main__":
    # Función principal que inicializa el programa
    pygame.init()  # Inicializa pygame y sus módulos
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_caption('Flappy Dove UdeA')
    #Se le indica a pygame que utilice las imagenes contenidas en la carpeta assets
    GAME_SPRITES['numbers'] = (
        pygame.image.load('assets/sprites/0.png').convert_alpha(),
        pygame.image.load('assets/sprites/1.png').convert_alpha(),
        pygame.image.load('assets/sprites/2.png').convert_alpha(),
        pygame.image.load('assets/sprites/3.png').convert_alpha(),
        pygame.image.load('assets/sprites/4.png').convert_alpha(),
        pygame.image.load('assets/sprites/5.png').convert_alpha(),
        pygame.image.load('assets/sprites/6.png').convert_alpha(),
        pygame.image.load('assets/sprites/7.png').convert_alpha(),
        pygame.image.load('assets/sprites/8.png').convert_alpha(),
        pygame.image.load('assets/sprites/9.png').convert_alpha())
    #Transformación de rotación sobre la columna
    GAME_SPRITES['column'] = (pygame.transform.rotate(pygame.image.load(
        COLUMN).convert_alpha(), 180), pygame.image.load(COLUMN).convert_alpha())
    #Sonidos utilizados por el juego
    GAME_SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit.wav')
    GAME_SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point.wav')
    GAME_SPRITES['background'] = pygame.image.load(BACKGROUND).convert()
    GAME_SPRITES['player'] = pygame.image.load(PLAYER).convert_alpha()

    while True:
        welcome_screen()  # Ejecución de la pantalla de bienvenida
        main_game()  # Ejecución del juego
