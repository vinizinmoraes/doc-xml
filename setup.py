"""Setup script for XML Watcher Service."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Runtime dependencies only - development dependencies should not be included
requirements = [
    "watchdog==3.0.0",
    "requests==2.31.0", 
    "PyYAML==6.0.1",
    "python-dotenv==1.0.0",
    "colorlog==6.7.0",
    "tqdm==4.66.1",
    "pywin32==306; sys_platform == 'win32'",
]

setup(
    name="xml-watcher",
    version="1.0.0",
    author="Vinícius Morais",
    author_email="vinizinmoraes@users.noreply.github.com",
    description="A cross-platform service that monitors folders for XML files and uploads them to an API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vinizinmoraes/doc-xml",
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
