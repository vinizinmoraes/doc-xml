"""Setup script for XML Watcher Service."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="xml-watcher",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A cross-platform service that monitors folders for XML files and uploads them to an API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/xml-watcher",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "xml-watcher=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.example"],
    },
)
