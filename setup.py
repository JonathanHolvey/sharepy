# --------------------------------------------------------------------------
#
# GNU GENERAL PUBLIC LICENSE
# --------------------------------------------------------------------------

from setuptools import setup, find_packages

setup(
    name='sharepy',
    version='1.0.0',
    author='Authors',
    packages=find_packages(exclude=["tests", "tests.*"]),
    url=("https://github.com/ljr55555/sharepy"),
    license='MIT License',
    description='Python sharepoint wrapper.',
    long_description=open('README.md').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE',
        'Topic :: Software Development'],
    install_requires=[
        "requests~=2.16"
    ],
)
