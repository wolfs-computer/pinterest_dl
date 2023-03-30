#!/usr/bin/env python3

# class for managing bokmarks while reading pins/boards

class BookmarkManager:
    def __init__(self):
        self.bookmarks = {}

    def add_bookmark(self, key, bookmark, secondary_key=None):
        if key not in self.bookmarks:
            self.bookmarks[key] = {}

        if secondary_key is not None:
            self.bookmarks[key][secondary_key] = bookmark
        else:
            self.bookmarks[key] = bookmark

    def get_bookmark(self, key, secondary_key=None):
        try:
            if secondary_key is not None:
                return self.bookmarks[key][secondary_key]
            else:
                return self.bookmarks[key]
        except KeyError:
            return None

    def del_bookmark(self, key, secondary_key=None):
        if key in self.bookmarks:
            if secondary_key is not None:
                del self.bookmarks[key][secondary_key]
            else:
                del self.bookmarks[key]

    def show_bookmarks(self):
        return self.bookmarks
