#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from selenium.webdriver.firefox.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

from selenium.webdriver.common.proxy import Proxy, ProxyType

import requests
import os
import sys
from colorama import Fore, Back, Style

from pinterest_dl import pinterest_cookies
from pinterest_dl import url_builder
from pinterest_dl import bookmark_manager
from pinterest_dl import m3u8_dl
from pinterest_dl import config_parser
from pinterest_dl import arg_parser

# only for tests
from pprint import pprint


# CLI parser
parser = arg_parser.create_parser()

# if no options were given
# display help and exit
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()


# Config

# if default config doesnt exists -> write it
default_config_path = config_parser.default_config_path

if not os.path.exists(default_config_path):
    config_parser.write_config(default_config_path)

config = config_parser.read_config(default_config_path)


# main pinterest-dl class
class PinterestDL:
    def __init__(self, email, driver_dir=config["driver_path"], cookies_path=config["cookies_path"], proxies=config["proxies"], storage_path=config["storage_path"]):
        self.email = email
        self.username = email.split("@")[0]

        # options
        self.driver_dir = driver_dir
        self.cookies_path = f"{cookies_path}/{self.username}"
        # proxies
        if proxies is not None:
            proxies = proxies.split(",")
            if len(proxies) > 1:
                self.proxies = {"http": proxies[1], "https": proxies[0]}
            else:
                self.proxies = {"https": proxies[0]}
        else:
            self.proxies = None

        # manager for bookmarks on webpages
        # (bookmarks needed to get parts of big page with content)
        self.bookmark_manager = bookmark_manager.BookmarkManager()

        # path to all downloaded boards and pins
        self.storage_path = storage_path
        if not os.path.exists(self.storage_path):
            os.mkdir(self.storage_path)

        # path to all downloaded boards and pins of the current user
        self.user_storage = f"{storage_path}/{self.username}"
        if not os.path.exists(self.user_storage):
            os.mkdir(self.user_storage)

        # setup request profile
        self.request_setup()

    def selenium_setup(self, headless=True, proxy=None):
        """
        selenium setup
        """

        # set driver options
        driver_options = Options()

        # show browser or not
        if headless:
            driver_options.add_argument("--headless")

        # proxy setup
        if proxy is not None:
            http_proxy = Proxy()
            http_proxy.proxy_type = ProxyType.MANUAL
            http_proxy.http_proxy = proxy
            http_proxy.socks_proxy = proxy
            http_proxy.ssl_proxy = proxy
            http_proxy.add_to_capabilities(webdriver.DesiredCapabilities.FIREFOX)

        # download driver or use downloaded

        if not os.path.exists(self.driver_dir):
            os.mkdir(self.driver_dir)

        tree = os.walk(self.driver_dir)
        driver_exec_name = "geckodriver"
        driver_exec = None

        for curent_dir, dirs, files in tree:
            if driver_exec_name in files:
                driver_exec = os.path.join(curent_dir, files[files.index(driver_exec_name)])

        if driver_exec is None:
            gecko = GeckoDriverManager(path=self.driver_dir)
            driver_exec = gecko.install()
            print("install driver")

        print("Driver:", driver_exec)

        # start driver
        service = Service(executable_path=driver_exec, log_path=os.devnull)
        self.driver = webdriver.Firefox(service=service, options=driver_options)
        # service_log_path -> where to write log

    def login(self, password, wait_time=9):
        """
        login to pinterest
        """

        # setup selenium
        self.selenium_setup(headless=True)

        # make a request with driver to pinterest login page
        self.driver.get("https://pinterest.com/login")

        # wait until login field dhow up
        WebDriverWait(self.driver, wait_time).until(
            expected_conditions.element_to_be_clickable((By.ID, "email"))
        )

        # start sending keys to login field
        self.driver.find_element(By.ID, "email").send_keys(self.email)
        self.driver.find_element(By.ID, "password").send_keys(password)

        # login button
        logins = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Log in')]")

        for login in logins:
            login.click()

        WebDriverWait(self.driver, wait_time).until(
            expected_conditions.invisibility_of_element((By.ID, "email"))
        )

        # get cookies from driver session
        driver_cookies = self.driver.get_cookies()

        pinterest_cookies.cookie_write(self.cookies_path, driver_cookies)

        print("Successfully logged in with account " + self.email)

        self.driver.close()

        # write cookie path to config
        config["users"][self.username]["cookie_file"] = self.cookies_path
        config["users"][self.username]["is_loged_in"] = True
        config_parser.update_config(args.config_path, config)

    def login_check(self):
        cookies = pinterest_cookies.cookie_get(self.cookies_path)
        if cookies is not None:
            return True
        else:
            return False

    def request_setup(self):
        """
        setup request
        """

        # start requests session
        self.http = requests.session()

        # use proxy (if there is)
        if self.proxies is not None:
            self.http.proxies = self.proxies

        # self.http.proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
        # self.http.proxies = {'https': 'socks5://127.0.0.1:9050'}
        # TOR example -> session.proxies = {'http':  'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}

        # set headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
        }
        self.http.headers = headers

        # use login cookies for requests
        selenium_cokies = pinterest_cookies.cookie_get(self.cookies_path)

        # delete old requests session cookies
        self.http.cookies.clear()

        # set new ones
        if selenium_cokies is not None:
            for cookie in selenium_cokies:
                self.http.cookies.set(cookie["name"], cookie["value"])

    def request(self, url, stream=False):
        """
        make a request
        """

        # request url
        response = self.http.get(url, stream=stream)

        # check IP
        # check = self.http.get("https://checkip.perfect-privacy.com/csv").text
        # print(check)

        return response

    def draw_progress(self, max, total_data, data):
        """
        draw progress when downloading
        """

        max = 20
        downloaded = 0

        def draw(data):
            nonlocal downloaded
            downloaded += len(data)
            done = int(downloaded * max / total_data)

            sys.stdout.write(f'\r|{"█" * done}{" " * (max - done)}| -- {done}/{max}')
            sys.stdout.flush()

            if downloaded == total_data:
                sys.stdout.write("\n")

        return draw

    def download_media(self, url, media_path, board_name, section=None):
        with open(media_path, "wb") as file:
            board_str = Back.RED + "Board" + Style.RESET_ALL

            if section is None:
                print(f"Downloading {board_str}: {board_name} -> Name: {os.path.basename(media_path)}")
            else:
                section_str = Back.GREEN + "Section" + Style.RESET_ALL
                print(f"Downloading {board_str}: {board_name} {section_str}: {section} -> Name: {os.path.basename(media_path)}")

            responce = self.request(url, stream=True)

            if responce.status_code != 200:
                print("bad responce!")
                return None

            file_length = responce.headers.get("content-length")

            if file_length is None:
                file.write(responce.content)
            else:
                show_progress = self.draw_progress(10, int(file_length), 0)

                for data in responce.iter_content(chunk_size=1024):
                    file.write(data)
                    show_progress(data)

    # def get_pins(self, username=None, page_size=250):
    #     # if no username given it is user profile
    #     # if there is name -> not your account
    #     if username is None:
    #         username = self.username
    #         own_profile = True
    #     else:
    #         own_profile = False
    #
    #     next_bookmark = 0
    #
    #     options = {
    #         "username": username,
    #         "is_own_profile_pins": own_profile,
    #         "field_set_key": "grid_item",
    #         "pin_filter": None,
    #         "bookmarks": [next_bookmark],
    #         "page_size": page_size,
    #     }
    #
    #     pin_url = "https://www.pinterest.com/resource/UserPinsResource/get/"
    #
    #     url = url_builder.build_url(pin_url, options)
    #
    #     response = self.request(url).json()
    #
    #     # bookmark = response["resource"]["options"]["bookmarks"][0]
    #
    #     return response["resource_response"]["data"]

    def get_boards(self, username=None, page_size=250):

        if username is None:
            username = self.username

        # bookmark
        next_bookmark = self.bookmark_manager.get_bookmark(key="boards", secondary_key=username)

        options = {
            "page_size": page_size,
            "privacy_filter": "all",
            "sort": "custom",
            "username": username,
            "isPrefetch": False,
            "include_archived": True,
            "field_set_key": "profile_grid_item",
            "group_by": "visibility",
            "redux_normalize_feed": True,
            "bookmarks": [next_bookmark],
        }

        source_url = f"/{username}/boards/"
        url = "https://www.pinterest.com/_ngjs/resource/BoardsResource/get/"
        url = url_builder.build_url(url, options, source_url=source_url)

        response = self.request(url).json()

        bookmark = response["resource"]["options"]["bookmarks"][0]

        self.bookmark_manager.add_bookmark(key="boards", secondary_key=username, bookmark=bookmark)

        return response["resource_response"]["data"]

    def get_board_feed(self, board_id="", page_size=250):
        """
        return list of pins
        """

        next_bookmark = self.bookmark_manager.get_bookmark(key="board_feed", secondary_key=board_id)

        if next_bookmark == "-end-":
            return []

        options = {
            "isPrefetch": False,
            "board_id": board_id,
            "field_set_key": "partner_react_grid_pin",
            "filter_section_pins": True,
            "layout": "default",
            "page_size": page_size,
            "redux_normalize_feed": True,
            "bookmarks": [next_bookmark],
        }

        url = "https://www.pinterest.com/resource/BoardFeedResource/get/"
        url = url_builder.build_url(url, options)

        response = self.request(url).json()

        bookmark = response["resource"]["options"]["bookmarks"][0]
        self.bookmark_manager.add_bookmark(key="board_feed", secondary_key=board_id, bookmark=bookmark)

        return response["resource_response"]["data"]

    def get_board_pins(self, board_id, page_size=250):
        """
        easier pin extracor
        """

        board = self.get_board_feed(board_id, page_size=page_size)
        board_parts = []

        while len(board) > 0:
            board_parts += board
            board = self.get_board_pins(board_id)

        pins = board_parts

        # delete thing with recommendation
        # pins.pop(-1)

        return pins

    def get_board_sections(self, board_id, page_size=250):
        """
        get all board sections
        """

        next_bookmark = self.bookmark_manager.get_bookmark(key="board_sections", secondary_key=board_id)

        if next_bookmark == "-end-":
            return []

        options = {
            "isPrefetch": False,
            "board_id": board_id,
            "redux_normalize_feed": True,
            "bookmarks": [next_bookmark],
        }

        url = "https://www.pinterest.com/resource/BoardSectionsResource/get/"
        url = url_builder.build_url(url, options)

        response = self.request(url).json()

        bookmark = response["resource"]["options"]["bookmarks"][0]
        self.bookmark_manager.add_bookmark(key="board_sections", secondary_key=board_id, bookmark=bookmark)

        return response["resource_response"]["data"]

    def get_board_sections_pins(self, section_id, page_size=250):
        """
        get all board sections pins
        """

        next_bookmark = self.bookmark_manager.get_bookmark(key="board_sections_pins", secondary_key=section_id)

        if next_bookmark == "-end-":
            return []

        options = {
            "isPrefetch": False,
            "field_set_key": "react_grid_pin",
            "is_own_profile_pins": True,
            "page_size": page_size,
            "redux_normalize_feed": True,
            "section_id": section_id,
            "bookmarks": [next_bookmark],
        }

        url = "https://www.pinterest.com/resource/BoardSectionPinsResource/get/"
        url = url_builder.build_url(url, options)

        response = self.request(url).json()

        bookmark = response["resource"]["options"]["bookmarks"][0]
        self.bookmark_manager.add_bookmark(key="board_sections_pins", secondary_key=section_id, bookmark=bookmark)

        return response["resource_response"]["data"]

    def download_pin(self, pin, pin_path, board_name, section=None):
        """
        download all types of pins except one
        """

        name = os.path.basename(pin_path)
        dir = pin_path.split(name)[0]
        # options for external request function
        external_request_opts = {
            "headers": self.http.headers,
            "proxies": self.http.proxies,
        }

        # recomendations at the end of the board
        if pin["type"] == "story":
            if pin["story_type"] == "board_ideas_preview_detailed":
                return

        # video
        if pin["videos"] is not None:
            url = pin["videos"]["video_list"]["V_HLSV3_WEB"]["url"]
            m3u8_dl.download_m3u8(url, dir, name, external_request_opts)
            # pprint(pin)
            # print(url)

        # story
        elif pin["story_pin_data"] is not None:
            step = 0

            for page in pin["story_pin_data"]["pages"]:
                # story images
                if page["blocks"][0]["block_type"] == 2:
                    sig = page["blocks"][0]["image_signature"]
                    url = "https://i.pinimg.com/750x"
                    for index, prefix in enumerate(sig):
                        if index > 5:
                            break

                        if index % 2 == 0:
                            url += "/"

                        url += prefix

                    url += "/" + sig + ".jpg"

                    image_path = f"{pin_path}.{step}.jpg"

                    self.download_media(url, image_path, board_name, section=section)
                    # print(pin_path)

                    step += 1
                # story videos
                elif page["blocks"][0]["block_type"] == 3:
                    url = page["blocks"][0]["video"]["video_list"]["V_EXP4"]["url"]
                    video_path = f"{pin_path}.{step}.mp4"
                    # pprint(page["blocks"][0]["video"]["video_list"])
                    # m3u8_dl.download_m3u8(url, dir, f"{name}.{step}")
                    self.download_media(url, video_path, board_name, section=section)
                    step += 1
                else:
                    print("-> error?")

        # carousel (only images)
        elif pin["carousel_data"] is not None:
            slots = pin["carousel_data"]["carousel_slots"]
            step = 0

            for slot in slots:
                record_height = 0
                biggest_image = None

                for key in list(slot["images"].keys()):
                    image = slot["images"][key]
                    if int(slot["images"][key]["height"]) > record_height:
                        record_height = image["height"]
                        biggest_image = image["url"]

                self.download_media(biggest_image, f"{pin_path}.{step}", board_name, section=section)
                step += 1

        # image
        else:
            image_url = pin["images"]["orig"]["url"]

            self.download_media(image_url, pin_path, board_name, section=section)

    # download section
    def download_section(self, board_name, section):
        section_name = section["title"]
        section_id = section["id"]

        board_path = self.user_storage + f"/{board_name}/"

        section_path = board_path + section_name + "/"

        if not os.path.exists(section_path):
            os.mkdir(section_path)

        pins = self.get_board_sections_pins(section_id)

        for index, pin in enumerate(pins):
            pin_path = section_path + str(index + 1)

            self.download_pin(pin, pin_path, board_name=board_name, section=section_name)

    # download board
    def download_board(self, board):
        board_id = board["id"]
        board_name = board["name"]
        board_path = self.user_storage + f"/{board_name}/"

        # create board dir in pinterest-dl storage path
        if not os.path.exists(board_path):
            os.mkdir(board_path)

        # if there is a sections in the board
        sections = self.get_board_sections(board_id)

        if len(sections) != 0:
            for section in sections:
                self.download_section(board_name, section)

        # just pins on the board (not in sections)
        pins = self.get_board_pins(board_id)

        for index, pin in enumerate(pins):
            pin_path = board_path + str(index + 1)

            self.download_pin(pin, pin_path, board_name=board_name)


def main(args):
    # get config
    config = config_parser.read_config(args.config_path)

    # account

    # to add new user
    if args.user_add:
        # !!!! rewrite!
        print("Add new user/s:")

        try:
            while True:
                email = input("Email: ")
                user = email.split("@")[0]
                password = input("Password (optional): ")

                if email != "" and "@" in email:
                    # write username to list of users
                    config["user_list"].append(user)
                    # create data filed
                    config["users"].update({user: {"email": email, "is_loged_in": False}})

                    # if password exists create profile and write password to it
                    if password != "":
                        config["users"][user].update({"password": password})

                    # if there is cookie file for this account (in case of profile deletion)
                    possible_cookie_file = config["cookies_path"] + "/" + user
                    if os.path.exists(possible_cookie_file):
                        config["users"][user]["cookie_file"] = possible_cookie_file
                        config["users"][user]["is_loged_in"] = True

                    # update config
                    config_parser.update_config(args.config_path, config)

        except KeyboardInterrupt:
            print("\nStop adding users...")
            return

    # user
    user = args.user

    # if user == number
    if user is not None and user.isdigit():
        user = int(user)

        try:
            user = config["user_list"][user - 1]
        except IndexError:
            print("No user with such index!")
            return

    # email
    if config["users"].get(user, None) is not None:
        email = config["users"][user]["email"]
    else:
        email = None

        if user is None:
            print("No set user!")
        else:
            print("No such user!")

        return

    if user is not None:
        account = PinterestDL(email)
    else:
        # if no user in config or arguments
        print("Specify the user!")
        return

    # show info about all users
    if args.user_show:
        for index, name in enumerate(config["users"].keys()):
            number = index + 1

            if index == 0:
                number = "Default"

            print(f'Email: {config["users"][name]["email"]} ({number})')
            print("Password:", config["users"][name]["password"])
            print("Login status:", config["users"][name]["is_loged_in"])
            print("Cookie file:", config["users"][name]["cookie_file"])
            print("\n")

    # show account
    if args.list_account:
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

            content[board]["sectons_pin_count"] = total_section_pin_count
            content[board]["board_pin_count"] = total_board_pin_count - total_section_pin_count

        # format results

        print("\n" + user)

        if len(content) == 0:
            print("│")
            print("└ No boards on account")

        for index, board in enumerate(content):
            name = board
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
            print(f"{pipe1}    ├── id -> {id}")
            print(f"{pipe1}    ├── only board pin number -> {board_pin_count}")
            if len(sections) > 0:
                # if no sections
                print(f"{pipe1}    ├── total sections pin number -> {sections_pin_count}")
            print(f"{pipe1}    └── sections: {len(sections)}")

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

    # login in account
    if args.login:
        login = True
        password = config["users"][user]["password"]

        if password is None:
            print("No password for user!")
            login = False

        # if already loged in (by config)
        if config["users"][user]["is_loged_in"]:
            inp = input("You are already loged in (by config), do you realy want to login? [Y/n] ")
            login = False

            if inp == "" or inp == "Y":
                login = True

        if login:
            print("login...")
            account.login(password=password)

            # check if logged by cookie files
            if account.login_check():
                print("Logged in seccessfully")
            else:
                print("Login failed")

    # check for login anyway
    if not config["users"][user]["is_loged_in"]:
        print("You are not logged in! Some boards will not be downloaded!")

    # get section
    # in format <board_name>:<section1>,<section2>.<board_name>:<section>

    if args.sections is not None:
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
        print("Downloading sectons of boards:", " ".join(boards_install.keys()))
        print("start downloading...")

        for board in boards_install:
            board_id = boards_install[board]["id"]
            # get sections
            board_sections = account.get_board_sections(board_id)
            for section in board_sections:
                section_name = section["title"]

                if section_name in sections[board]:
                    account.download_section(board, section)

    # get boards
    if args.boards is not None:
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

    if args.all_boards:
        # get all boards names from account
        print("geting boards...")
        boards_json = account.get_boards()

        boards = {}

        for board in boards_json:
            boards.update({board["name"]: {"name": board["name"], "id": board["id"]}})

        print("start downloading all boards...")

        for board in boards:
            account.download_board(boards[board])


if __name__ == "__main__":
    main(args)
    exit()
