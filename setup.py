import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="WindowsUtils_Cyb3rDud3AndKupaRashit",
    version="0.0.1",
    author="Cyb3rDud3/KupaRashit",
    author_email="cyb3rguy1337@gmail.com",
    description="A Package for some useful utils in windows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Cyb3rDud3/windows_utils",
    project_urls={
        "Bug Tracker": "https://github.com/Cyb3rDud3/windows_utils/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)