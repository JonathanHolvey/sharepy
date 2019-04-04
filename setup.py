from setuptools import setup, find_packages

description = """SharePy will handle authentication for your SharePoint Online/O365 site, allowing
you to make straightforward HTTP requests from Python. It extends the commonly used Requests module,
meaning that returned objects are familliar, easy to work with and well documented."""

setup(
    name="sharepy",
    version="1.4.0",
    description="Simple SharePoint Online authentication for Python",
    long_description=description,
    url="https://github.com/JonathanHolvey/sharepy",
    author="Jonathan Holvey",
    author_email="jonathan.holvey@outlook.com",
    license="GPLv3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
    ],
    package_data={"sharepy": ["saml-templates/*.xml"]},
    keywords="sharepoint online authentication",
    packages=find_packages(),
	install_requires=["requests"]
)

"""
To publish:
$ python setup.py sdist
$ twine upload dist/*
"""
