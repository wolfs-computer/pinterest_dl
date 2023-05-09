#!/usr/bin/env python3

import sys
from time import sleep
from colorama import Back, Style, Fore


class Progressbar:
    """
    class to manage and draw progress bars
    """

    UP = "\x1b[1A"
    CLR = "\x1b[2K"
    string = ""
    instances = []
    final = False

    def __init__(self, id=0, total_data=0, max=100, char_max=50, chars="█ "):
        # default values

        self.id = id

        self.manager = False

        self.char_undone = chars[-1]
        self.char_done = chars[-2]
        self.char_process = chars[0:-1]

        self.line = ""

        self.caption = ""

        self.total_data = total_data
        self.max = max
        self.char_max = char_max

        self.bank = 0
        self.done = 0

        self.end = False

        self.form = "{caption}|{done_section}{process_section}{undone_section}| -- {done:.1f}/{max}\n"
        self.form_variables = dict.fromkeys(["caption", "done_section", "process_section", "undone_section", "done", "max"])

        self.__class__.instances.append(self)

        if id == 0:
            self.max = 0
            self.manager = True

    def setup(self, total_data=None, max=None, char_max=None, chars=None, form=None, form_variables=None, update=False):
        """
        for flexibility of the bar
        """

        if total_data is not None:
            self.total_data = total_data

        if max is not None:
            self.max = max

        if char_max is not None:
            self.char_max = char_max

        if chars is not None:
            self.char_undone = chars[-1]
            self.char_done = chars[-2]
            self.char_process = chars[0:-1]

        if form is not None:
            self.form = form
        if form_variables is not None:
            self.form_variables = form_variables

        self.line = ""
        # self.caption = ""

        self.bank = 0
        self.done = 0

        self.end = False

        if update:
            # if progress bar used more then once
            self.final = False
            line_count = self.string.count("\n")
            # sys.stdout.write((self.UP + self.CLR) * line_count + "\r")
            sys.stdout.write((self.UP) * line_count + "\r")

    def step(self, unit, debug=False):
        # print(self.done, self.max, unit, self.total_data)
        if self.done == self.max:
            return

        if self.total_data <= 0:
            self.done = self.max
            return

        self.bank += unit

        self.done = (self.max * self.bank) / self.total_data

        char_num_done = (self.char_max * self.bank) / self.total_data
        char_done_number = int(char_num_done // 1)

        # len(proc chars) -> 1%

        char_process_number = int((char_num_done - char_done_number) // (1 / len(self.char_process)))

        # bar draw

        done_section = self.char_done * char_done_number

        if char_done_number == self.char_max:
            process_section = self.char_done
        else:
            process_section = self.char_process[char_process_number]

        undone_section = self.char_undone * (self.char_max - char_done_number)

        # final progress line
        # self.line = f'{self.caption}|{done_section}{process_section}{undone_section}| -- {int(self.done)}/{self.max}\n'

        default_form_variables = {}
        default_form_variables["caption"] = self.caption
        default_form_variables["done_section"] = done_section
        default_form_variables["process_section"] = process_section
        default_form_variables["undone_section"] = undone_section
        default_form_variables["done"] = self.done
        default_form_variables["max"] = self.max

        # update with values
        for key in self.form_variables.keys():
            # <if> to allow custom variables, not only default
            if key in default_form_variables:
                self.form_variables[key] = default_form_variables[key]

        # final progress bar string
        self.line = self.form.format(**self.form_variables)

    def set_caption(self, text):
        self.caption = text + "\n"

    def add_caption(self, text):
        self.caption = self.caption.split("\n")[0] + text + "\n"

    def debug(self):
        self.caption = f"{self.max} {self.done} {char_done_number} {char_process_number}\n"

    def list_bars(self):
        return self.instances

    def cleanup(self):
        # temporal?
        line_count = self.string.count("\n")
        sys.stdout.write(("\n") * line_count + "\r")

    def update(self):
        self.string = ""

        end_check = len(self.instances)

        for inst in self.instances:
            if inst.done == inst.max:
                end_check -= 1
                self.end = True

            self.string += inst.line

        # for manager caption
        if self.manager:
            self.string += self.caption

        line_count = self.string.count("\n")

        # to make progress bar clean (without double symbols at the end)
        clean_string = ""
        for part in self.string.split("\n")[0:-1]:
            # if part != "":
            clean_string += self.CLR + part + "\n"
            
        # write progress to stdout
        sys.stdout.write(clean_string)

        if end_check == 0:
            self.final = True
        else:
            # get up for new iteration
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
        #
        # except Exception:
        #     print("An exception occured!")

        finally:
            sys.stdout.write(SHOW)

    return wrapper


if __name__ == "__main__":
    # test

    @progress_wrapper
    def show_progress(a, b):
        manager = Progressbar(0)
        pr1 = Progressbar(id=1, total_data=a, max=100, char_max=20, chars=["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", " "])
        pr2 = Progressbar(id=2, total_data=b, chars="* ")

        form = "-> {caption}{addon}\n|{done_section}{process_section}{undone_section}| -- {done:.1f}%\n"
        form_variables = dict.fromkeys(["caption", "done_section", "process_section", "undone_section", "done"])
        form_variables["addon"] = Fore.RED + "test!" + Style.RESET_ALL

        pr1.setup(form=form, form_variables=form_variables)

        pr2.set_caption("gh:")
        pr2.add_caption(" 1, 2")

        for g in range(900):
            sleep(0.1)

            pr1.set_caption(f"Iteration: {g}")

            manager.set_caption(f"manager -> {g}")

            pr1.step(1)
            pr2.step(1)

            if not manager.final:
                manager.update()
            else:
                break

    show_progress(20, 100)
