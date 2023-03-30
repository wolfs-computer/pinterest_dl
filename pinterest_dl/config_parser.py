#!/usr/bin/env python3

import json


default_config_path = "config.json"


def write_config(config_path):
    # default empty config
    data = {
        # paths
        "storage_path": "materials/pinterest-storage",
        "driver_path": "materials/driver",
        "cookies_path": "materials/driver/cookies",

        # proxies
        "proxies": None,

        # users
        "users": {
        },

        # list of users
        "user_list": [
        ],
    }

    # write config
    with open(config_path, "w") as config:
        json.dump(data, config, indent=4)


def update_config(config_path, new_version):
    # write config
    with open(config_path, "w") as config:
        json.dump(new_version, config, indent=4)


def read_config(config_path):
    with open(config_path, "r") as config:
        data = json.load(config)

    return data


if __name__ == "__main__":
    write_config(default_config_path)
    print(read_config(default_config_path))
