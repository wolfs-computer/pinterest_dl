#!/usr/bin/env python3
"""
Main pinterest_dl class declaration

"""

# Selenium
# browser core
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
# core option
from selenium.webdriver.firefox.options import Options
# UI actions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
# proxy support
from selenium.webdriver.common.proxy import Proxy, ProxyType

import requests
import os
import sys
from colorama import Back, Style, Fore

# my modules
from pinterest_dl import pinterest_cookies
from pinterest_dl import url_builder
from pinterest_dl import bookmark_manager
from pinterest_dl import m3u8_dl
from pinterest_dl import progressbar

# temporal
from pprint import pprint
from time import sleep


# main pinterest-dl class
class PinterestDL:
    """
    Pinterest_dl main class
    """

    def __init__(self, email, root_dir, storage_path, driver_dir, cookies_path, proxies):
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

        def check_dir(dir_name):
            if not os.path.exists(dir_name):
                os.mkdir(dir_name)

        # path for all downloaded files including driver/cookies/boards
        self.root_dir = root_dir
        check_dir(self.root_dir)

        # path to all downloaded boards and pins
        self.storage_path = storage_path
        check_dir(self.storage_path)

        # path to driver
        check_dir(self.driver_dir)

        # path to all downloaded boards and pins of the current user
        self.user_storage = f"{storage_path}/{self.username}"
        check_dir(self.user_storage)

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

    def login_check(self):
        """
        check if user is logged in
        """
        cookies = pinterest_cookies.cookie_get(self.cookies_path)
        if cookies is not None:
            return True
        else:
            return False

    def get_cookies(self):
        """
        return cookie file path if there is one
        """
        if self.login_check():
            return self.cookies_path
        else:
            return None

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

    def init_progressbar(self, max=20, chars=["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", " "]):
        """
        init progress bar for downloading indication
        """

        all_bars = progressbar.Progressbar.instances

        all_ids = [instance.id for instance in all_bars]

        if len(all_bars) == 0 or 1 not in all_ids:
            self.progressbar1 = progressbar.Progressbar(1, max=max, chars=chars)

    @progressbar.progress_wrapper
    def download_media(self, url, media_path, board_name, section=None, is_m3u8=False):
        """
        download media by url form board to specific path
        """
        # status here
        status = ""

        board_str = Fore.RED + "Board" + Style.RESET_ALL

        if section is None:
            status = f"Downloading {board_str}: \"{board_name}\" -> Name: \"{os.path.basename(media_path)}\""
        else:
            section_str = Fore.GREEN + "Section" + Style.RESET_ALL
            status = f"Downloading {board_str}: \"{board_name}\" {section_str}: \"{section}\" -> Name: {os.path.basename(media_path)}"

        # init progress bar here
        self.init_progressbar()

        # format of the progress bar
        progress_form = "{caption}|{done_section}{process_section}{undone_section}| {done:.1f}%\n{info}{warn}"

        progress_form_variables = dict.fromkeys(["caption", "done_section", "process_section", "undone_section", "done"])
        # special fields with warnings and information
        progress_form_variables["info"] = Fore.BLUE + "Info: " + Style.RESET_ALL + "OK" + "\n"
        progress_form_variables["warn"] = Fore.YELLOW + "Warning: " + Style.RESET_ALL + "too cool!" + "\n"

        # setup progress bar format
        self.progressbar1.setup(form=progress_form, form_variables=progress_form_variables)

        # max percentage -> 100
        # max chars in bar progress -> 30
        self.progressbar1.setup(max=100, char_max=30)

        self.progressbar1.final = False
        self.progressbar1.set_caption(status)

        if is_m3u8:

            self.progressbar1.setup(update=True)

            external_request_opts = {
                "headers": self.http.headers,
                "proxies": self.http.proxies,
            }

            m3u8_dl.download_m3u8(url, os.path.dirname(media_path), os.path.basename(media_path), external_request_opts, self.progressbar1)

        else:

            with open(media_path, "wb") as file:
                # getting file

                responce = self.request(url, stream=True)

                if responce.status_code != 200:
                    print("bad responce!")
                    return None

                file_length = responce.headers.get("content-length")

                if file_length is None:
                    file.write(responce.content)
                else:
                    self.progressbar1.setup(int(file_length), update=True)

                    for data in responce.iter_content(chunk_size=1024):
                        file.write(data)

                        if not self.progressbar1.final:
                            # sleep(0.01)
                            self.progressbar1.step(len(data))
                            self.progressbar1.update()

    def get_boards(self, username=None, page_size=250):
        """
        get all boards from account
        """

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
        return list of pins from board
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
        easier pin extracor then self.get_board_feed()
        """

        board = self.get_board_feed(board_id, page_size=page_size)
        board_parts = []

        while len(board) > 0:
            board_parts += board
            board = self.get_board_pins(board_id)

        pins = board_parts

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
        get all board section pins
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
        download all types of pins
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
            # m3u8_dl.download_m3u8(url, dir, name, external_request_opts)
            self.download_media(url, dir+name, board_name, section=section, is_m3u8=True)

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

                    step += 1
                # story videos
                elif page["blocks"][0]["block_type"] == 3:
                    url = page["blocks"][0]["video"]["video_list"]["V_EXP4"]["url"]
                    video_path = f"{pin_path}.{step}.mp4"
                    self.download_media(url, video_path, board_name, section=section)
                    step += 1

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
        """
        download only one section
        """
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
        """
        download only one board
        """
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
