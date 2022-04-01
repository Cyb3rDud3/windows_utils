import os
import subprocess
import winreg
from ctypes import wintypes, windll, c_wchar_p
from zipfile import ZipFile

import requests

ES_SYSTEM_REQUIRED = 0x00000001
ES_CONTINUOUS = 0x80000000
startupinfo = subprocess.STARTUPINFO()
startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW


def setRegistryKey(key_name: str, value: str, registry_path: str, HKLM=False) -> bool:
    """
    :param key_name: registry key name
    :type key_name: str
    :param value: registry value
    :type value: str
    :param registry_path: full path to registry key
    :type registry_path: str
    :param HKLM: is HKLM
    :type HKLM: bool
    :return: bool
    """
    try:
        if HKLM:
            base_path = winreg.HKEY_LOCAL_MACHINE
        else:
            base_path = winreg.HKEY_CURRENT_USER
        winreg.CreateKey(base_path, registry_path)
        registry_key = winreg.OpenKey(base_path, registry_path, 0,
                                      winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, key_name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
        return True
    except WindowsError:
        return False


def getRegistryKey(key_name: str, registry_path: str, HKLM=False) -> str:
    """
    :param key_name: registry key name
    :type key_name: str
    :param registry_path: full path to registry key
    :type registry_path: str
    :param HKLM: is HKLM
    :type HKLM: bool
    :return: bool
    """
    try:
        if HKLM:
            base_path = winreg.HKEY_LOCAL_MACHINE
        else:
            base_path = winreg.HKEY_CURRENT_USER
        registry_key = winreg.OpenKey(base_path, registry_path, 0,
                                      winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, key_name)
        winreg.CloseKey(registry_key)
        return str(value)
    except WindowsError:
        return ""


def extract_zip(extraction_path: str, file_to_extract: str) -> bool:
    """
    :param extraction_path: full path to the dir that we will extract the zip into
    :param file_to_extract: name of file (possibly full path) of file to extract
    """
    try:
        with ZipFile(file_to_extract) as zf:
            zf.extractall(extraction_path)
        return True
    except Exception as e:
        print(e)
        return False


def download_file(path: str, URL: str) -> bool:
    """
    :param str path: full path on file system to download the file into
    :param str URL: url to download from.
    """
    with requests.get(URL, stream=True, verify=False) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return True


def hide_path(p: str) -> bool:
    """
    :param p: path that we want to make "hidden" using windows api.
    """
    try:
        windll.kernel32.SetFileAttributesW(p, 0x02)
        return True
    except Exception as e:
        return False


def run_pwsh(code: str) -> str:
    """
    :param code: powershell code to run

    //TODO 16: add creation flags to make hidden, but still get stdout.
    """
    p = subprocess.run(['powershell', code], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    return p.stdout.decode()


def run_detached_process(code: str, is_powershell=False) -> str:
    DETACHED_NEW_WITH_CONSOLE = {
        'close_fds': True,  # close stdin/stdout/stderr on child
        'creationflags': 0x00000008 | 0x00000200,
    }
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    if is_powershell:
        p = subprocess.run(code, stdin=subprocess.DEVNULL, shell=True, **DETACHED_NEW_WITH_CONSOLE)
        return ""
    else:
        p = subprocess.Popen(code, stdin=subprocess.DEVNULL, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                             **DETACHED_NEW_WITH_CONSOLE)
    stdout, stderr = p.communicate()
    return stdout


def ctypes_update_system() -> None:
    """
    use ctypes to call SendMessageTimeout directly
    to send broadcast to all windows.
    """
    SendMessageTimeout = windll.user32.SendMessageTimeoutW
    UINT = wintypes.UINT
    SendMessageTimeout.argtypes = wintypes.HWND, UINT, wintypes.WPARAM, c_wchar_p, UINT, UINT, UINT
    SendMessageTimeout.restype = wintypes.LPARAM
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x1A
    SMTO_NORMAL = 0x000
    SendMessageTimeout(HWND_BROADCAST, WM_SETTINGCHANGE, 0, 'Environment', SMTO_NORMAL, 10, 0)
    return


def set_env_variable(name: str, value: str) -> bool:
    '''
    :param name: environment variable name
    :param value: environment variable value
    '''

    if os.environ.get(name):
        if value in os.environ[name]:
            return True
        os.environ[name] = value + os.pathsep + os.environ[name]
        return True
    return False


def prevent_system_sleep() -> bool:
    """we are preventing"""

    windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    return True


def allow_system_sleep():
    """we are allowing system sleep"""
    windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS)
    return True


def turn_screen_off() -> bool:
    """
    this function mimick an hibernate event, putting off you screens
    """
    WM_SYSCOMMAND = 0x0112
    SC_MONITORPOWER = 0xF170
    window = windll.kernel32.GetConsoleWindow()
    windll.user32.SendMessageA(window, WM_SYSCOMMAND, SC_MONITORPOWER, 2)
    return True


def turn_screen_on() -> bool:
    windll.user32.mouse_event(1, 1, 1, 0, 0)
    return True

def enable_safemode():
    run_detached_process("bcdedit /set {default} safeboot network")
    return

def disable_safemod():
    run_detached_process("bcdedit /deletevalue {default} safeboot")
    return


def change_background(full_path_to_background):
    windll.user32.SystemParametersInfoW(20, 0, full_path_to_background, 0)
