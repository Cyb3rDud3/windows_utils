import os
from shutil import which
from src.windows_utils.runtime.system.actions import getRegistryKey,run_pwsh,download_file
from src.windows_utils.runtime.system.utils import tempFolder,random_string
from src.windows_utils.runtime.system.info import Info

SYS_INFO = Info()
is_os_64bit = SYS_INFO.is_os_64bit


class PythonEnvironment:
    def __init__(self):
        self.python_path: str = ""
        self.is_python_installed: bool = False
        self.python_version: str = ""
        self.is_pyinstaller_exist: bool = False
        self.is_cython_exist: bool = False
        self.is_installed_as_admin: bool = False

    @property
    def __find_python_path(self) -> bool:
        python_reg_key = r"SOFTWARE\Python\PythonCore\3.{}\InstallPath"
        python_reg_value = "ExecutablePath"
        BASIC_APPDATA_LOCATION = r"c:\Users\{}\appdata\local\Programs\Python\Python3{}\python.exe"
        possible_locations = ['c:/Program Files', 'c:/Program Files (x86)', 'c:/ProgramData']
        for python_minor_version in range(5, 10):
            try:
                admin_value = getRegistryKey(key_name=python_reg_value,
                                             registry_path=python_reg_key.format(python_minor_version), HKLM=True)
                user_value = getRegistryKey(key_name=python_reg_value,
                                            registry_path=python_reg_key.format(python_minor_version), HKLM=False)
                if user_value:
                    self.is_python_installed = True
                    self.python_version = f"3.{python_minor_version}"
                    self.python_path = user_value
                    return True
                if admin_value:
                    self.is_installed_as_admin = True
                    self.is_python_installed = True
                    self.python_version = f"3.{python_minor_version}"
                    self.python_path = admin_value
                    return True
            except WindowsError:
                continue
            if os.path.exists(BASIC_APPDATA_LOCATION.format(os.getlogin(), python_minor_version)):
                self.is_python_installed = True
                self.python_version = f"3.{python_minor_version}"
                self.python_path = BASIC_APPDATA_LOCATION.format(os.getlogin(), python_minor_version)
                return True
        for location in possible_locations:
            if os.path.exists(location) and os.path.isdir(location):
                for directory in os.listdir(location):
                    if 'python' in directory.lower():
                        if ''.join([char for char in directory.lower() if char.isdigit()]).startswith('3'):
                            path_to_python = os.path.join(location, directory)
                            if 'python.exe' in os.listdir(path_to_python):
                                self.is_python_installed = True
                                self.python_path = os.path.join(path_to_python, 'python.exe')
                                return True

        from_shutil = which("python")
        if from_shutil:
            self.is_python_installed = True
            self.python_path = from_shutil
            return True
        from_shell = ''.join([line.strip() for line in run_pwsh("where python").splitlines() if
                              'WindowsApps' not in line and 'python.exe' in line])
        if from_shell:
            self.is_python_installed = True
            self.python_path = from_shell
            return True
        return False

    @property
    def __find_pyinstaller(self):
        if not self.is_python_installed:
            return False
        if self.search_package_in_pip('pyinstaller'):
            self.is_pyinstaller_exist = True
            return True
        return False

    @property
    def __find_cython(self):
        if not self.is_python_installed:
            return False
        if self.search_package_in_pip('cython'):
            self.is_cython_exist = True
            return True
        return False

    def search_package_in_pip(self, package):
        from_pwsh = run_pwsh(f"{self.python_path} -m pip list").splitlines()
        for line in from_pwsh:
            if package in line.lower():
                return True
        return False

    def install_package_with_pip(self, package):
        pwsh_command = run_pwsh(f"{self.python_path} -m pip install {package}")
        if self.search_package_in_pip(package):
            return True
        print('[*] Something Went wrong with installing the package, this is the stdout {}'.format(pwsh_command))
        return False

    def install_python(self, version="3.8.1", as_admin=False):
        py64_url = f"https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe"
        py32_url = f"https://www.python.org/ftp/python/{version}/python-{version}.exe"
        InstallAllUsers = 0 if not as_admin else 1
        Include_launcher = 0 if not as_admin else 1
        url = py64_url if is_os_64bit else py32_url
        rand_py = tempFolder.format(os.getlogin(), f"{random_string(is_random=True, is_exe=True)}")
        install_python_command = f"{rand_py} /quiet InstallAllUsers={InstallAllUsers} Include_launcher={Include_launcher} PrependPath=1 Include_test=0"
        if download_file(rand_py, url):
            run_pwsh(install_python_command)
            return PythonEnvironment()
        return False
