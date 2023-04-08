#!/usr/bin/env python3
"""
class for managing bokmarks while reading pins/boards
"""


class BookmarkManager:
    """
    class for managing bookmarks on pinterest pages
    """

    def __init__(self):
        self.bookmarks = {}

    def add_bookmark(self, key, bookmark, secondary_key=None):
        """
        add bookmark to all bookmarks
        """
        if key not in self.bookmarks:
            self.bookmarks[key] = {}

        if secondary_key is not None:
            self.bookmarks[key][secondary_key] = bookmark
        else:
            self.bookmarks[key] = bookmark

    def get_bookmark(self, key, secondary_key=None):
        """
        get bookmark from all bookmarks
        """
        try:
            if secondary_key is not None:
                return self.bookmarks[key][secondary_key]
            else:
                return self.bookmarks[key]
        except KeyError:
            return None

    def del_bookmark(self, key, secondary_key=None):
        """
        delete bookmark from all bookmarks
        """
        if key in self.bookmarks:
            if secondary_key is not None:
                del self.bookmarks[key][secondary_key]
            else:
                del self.bookmarks[key]

    def show_bookmarks(self):
        """
        return all bookmarks
        """
        return self.bookmarks
