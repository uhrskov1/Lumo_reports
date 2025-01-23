import glob
import os
import shutil


def appendExtensionIfExists(dst: str = None):
    """
    Method for detecting if a similar file already exists. If it does it will add an extention to the name
    @param dst: The full path and name where one wants to save the file.
    @return: dst: The full path and name.
    """
    dst_parts = dst.split(".")
    dst_path = ".".join(dst_parts[:-1])
    dst_extension = dst_parts[-1]

    i = 0
    while os.path.exists(dst):
        i += 1
        dst = f"{dst_path}_{str(i)}.{dst_extension}"

    return dst


def getFilePathsFolder(src: str = None, **kwargs):
    if "FileType" in kwargs:
        FileType = kwargs.get("FileType")
        FileType = f".{FileType}"
    # Check for new files in Index folder
    paths = glob.glob(rf"{src}\*{FileType}")

    return paths


def copyFile(src: str = None, dst: str = None, override: bool = False):
    """
    Method for copying files from one directory to another - with the option to override or not.
    src: The full path and name of the file which one wants to copy.
    dst: The full path and name where one wants to save the file.
    override: True if the file should override an existing file.
    """
    if not override:
        dst = appendExtensionIfExists(dst=dst)

    shutil.copy(src=src, dst=dst)

    return None


def moveFile(src: str = None, dst: str = None, override: bool = False):
    """
    Method for moving files from one directory to another - with the option to override or not.
    src: The full path and name of the file which one wants to copy.
    dst: The full path and name where one wants to save the file.
    override: True if the file should override an existing file.
    """
    if not override:
        dst = appendExtensionIfExists(dst=dst)

    shutil.move(src=src, dst=dst)
