from time import sleep
from random import randint
import math
from sense_hat import SenseHat

sense = SenseHat()
sense.clear()

speed = 2

MATRIX_SIZE=8

matrix = [
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
        0,0,0,0,0,0,0,0,
    ]

w = ( 0, 128, 255 )
b = ( 0, 0, 0 )

def place_matrix(mtrx):
    sense.clear()
    for i, p in enumerate(mtrx):
        if (p == 0): continue
        y=i//MATRIX_SIZE
        x=i%MATRIX_SIZE
        sense.set_pixel(x,y,w)


def move_matrix(mtrx):
    for i, p in enumerate(mtrx):
        if (p == 0): continue
        x=i%MATRIX_SIZE
        if (x>0): mtrx[i-1]=1
        mtrx[i]=0

    place_matrix(mtrx)

def get_matrix():
    m = []
    pixels = sense.get_pixels()
    for p in pixels:
        if (tuple(p)==b): m.append(0)
        else: m.append(1)
    return m

def update_channel(value, inc, step=25):
    delta = randint(0, step)
    value += delta if inc else -delta

    if value >= 255:
        value = 255
        inc = False
    elif value <= 0:
        value = 0
        inc = True

    return value, inc

# 0 - cos, 1 - sin, 2 - both
def draw(n, arg):
    global w

    i=0
    x=0
    temp=0
    x_div=2
    if (arg == 0): r, g, b = 255, 0, 0
    elif (arg == 1): r, g, b = 0, 128, 255
    elif (arg == 2):
        r, g, b = 0, 18, 2
        r_inc, g_inc, b_inc = True, True, True
        x_div=1

    w = (r, g, b)
    while True:
        if round(i) == n:
            break

        x+=math.pi/(18/x_div)
        if (arg == 0):
            temp = (math.sin(x) ** 2) * 7

            sense.set_pixel(7, round(temp), w)
        elif (arg == 1):
             temp2 = (math.cos(x) ** 2) * 7

             sense.set_pixel(7, round(temp2), w)
        else:
            temp = (math.sin(x) ** 2) * 7
            temp2 = (math.cos(x) ** 2) * 7

            sense.set_pixel(7, round(temp), w)
            sense.set_pixel(7, round(temp2), w)


        sleep(0.1)
        if (arg == 2):
            r, r_inc = update_channel(r, r_inc)
            g, g_inc = update_channel(g, g_inc)
            b, b_inc = update_channel(b, b_inc)

            w = (r, g, b)

        mtrx = get_matrix()
        move_matrix(mtrx)

        i += 1 / 18

def start_show():
#    sense.show_message("sin():", scroll_speed=0.075/speed, text_colour=(0, 255, 0))
    draw(4, 1)

#    sense.show_message("cos():", scroll_speed=0.075/speed, text_colour=(0, 255, 0))
#    draw(4444, 0)

#    sense.show_message("Tgt:", scroll_speed=0.075/speed, text_colour=(0, 255, 0))
    while True:
        t = randint(1, 10)
        style = randint(0, 2)
        draw(t, style)


start_show()
