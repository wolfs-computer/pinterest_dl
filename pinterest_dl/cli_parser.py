#!/usr/bin/env python3
"""
definition of pinterest-dl CLI options
"""

import os
import argparse
from pinterest_dl import config_functions


# basic:
# help (-h/--help)
# verbose (-v/--verbose)
# version (-V/--version)


def create_parser():
    """
    create parser for pinterest-dl
    """

    init_parser = argparse.ArgumentParser(add_help=False)

    # get default config paths
    config_dir, config_path = config_functions.init_config()

    if not os.path.exists(config_dir):
        # create config dir if dont exists
        os.mkdir(config_dir)

    if not os.path.exists(config_path):
        # create config file if dont exists
        config_functions.write_config(config_path, config_functions.default_config())

    # use specific config
    init_parser.add_argument(
        "-c",
        "--config",
        dest="config_path",
        action="store",
        default=config_path,
        metavar="<config path>",
        help="specify config",
    )

    args, remaining_argv = init_parser.parse_known_args()

    # if given path exists use it as config
    if config_path != args.config_path and os.path.exists(args.config_path):
        config_path = args.config_path

    # read config
    config = config_functions.read_config(config_path)

    # CLI argument parser:
    parser = argparse.ArgumentParser(
        prog="pinterest-dl",
        description="utility for downloading pins from Pinterest",
        parents=[init_parser]
    )

    # CLI options:

    group_pin_opt = parser.add_argument_group("Pinterest-dl options")

    # !! DEBUG option !!
    group_pin_opt.add_argument(
        "-i",
        "--info",
        dest="show_info",
        action="store_true",
        default=False,
        help="display values",
    )

    # proxy
    group_pin_opt.add_argument(
        "-p",
        "--proxies",
        dest="proxies",
        action="store",
        default=config["proxies"],
        metavar="<url>,<url>",
        help="specify pinterest-dl proxies comma separated",
    )

    # paths:

    # pinterest-dl storage path
    group_pin_opt.add_argument(
        "--storage",
        dest="storage_path",
        action="store",
        default=config["storage_path"],
        metavar="<storage path>",
        help="specify pinterest-dl storage path",
    )

    # driver path
    group_pin_opt.add_argument(
        "--driver",
        dest="driver_path",
        action="store",
        default=config["driver_path"],
        metavar="<driver path>",
        help="specify driver path",
    )

    # cookies path
    group_pin_opt.add_argument(
        "--cookies",
        dest="cookies_path",
        action="store",
        default=config["cookies_path"],
        metavar="<cookie path>",
        help="specify cookies path (it will be stored in driver_path, must start with /)",
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
        metavar="<user>",
        help="specify user for downloading, (username/index in config)",
    )

    # add new user
    group_dl.add_argument(
        "-a",
        "--add-user",
        dest="user_add",
        action="append",
        default=None,
        metavar="<email> <password>",
        nargs="+",
        help="specify user/s to add in config, -a <email> <password> -a <email> -a ..., use quotes if email or password contain whitespace",
    )

    # show all users and their info
    group_dl.add_argument(
        "-o",
        "--user-show",
        dest="user_show",
        action="store_true",
        default=False,
        help="show info about all users",
    )

    # login in to account with password
    group_dl.add_argument(
        "-l",
        "--login",
        dest="login",
        action="store_true",
        default=False,
        help="login to account",
    )

    # download specified boards
    group_dl.add_argument(
        "-b",
        "--boards",
        dest="boards",
        action="store",
        default=None,
        metavar="<board>,<board>",
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

    # download specified sections of boards
    group_dl.add_argument(
        "-s",
        "--sections",
        dest="sections",
        action="store",
        default=None,
        metavar="<board_name>:<section1>,<section2>.<board_name>:<section>",
        help="specify section of the board to download",
    )

    # list all account boards and sections
    group_dl.add_argument(
        "--list",
        dest="list_account",
        action="store_true",
        default=False,
        help="list all boards and sections",
    )

    return parser
