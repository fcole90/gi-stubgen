# From: https://github.com/allenai/python-package-template/blob/main/setup.py
from setuptools import find_packages, setup

setup(
    name="gi-stubgen",
    version="0.0.1",
    description="",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 1 - Planning",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Topic :: Documentation",
        "Topic :: Desktop Environment :: Gnome",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Code Generators",
    ],
    keywords="",
    url="https://github.com/fcole90/gi-stubgen",
    author="Gabriele Musco, Fabio Colella",
    author_email="gabmus at disroot dot org, fcole90@gmail.com",
    license="GPL3",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"],
    ),
    install_requires=[
        "gi-docgen"
    ],
    python_requires=">=3.7",
)
