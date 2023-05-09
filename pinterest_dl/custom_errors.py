#!/usr/bin/env python3

# import os

class PinterestDlError(Exception):
    def __init__(self, message=""):
            self.message = message

    # def __call__(self, *args):
    #     return self.__class__(*(self.args + args))

    def __str__(self):
        return str(self.message)


class PinterestDlException(PinterestDlError):
    """
    test1
    """
    pass

class BadM3u8File(PinterestDlError):
    """
    raised when bad .m3u8 file given
    """
    def __str__(self):
        return "Bad .m3u8 file"



# raise PinterestDlException("error number 1!")
# raise BadM3u8File

# try:
#     print("jk")
#     raise PinterestDlException("error number 1!")
# except PinterestDlException as p:
#     print(p)
