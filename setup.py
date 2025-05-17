#!/usr/bin/env python3
"""Setup script for the Kita Scraper package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kita-scraper",
    version="1.0.0",
    author="Zbigniew Zabost",
    author_email="zabostz@gmail.com",
    description="A tool to scrape pictures from your kita site and save them locally",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zbigniewzabost/verbose-journey",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kita-scraper=kita_scraper.cli:main",
        ],
    },
)
