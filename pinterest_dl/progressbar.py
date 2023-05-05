#!/usr/bin/env python3

import sys
from time import sleep


class Progressbar:
    """
    class to manage and draw progress bars
    """

    UP = "\x1b[1A"
    CLR = "\x1b[2K"
    string = ""
    instances = []
    final = False

    def __init__(self, id, total_data=0, max=100, chars="█ "):
        # default values

        self.id = id

        self.char_undone = chars[-1]
        self.char_done = chars[-2]
        self.char_process = chars[0:-1]

        self.line = ""
        self.caption = ""

        self.total_data = total_data
        self.max = max

        self.bank = 0
        self.done = 0

        self.end = False

        self.__class__.instances.append(self)

        if id == 0:
            self.max = 0

    def setup(self, total_data, max=None, chars=None, update=False):
        """
        for flexibility of the bar
        """

        self.total_data = total_data

        if max is not None:
            self.max = max

        if chars is not None:
            self.char_undone = chars[-1]
            self.char_done = chars[-2]
            self.char_process = chars[0:-1]

        self.line = ""
        self.caption = ""

        self.bank = 0
        self.done = 0

        self.end = False

        if update:
            line_count = self.string.count("\n")
            sys.stdout.write((self.UP + self.CLR) * line_count + "\r")

    def step(self, unit, debug=False):
        if self.done == self.max:
            return

        if self.total_data <= 0:
            self.done = self.max
            return

        self.bank += unit

        self.done = (self.max * self.bank) / self.total_data

        char_done_number = int(self.done // 1)

        # 8 - 1%

        char_process_number = int((self.done - char_done_number) // (1 / len(self.char_process)))

        # bar draw

        done_section = self.char_done * char_done_number

        if char_done_number == self.max:
            process_section = self.char_done
        else:
            process_section = self.char_process[char_process_number]

        undone_section = self.char_undone * (self.max - char_done_number)

        # debug caption
        if debug:
            self.caption = f"{self.max} {self.done} {char_done_number} {char_process_number}\n"

        # final progress line
        self.line = f'{self.caption}|{done_section}{process_section}{undone_section}| -- {int(self.done)}/{self.max}\n'

    def set_caption(self, text):
        self.caption = text + "\n"

    def list_bars(self):
        return self.instances

    def update(self):
        self.string = ""

        end_check = len(self.instances)

        for inst in self.instances:
            if inst.done == inst.max:
                end_check -= 1
                self.end = True

            self.string += inst.line

        line_count = self.string.count("\n")

        sys.stdout.write(self.string)

        if end_check == 0:
            self.final = True
        else:
            sys.stdout.write((self.UP) * line_count + "\r")


def progress_wrapper(func):
    """
    wrapper to hide cursor and show it after everything is done
    """

    def wrapper(*args, **kwargs):
        HIDE = "\x1b[?25l"
        SHOW = "\x1b[?25h"

        try:
            sys.stdout.write(HIDE)

            func(*args, **kwargs)

        finally:
            sys.stdout.write(SHOW)

    return wrapper


if __name__ == "__main__":
    # test

    @progress_wrapper
    def show_progress(a, b):
        manager = Progressbar(0)
        pr1 = Progressbar(1, a, chars=["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", " "])
        pr2 = Progressbar(2, b, chars="* ")

        # pr1.set_caption("gh:")

        for g in range(900):
            sleep(0.9)
            pr1.set_caption(f"Iteration: {g}")

            pr1.step(1)
            pr2.step(1)

            if g == 3:
                pr1.setup(total_data=100)

            if not manager.final:
                manager.update()
            else:
                break

    show_progress(20, 50)
