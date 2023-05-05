#!/usr/bin/env python3

import sys
from time import sleep
from colorama import Style, Back, Fore
import itertools


def test1():
    # BUP = "\x1b[F"
    # DOWN = "\x1b[B"

    HIDE = "\x1b[?25l"
    SHOW = "\x1b[?25h"

    UP = "\x1b[1A"
    # CLR = "\x1b[2K"

    try:
        for g in range(19):
            sleep(0.1)

            sys.stdout.write(HIDE)

            string = f"{g} - test1\n{g ** 2} second line\n"
            line_count = string.count("\n")

            sys.stdout.write(string)

            # sys.stdout.flush()

            # sys.stdout.write((UP + CLR) * line_count)

            if g != 18:
                sys.stdout.write((UP) * line_count + "\r")

    finally:
        sys.stdout.write(SHOW)


def test2(total_data, max=100, chars=" █"):
    UP = "\x1b[1A"

    char_undone = chars[0]
    char_done = chars[1]

    bank = 0

    def draw(unit):
        nonlocal bank

        bank += unit

        done = int((max * bank) / total_data)

        string = f'first line\n|{char_done * done}{char_undone * (max - done)}| -- {done}/{max}\n'

        line_count = string.count("\n")

        sys.stdout.write(string)

        if done == max:
            sys.stdout.write("\n")
        else:
            sys.stdout.write((UP) * line_count + "\r")

    return draw


# HIDE = "\x1b[?25l"
# SHOW = "\x1b[?25h"
#
# sys.stdout.write(HIDE)
#
# pr = test2(500)
#
# for _ in range(50):
#     sleep(0.1)
#     pr(10)
#
# sys.stdout.write(SHOW)




exit()

class Progressbar:
    UP = f"\x1b[1A"
    CLR = f"\x1b[0K"

    out = ""

    def __init__(self, chars={"done": ["█"], "undone": " "}):
        # chars
        self.chars_done = chars["done"]
        self.chars_undone = chars["undone"]

    def create_progressbar(self, total_data, max, unit):

        doning_char = itertools.cycle(self.chars_done)

        current_amount = 0

        def draw(unit):
            nonlocal current_amount

            current_amount += unit

            done = int((max * current_amount) / total_data)
            undone = (max - done)

            line = f'\r |{self.chars_done[-1] * (done - 1)}{next(doning_char)}{self.chars_undone * undone}| -- {done}/{max}'

            return line

        return draw

    def update(self):
        pass


pr = Progressbar()
pr1 = pr.create_progressbar(100, 100, 0)

g = 0

while g <= 100:
    g += 1
    sleep(0.1)

    print(pr1(g))

exit()

def draw_progress(max, total_data, data, draw_chars, indicator="□"):
    """
    draw progress when downloading
    """

    char_done = draw_chars[0]
    char_undone = draw_chars[1]

    downloaded = 0

    def draw(data):
        nonlocal downloaded

        downloaded += data

        done = int((max * downloaded) / total_data)

        color_done = Fore.RED + str(done) + Style.RESET_ALL
        if done == max:
            color_done = Fore.GREEN + str(done) + Style.RESET_ALL

        color_indicator = Back.RED + Fore.BLACK + indicator + Style.RESET_ALL

        sys.stdout.write(f'\r {color_indicator} |{char_done * done}{char_undone * (max - done)}| -- {color_done}/{max}')
        sys.stdout.flush()

        if done == max:
            sys.stdout.write("\n")

    return draw


max = 20
total_data = 100

# https://en.wikipedia.org/wiki/List_of_Unicode_characters#Block_Elements
# cool bars:
# https://stackoverflow.com/questions/3160699/python-progress-bar

# ▰▱
# ▂▁
# ▮▯
# ⬤◯
# ⬛⬜
# ▆▁
# █░
# blocks = ["", "▏","▎","▍","▌","▋","▊","▉","█"]
# ▒
# ▢
# □ 
# ▪ 
# ■
# ━━━━━ 

show_progress = draw_progress(max, total_data, 0, "█▒", "⬜")


for i in range(max):
    sleep(0.1)
    show_progress(5)
