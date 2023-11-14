#!/usr/bin/env python3
"""
functions to manipulate cookies of different accounts
"""

import json
import os


def cookie_get(cookie_path):
    """
    get cookies from cookie_path
    """

    dir = os.path.dirname(cookie_path)
    if not os.path.exists(dir):
        os.mkdir(dir)

    try:
        with open(cookie_path, "r") as file:
            content = file.read()
            cookies = json.loads(content)
            return cookies
    except Exception:
        return None


def cookie_write(cookie_path, cookies):
    """
    write cookies to cookie_path
    """

    dir = os.path.dirname(cookie_path)
    if not os.path.exists(dir):
        os.mkdir(dir)

    with open(cookie_path, "w") as file:
        file.write(json.dumps(cookies))
