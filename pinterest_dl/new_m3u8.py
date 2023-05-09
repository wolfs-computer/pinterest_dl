#!/usr/bin/env python3

import m3u8
import requests
from pprint import pprint


url = "https://v1.pinimg.com/videos/mc/hls/87/a4/e5/87a4e536c42fd9693a96e225e26706f0.m3u8"
# url = "https://v1.pinimg.com/videos/mc/hls/da/5e/dc/da5edc29199001230482c451c25a1b1f.m3u8"

responce = requests.get(url)
file = responce.text

playlist = m3u8.loads(file)

print(playlist.dumps())
# print(playlist.keys)
pprint(playlist.data)


#
# m3u8_parsed = m3u8.load(url)
#
# with open('../materials/track.ts', 'wb') as f:
#     for segment in m3u8_parsed.segments:
#         r = requests.get(segment.absolute_uri)
#         f.write(r.content)
