#!/usr/bin/env python3
"""
functions for CLI
"""

import os
import sys
from pinterest_dl.PinterestDL import PinterestDL
from pinterest_dl import config_parser
from colorama import Style, Fore


# PRE args

def get_proxies(args):
    """
    use proxy
    """

    if args.proxies is not None:
        proxies = args.proxies.split(",")
        if len(proxies) > 1:
            proxies = {"https": proxies[0], "http": proxies[1]}
        else:
            proxies = {"https": proxies[0], "http": proxies[0]}

        return proxies
    else:
        return None


def user_add(config, args):
    """
    add new user/s
    """

    for user in args.user_add:

        email = user[0]
        password = None
        if len(user) > 1:
            password = user[1]

        user = email.split("@")[0]

        if email != "" and "@" in email:

            if user in config["users"]:
                print(f"User \"{user}\" already exists")
                continue

            # write username to list of users
            config["user_list"].append(user)
            # create data filed
            config["users"].update({user: {"email": email, "password": None, "is_logged_in": False, "cookie_file": None}})

            print("Added user:", user)

            # if password exists create profile and write password to it
            if password != "":
                config["users"][user].update({"password": password})
                print("Added password for:", user)
            else:
                print("No password for:", user)

            # if there is cookie file for this account (in case of profile deletion)
            possible_cookie_file = config["cookies_path"] + "/" + user
            if os.path.exists(possible_cookie_file):
                config["users"][user]["cookie_file"] = possible_cookie_file
                config["users"][user]["is_logged_in"] = True
                print("Found login data for:", user)

            # update config
            config_parser.write_config(args.config_path, config)
        else:
            print(f"Invalid email: \"{user}\"")


# MAIN args

def get_email(config, user):
    """
    get email
    """
    if config["users"].get(user, None) is not None:
        email = config["users"][user]["email"]
    else:
        email = None

        if user is None:
            print("No set user!")
            sys.exit(1)
        else:
            print("No such user in config!")

    return email


def get_user_index(config, user):
    """
    in case user means index of user in config
    """

    user = int(user)

    try:
        user = config["user_list"][user - 1]

        return user
    except IndexError:
        print("No user with such index!")
        sys.exit(1)


def login(args, config, user, account, password):
    """
    login in account
    """

    login = True

    if password is None:
        print("No password for user!")
        try:
            password = input("Set password: ")

            # update config
            if password != "":
                config["users"][user]["password"] = password
                config_parser.write_config(args.config_path, config)

                login = True
            else:
                print("\nEmpty password!")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nEmpty password!")
            sys.exit(1)

    # if already logged in (by config)
    if config["users"][user]["is_logged_in"]:
        inp = input("You are already logged in (by config), do you realy want to login? [Y/n] ")
        login = False

        if inp == "" or inp == "Y":
            login = True

    if login:
        print("login...")
        account.login(password=password)

        # check if logged by cookie files
        if account.login_check():
            print("Logged in seccessfully")

            # update config
            config["users"][user]["is_logged_in"] = True
            config["users"][user]["cookie_file"] = account.get_cookies()
            config_parser.write_config(args.config_path, config)
        else:
            print("Login failed")


def get_boards(args, account):
    """
    get board/s
    """

    # get requested boards names
    requested_boards = args.boards.split(",")

    # get all boards names from account
    print("geting boards...")
    boards_json = account.get_boards()

    boards = {}

    for board in boards_json:
        boards.update({board["name"]: {"name": board["name"], "id": board["id"]}})

    # check if requested boards exist
    boards_install = {}

    for board in requested_boards:
        if board in boards.keys():
            boards_install.update({board: boards[board]})
        else:
            print("No board:", board)

    # download requested boards
    print("Downloading boards:", " ".join(boards_install.keys()))
    print("start downloading...")

    for board in boards_install:
        account.download_board(boards_install[board])


def get_all_boards(account):
    """
    get all boards
    """

    # get all boards names from account
    print("geting boards...")
    boards_json = account.get_boards()

    boards = {}

    for board in boards_json:
        boards.update({board["name"]: {"name": board["name"], "id": board["id"]}})

    print("start downloading all boards...")

    for board in boards:
        account.download_board(boards[board])


def get_sections(args, account):
    """
    get section/s
    """
    # in format <board_name>:<section1>,<section2>.<board_name>:<section>

    sections = {}
    line = args.sections

    # boards
    boards = line.split(".")
    # sections
    for board in boards:
        board_name = board.split(":")[0]
        board_sections = board.split(":")[1].split(",")
        sections.update({board_name: board_sections})

    # get requested boards names
    requested_boards = sections.keys()

    # get all boards names from account
    print("geting boards...")
    boards_json = account.get_boards()

    boards = {}

    for board in boards_json:
        boards.update({board["name"]: {"name": board["name"], "id": board["id"]}})

    # check if requested boards exist
    boards_install = {}

    for board in requested_boards:
        if board in boards.keys():
            boards_install.update({board: boards[board]})
        else:
            print("No board:", board)

    # download requested boards
    print("Downloading sectons of boards:", " ".join(boards_install.keys()), )
    print("start downloading...")

    for board in boards_install:
        board_id = boards_install[board]["id"]
        # get sections
        board_sections = account.get_board_sections(board_id)

        # cheack if sections exist
        no_sections = []
        board_section_names = [section["title"] for section in board_sections]

        for section in sections[board]:
            # print(sections[board])
            if section not in board_section_names:
                sections[board].remove(section)
                no_sections.append(section)

        if len(no_sections) > 0:
            print("no such sections:", " ".join(no_sections))

        # download sections
        for section in board_sections:
            section_name = section["title"]

            if section_name in sections[board]:
                account.download_section(board, section)


def list_account(user, account):
    """
    list account in tree shape
    """

    content = {}

    print("geting boards...")

    boards = {}
    boards_json = account.get_boards()

    for board in boards_json:
        boards.update({board["name"]: {"name": board["name"], "id": board["id"], "pin_count": board["pin_count"]}})

    print("getting sections...")

    for board in boards:

        board_id = boards[board]["id"]
        total_board_pin_count = boards[board]["pin_count"]
        total_section_pin_count = 0

        content.update({board: {"id": board_id, "sections": {}, "total_pin_number": total_board_pin_count, "sections_pin_count": 0, "board_pin_count": 0}})

        board_sections = account.get_board_sections(board_id)

        for section in board_sections:
            section_name = section["title"]
            secton_pin_count = section["pin_count"]
            content[board]["sections"].update({section_name: secton_pin_count})

            total_section_pin_count += secton_pin_count

        content[board]["sections_pin_count"] = total_section_pin_count
        content[board]["board_pin_count"] = total_board_pin_count - total_section_pin_count

    # format results

    if account.login_check():
        login_state = Fore.GREEN + "Logged in" + Style.RESET_ALL
    else:
        login_state = Fore.RED + "Not logged in!" + Style.RESET_ALL

    print(f"\n{user} ({login_state})")

    if len(content) == 0:
        print("│")
        print("└ No boards on account")

    for index, board in enumerate(content):
        id = content[board]["id"]
        total_pin_number = content[board]["total_pin_number"]
        board_pin_count = content[board]["board_pin_count"]
        sections_pin_count = content[board]["sections_pin_count"]

        sections = content[board]["sections"]

        pipe1 = "│"
        pipe2 = "├"
        if index + 1 == len(content):
            pipe1 = " "
            pipe2 = "└"

        # format board
        print(f"{pipe2}── {board}: {total_pin_number}")
        if len(sections) > 0:
            print(f"{pipe1}    ├── id -> {id}")
            print(f"{pipe1}    ├── only board pin number -> {board_pin_count}")
            print(f"{pipe1}    ├── total sections pin number -> {sections_pin_count}")
            print(f"{pipe1}    └── sections: {len(sections)}")
        else:
            print(f"{pipe1}    └── id -> {id}")


        # format board sections
        for index, section in enumerate(sections):
            section_name = section
            section_pin_count = sections[section]

            nest_pipe = "├"
            if index + 1 == len(sections):
                nest_pipe = "└"

            print(f"{pipe1}        {nest_pipe}── {section_name}: {section_pin_count}")

        if index + 1 != len(content):
            print(pipe1)


def user_show(config):
    """
    show all info about user from config
    """

    for index, name in enumerate(config["users"].keys()):
        number = index + 1

        if index == 0:
            number = "Default"

        # hide password
        password = config["users"][name]["password"]
        hidden_password = "".join(["*" for letter in password])

        print(f'Email: {config["users"][name]["email"]} ({number})')
        print("Password:", hidden_password)
        print("Login status:", config["users"][name]["is_logged_in"])
        print("Cookie file:", config["users"][name]["cookie_file"])

        if index + 1 != len(config["users"].keys()):
            print("\n")


def arg_execute(args, config):
    """
    main function that executes function depending on args
    """

    # PRE

    # !! DEBUG option !!
    if args.info:
        from pprint import pprint
        pprint(args)
        print(args.user_add)

        sys.exit(1)

    if args.user_add:
        user_add(config, args)
        sys.exit(1)


    # MAIN

    user = args.user

    if user.isdigit():
        # if user was specified by index
        user = get_user_index(config, user)


    email = get_email(config, user)

    if user[:1] == "@":
        # to indicate foreign account
        password = 1
        user = user[1:]
    else:
        password = config["users"][user]["password"]

    root_dir = config["root_dir"]
    storage_path = args.storage_path
    driver_path = args.driver_path
    cookies_path = args.cookies_path
    proxies = get_proxies(args)

    account = PinterestDL(user, root_dir, storage_path, driver_path, cookies_path, proxies, email)


    if args.login:
        if password is not None:
            login(args, config, user, account, password)
        else:
            print("No password for user!")


    # update config with login state
    config_parser.update_config(args.config_path, config)


    # after login args:

    # show info about all users
    if args.user_show:
        user_show(config)
        sys.exit(1)

    # check for login
    if type(password) == "str" and not config["users"][user]["is_logged_in"]:
        print(f"You are {Fore.RED}not logged in!{Style.RESET_ALL} Some boards will not be displayed/used!\n")

    # list account
    if args.list_account:
        list_account(user, account)

    # get section
    if args.sections is not None:
        get_sections(args, account)

    # get boards
    if args.boards is not None:
        get_boards(args, account)

    # get all boards
    if args.all_boards:
        get_all_boards(account)
