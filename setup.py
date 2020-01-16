from setuptools import setup, find_packages
from os import path
from glob import glob

DIR = path.abspath(path.dirname(__file__))

description = """SharePy will handle authentication for your SharePoint Online/O365 site, allowing
you to make straightforward HTTP requests from Python. It extends the commonly used Requests module,
meaning that returned objects are familliar, easy to work with and well documented."""

with open(path.join(DIR, "./README.md")) as f:
    long_description = f.read()

setup(
    name="sharepy",
    version="2.0.0-beta",
    description="Simple SharePoint Online authentication for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="sharepoint online authentication",
    author="Jonathan Holvey",
    author_email="jonathan.holvey@outlook.com",
    url="https://github.com/JonathanHolvey/sharepy",
    project_urls={
        "Issues": "https://github.com/JonathanHolvey/sharepy/issues",
    },
    license="GPLv3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2.7"
    ],
    packages=find_packages(),
    package_dir={"": "src"},
    package_data={"sharepy": glob(path.join(DIR, "src/sharepy/templates/*"))},
    python_requires=">=3.5, <4"
)
