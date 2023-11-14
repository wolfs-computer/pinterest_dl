#!/usr/bin/env python3
"""
functions for downloading video in m3u8 format
"""

import os
import requests

from functools import partial
from multiprocessing.pool import Pool
# from tqdm import tqdm
from moviepy.editor import VideoFileClip, AudioFileClip
from proglog import ProgressBarLogger

from pinterest_dl.progressbar import Progressbar
from pinterest_dl import custom_errors

# DEBUG
from time import sleep


global request_options
request_options = {}


class M3u8_Download:
    """
    main class for downloading .m3u8 files
    """

    def __init__(self, url, file_name):
        self.url = url
        self.file_name = file_name

        self.url_list = []
        self.url_name = []
        self.url_all = url.split("/")
        self.base_url = "/".join(self.url_all[:-1])

        self.is_new_type = False
        self.new_type_urls = {"video": [], "audio": ""}

    def request(self, url):
        responce = requests.get(url, **request_options)

        return responce

    def first(self, url=None, base_url=None):
        if url is None:
            url = self.url
        if base_url is None:
            base_url = self.base_url

        # get file
        m3u8 = self.request(url)

        if "URI=" in url:
            first_half = url.split("/")
            second_half = first_half[-1]
            del first_half[-1]

            second_half = second_half.split("\"")[-2]

            repaired_url = "/".join(first_half) + "/" + second_half

            m3u8 = self.request(repaired_url)


        m3u8_content = m3u8.content.decode("utf-8")

        if "#EXTM3U" not in m3u8_content:
            print("bad file!")
            return

        content = m3u8_content.split("\n")

        for line in content:
            if ".ts" in line:
                line_split = line.split("/")
                self.url_name.append(line_split[-1])
                self.url_list.append(base_url + "/" + line_split[-1])

            elif ".cmfv" in line and "#" not in line:
                self.is_new_type = True
                line_split = line.split("/")
                self.new_type_urls["video"].append(base_url + "/" + line_split[-1])
                return

            elif ".cmfa" in line and "#" not in line:
                self.is_new_type = True
                line_split = line.split("/")
                self.new_type_urls["audio"] = base_url + "/" + line_split[-1]
                return

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

    def request(self, url):
        responce = requests.get(url, **request_options)

        return responce

    def get(self, num):
        if self.name in self.file_dir:
            with open(os.path.join(self.file_dir_ts, self.name), "rb") as f:
                self.content = f.read()
        else:
            ts_res = self.request(self.url)
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
        if ts_c == mv_list[0]:
            with open(file_path, "wb") as f:
                f.write(ts_c.content)
        else:
            with open(file_path, "ab") as f:
                f.write(ts_c.content)

    clear_ts(movie_file_dir)


def download_m3u8(url, path="./", name="test", request_opt={}, progressbar=Progressbar()):
    # global request options
    request_options = request_opt

    m3u8_url = url.strip() # url

    m3 = M3u8_Download(m3u8_url, str(name))
    m3.first()

    if m3.is_new_type:
        # audio and video urls
        video_url = sorted(m3.new_type_urls["video"])[-1]
        audio_url = m3.new_type_urls["audio"]

        video_path = path + "/" + name + "_video.mp4"
        audio_path = path + "/" + name + "_audio.mp4"

        # download video
        with open(video_path, "wb") as video_file, open(audio_path, "wb") as audio_file:
            video_responce = requests.get(video_url, stream=True, **request_options)
            audio_responce = requests.get(audio_url, stream=True, **request_options)

            if video_responce.status_code != 200 or audio_responce.status_code != 200:
                print("bad responce!")
                return None

            video_length = int(video_responce.headers.get("content-length"))
            audio_length = int(audio_responce.headers.get("content-length"))
            # total_length = int(video_length) + int(audio_length)

            if video_length is None:
                video_file.write(video_responce.content)
            else:
                # set total amount of data to download
                progressbar.setup(total_data=video_length)
                # display info about downloading video
                progressbar.update_format_var("info", "Downloading video for pin", use_prefix=True)

                # download file by pieces
                for data in video_responce.iter_content(chunk_size=1024):
                    video_file.write(data)

                    progressbar.step(len(data))

                    # update progress bar
                    if not progressbar.final:
                        progressbar.update()

            if audio_length is None:
                audio_file.write(audio_responce.content)
            else:
                # set total amount of data to download
                progressbar.setup(update=True, total_data=audio_length)
                # display info about downloading audio
                progressbar.update_format_var("info", "Downloading audio for pin", use_prefix=True)

                # download file by pieces
                for data in audio_responce.iter_content(chunk_size=1024):
                    audio_file.write(data)

                    progressbar.step(len(data))

                    # update progress bar
                    if not progressbar.final:
                        progressbar.update()

        # logger for rendering progress
        class MyBarLogger(ProgressBarLogger):

            def callback(self, **changes):
                # Every time the logger message is updated, this function is called with
                # the `changes` dictionary of the form `parameter: new value`.
                for (parameter, value) in changes.items():
                    # print('Parameter %s is now %s' % (parameter, value))
                    pass

            def bars_callback(self, bar, attr, value, old_value=None):
                if bar != "t":
                    return

                # Every time the logger progress is updated, this function is called
                total = self.bars[bar]['total']
                # percentage = (value / total) * 100

                # set total data
                if progressbar.total_data != total:
                    progressbar.setup(update=True, total_data=total)

                # dt = bar, attr, value, percentage, total
                # progressbar.update_format_var("warn", f"{value}/{total} - {progressbar.bank}")
                # progressbar.update_format_var("err", f"{dt}")

                progressbar.step(1)

                if not progressbar.final:
                    progressbar.update()

        logger = MyBarLogger()

        # concatenate video and audio
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # display info about downloading audio
        progressbar.update_format_var("info", "Rendering pin video", use_prefix=True)

        final_clip = video_clip.set_audio(audio_clip)
        temp_audiofile = path + "/" + name + "_temp.mp3"
        final_clip.write_videofile(path + "/" + name + ".mp4", temp_audiofile=temp_audiofile, verbose=False, logger=logger)

        # clean-up
        os.remove(audio_path)
        os.remove(video_path)

    else:
        ts_list = [[m3.url_list[i], m3.url_name[i], i] for i in range(len(m3.url_list))]

        partial_func = partial(download, f_dir=path, num_all=len(m3.url_list))
        p = Pool(10)

        # r = tqdm(p.imap(partial_func, ts_list), total=len(m3.url_list), desc=f"downloading video pin {name}", ascii=True)
        # mv_list = list(r)

        mv_list = []

        total = len(m3.url_list)
        pre = p.imap(partial_func, ts_list)

        if progressbar.id == 0:
            progressbar.setup(total)
            progressbar.set_caption("downloading video")
        else:
            progressbar.setup(total_data=total)
            progressbar.update_format_var("info", "Downloading video", use_prefix=True, add=True)

        for g in pre:

            mv_list.append(g)

            progressbar.step(1)

            if not progressbar.final:
                # sleep(0.9)
                progressbar.update()

        p.close()
        p.join()

        save_mp4(mv_list, m3.file_name, path)


if __name__ == "__main__":
    links = ["https://v1.pinimg.com/videos/mc/hls/b9/96/55/b99655f9f7209dd63b3c2681538e2c30.m3u8", "https://v1.pinimg.com/videos/mc/hls/da/5e/dc/da5edc29199001230482c451c25a1b1f.m3u8"]
    broken_cat_url = ['https://v1.pinimg.com/videos/mc/hls/87/a4/e5/87a4e536c42fd9693a96e225e26706f0.m3u8']
    normal_cat_url = ['https://v.pinimg.com/videos/mc/hls/aa/f4/f3/aaf4f3fead7a6d9f0e8863dc341f87a9.m3u8']
    cat = ['https://v1.pinimg.com/videos/mc/hls/87/a4/e5/87a4e536c42fd9693a96e225e26706f0.m3u8', 'https://v.pinimg.com/videos/mc/hls/aa/f4/f3/aaf4f3fead7a6d9f0e8863dc341f87a9.m3u8', 'https://v.pinimg.com/videos/mc/hls/aa/f4/f3/aaf4f3fead7a6d9f0e8863dc341f87a9.m3u8']
    special = ["https://v1.pinimg.com/videos/mc/hls/da/5e/dc/da5edc29199001230482c451c25a1b1f.m3u8", "https://v1.pinimg.com/videos/mc/hls/da/5e/dc/da5edc29199001230482c451c25a1b1f.m3u8", "https://v1.pinimg.com/videos/mc/hls/da/5e/dc/da5edc29199001230482c451c25a1b1f.m3u8"]

    # request_opts = {}

    for index, link in enumerate(special):
        print("video number:", index + 1)
        download_m3u8(link, "../materials/", str(index + 1))
