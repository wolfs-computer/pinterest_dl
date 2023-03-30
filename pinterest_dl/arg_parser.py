#!/usr/bin/env python3

import os
import argparse
from pinterest_dl.config_parser import read_config, write_config

# TODO: add option groups

# Here argument parser gets default values from config file


def create_parser():
    """
    create parser for pinterest-dl
    """

    # Config path:
    init_parser = argparse.ArgumentParser(add_help=False)

    default_config_path = "config.json"
    init_parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        action="store",
        default=default_config_path,
        help="specify config",
    )

    args, remaining_argv = init_parser.parse_known_args()

    # if no config given use default and write do default path
    if not os.path.exists(args.config_path):
        write_config(args.config_path)

    config = read_config(args.config_path)

    # CLI argument parser:
    parser = argparse.ArgumentParser(
        prog="pinterest-dl",
        description="utility for downloading pins from Pinterest",
        parents=[init_parser]
    )

    # CLI options:

    group_pin_opt = parser.add_argument_group("pinterest-dl options")

    # verbose
    # parser.add_argument(
    #     "-V",
    #     dest="verbose",
    #     action="store_true",
    #     default=False,
    #     help="display verbose",
    # )

    # proxy
    group_pin_opt.add_argument(
        "-p",
        "--proxies",
        dest="proxies",
        action="store",
        default=config["proxies"],
        help="specify pinterest-dl proxies comma separated",
    )

    # paths:

    # pinterest-dl storage path
    group_pin_opt.add_argument(
        "--storage",
        dest="storage_path",
        action="store",
        default=config["storage_path"],
        help="specify pinterest-dl storage path",
    )

    # driver path
    group_pin_opt.add_argument(
        "--driver_path",
        dest="driver_path",
        action="store",
        default=config["driver_path"],
        help="specify driver path",
    )

    # cookies path
    group_pin_opt.add_argument(
        "--cookies_path",
        dest="cookies_path",
        action="store",
        default=config["cookies_path"],
        help="specify cookies path (it will be stored in driver_path, need to start with /)",
    )


    # Download boards:

    group_dl = parser.add_argument_group("Download options")

    # specify user (has default user)
    default_user = None

    if len(config["user_list"]) > 0:
        default_user = config["user_list"][0]

    group_dl.add_argument(
        "-u",
        "--user",
        dest="user",
        action="store",
        default=default_user,
        help="specify user for downloading, (username/index in config)",
    )

    # add new user
    group_dl.add_argument(
        "--user-add",
        dest="user_add",
        action="store_true",
        default=False,
        help="specify user to add",
    )

    # show all users and their info
    group_dl.add_argument(
        "--user-show",
        dest="user_show",
        action="store_true",
        default=False,
        help="show info about all users",
    )

    # login to account
    group_dl.add_argument(
        "-l",
        "--login",
        dest="login",
        action="store_true",
        default=False,
        help="login to account",
    )

    # specify boards
    group_dl.add_argument(
        "-b",
        "--boards",
        dest="boards",
        action="store",
        default=None,
        help="specify boards to download, separated by <,>",
    )

    # download all boards
    group_dl.add_argument(
        "--all",
        dest="all_boards",
        action="store_true",
        default=False,
        help="download all boards on current account",
    )

    group_dl.add_argument(
        "-s",
        "--sections",
        dest="sections",
        action="store",
        default=None,
        help="specify section of the board to download, in format <board_name>:<section1>,<section2>.<board_name>:<section>",
    )

    group_dl.add_argument(
        "--list",
        dest="list_account",
        action="store_true",
        default=False,
        help="list all boards and section",
    )

    return parser
