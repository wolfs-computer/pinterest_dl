#!/usr/bin/env python3
"""
function for downloading video in m3u8 format
"""

import os
import requests

from functools import partial
from multiprocessing.pool import Pool
from tqdm import tqdm


def request_builder(headers=None, proxies=None, stream=False):

    return request


class M3u8_Download:
    def __init__(self, url, file_name):
        self.url = url
        self.file_name = file_name

        self.url_list = []
        self.url_name = []
        self.url_all = url.split("/")
        self.base_url = "/".join(self.url_all[:-1])

        # self.request = request_function

    # def request(self, url):
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    #     }
    #
    #     responce = requests.get(url, headers=headers)
    #
    #     return responce

    def first(self, url=None, base_url=None):
        if url is None:
            url = self.url
        if base_url is None:
            base_url = self.base_url

        # if "#" in url:
        #     print(url)
        #     url = url.split("#")[0] + url.split('"')[-2]
        #     print(url)

        # get file
        m3u8 = request(url)

        m3u8_content = m3u8.content.decode("utf-8")

        if "#EXTM3U" not in m3u8_content:
            print("bad file!")

            return None

        content = m3u8_content.split("\n")

        for line in content:
            if ".ts" in line:
                line_split = line.split("/")
                self.url_name.append(line_split[-1])
                self.url_list.append(base_url + "/" + line_split[-1])
            elif ".m3u" in line:
                self.new_m3u8(line)

    def new_m3u8(self, new_url_part):
        temporal = new_url_part.split("/")
        # original link dir (without .m3u8 end)
        new_url_list = self.url_all[:-1]

        for element in temporal:
            if element not in self.url_all[:-1]:
                new_url_list.append(element)

        new_url = "/".join(new_url_list)
        new_base_url = "/".join(new_url_list[:-1])

        self.first(new_url, new_base_url)


# ??
class Ts_Download:
    """
    class for downloading .ts parts
    """

    def __init__(self, url, name, number, file_dir_ts):
        self.url = url
        self.name = name
        self.number = number
        self.file_dir_ts = file_dir_ts
        self.file_dir = os.listdir(file_dir_ts)

        self.content = b""

        # self.request = request_function

    # def request(self, url):
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    #     }
    #
    #     responce = requests.get(url, headers=headers)
    #
    #     return responce

    def get(self, num):
        if self.name in self.file_dir:
            with open(os.path.join(self.file_dir_ts, self.name), "rb") as f:
                self.content = f.read()
        else:
            ts_res = request(self.url)
            self.content = ts_res.content

    def save(self):
        if self.name in self.file_dir:
            print(f"file {self.name} already exists!")
        else:
            if self.content:
                with open(os.path.join(self.file_dir_ts, self.name), "wb") as f:
                    f.write(self.content)
            else:
                print(f"file {self.name} doesnt exist!")


def download(url_name, f_dir="a", num_all=999):
    ts = Ts_Download(url_name[0], url_name[1], url_name[2], f_dir)
    ts.get(num_all)
    return ts


def clear_ts(dir_remove_ts):
    file_list_ts = os.listdir(dir_remove_ts)
    for f_n in file_list_ts:
        if ".ts" in f_n:
            os.remove(os.path.join(dir_remove_ts, f_n))


def save_mp4(mv_list, file_name, movie_file_dir):
    file_path = os.path.join(movie_file_dir, file_name + ".mp4")

    if len(mv_list) == []:
        print("Didnt download anything!")
        return None

    if None in mv_list:
        print("You lost some .ts file")
        mv_real = [i for i in mv_list if i]
        for ts in mv_real:
            ts.save()
        return None

    mv_list.sort(key=lambda x: x.number)

    for ts_c in mv_list:
        with open(file_path, "ab") as f:
            f.write(ts_c.content)

    clear_ts(movie_file_dir)


def download_m3u8(url, path="./", name="test", request_options={}):
    # request function
    global request

    def request(url):
        responce = requests.get(url, **request_options)
        return responce

    m3u8_url = url.strip() # url

    m3 = M3u8_Download(m3u8_url, str(name))
    m3.first()

    ts_list = [[m3.url_list[i], m3.url_name[i], i] for i in range(len(m3.url_list))]

    partial_func = partial(download, f_dir=path, num_all=len(m3.url_list))
    p = Pool(10)

    # print(p.imap(partial_func, ts_list))

    mv_list = list(tqdm(p.imap(partial_func, ts_list), total=len(m3.url_list), desc=f"downloading video pin {name}", ascii=True))

    p.close()
    p.join()

    save_mp4(mv_list, m3.file_name, path)


if __name__ == "__main__":
    links = ['https://v1.pinimg.com/videos/mc/hls/87/a4/e5/87a4e536c42fd9693a96e225e26706f0.m3u8', 'https://v.pinimg.com/videos/mc/hls/aa/f4/f3/aaf4f3fead7a6d9f0e8863dc341f87a9.m3u8', 'https://v.pinimg.com/videos/mc/hls/aa/f4/f3/aaf4f3fead7a6d9f0e8863dc341f87a9.m3u8']

    # request_opts = {}

    for index, link in enumerate(links):
        download_m3u8(link, "./", str(index))
