#!/usr/bin/env python3
"""
functions for config actions
"""

import json
import os


def init_config():
    """
    return default paths
    """

    # config path for Linux
    default_config_dir = os.path.expanduser("~/.config/pinterest_dl")
    default_config_path = os.path.join(default_config_dir, "config.json")

    return default_config_dir, default_config_path


def default_config():
    """
    returns default pinterest_dl config
    """

    # other paths
    root_dir = os.path.join(os.path.expanduser("~"), "pinterest_dl")
    storage_path = os.path.join(root_dir, "pinterest-storage")
    driver_path = os.path.join(root_dir, "driver")
    cookies_path = os.path.join(driver_path, "cookies")

    # default empty config
    data = {
        # paths
        "root_dir": root_dir,
        "storage_path": storage_path,
        "driver_path": driver_path,
        "cookies_path": cookies_path,

        # proxies
        "proxies": None,

        # users
        "users": {
        },

        # list of users
        "user_list": [
        ],
    }

    return data


def write_config(config_path, config):
    """
    write specific config to specific path
    """
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)


def read_config(config_path):
    """
    read config from specific path
    """
    with open(config_path, "r") as config:
        data = json.load(config)

    return data


if __name__ == "__main__":
    config = default_config()

    config_dir, config_path = init_config()

    if not os.path.exists(config_dir):
        os.mkdir(config_dir)

    write_config(config_path, default_config())
    print(read_config(config_path))
