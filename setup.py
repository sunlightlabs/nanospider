import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "nanospider",
    version = "0.1.0",
    author = "Andrew Pendleton",
    author_email = "apendleton@sunlightfoundation.com",
    description = "A tiny caching link-follower built on gevent, lxml, and scrapelib",
    license = "BSD",
    keywords = "spider gevent lxml scrapelib",
    url = "http://github.com/sunlightlabs/nanospider/",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires = [
        "requests",
        "gevent",
        "scrapelib",
        "lxml",
        "url>=0.1.3",
    ],
    dependency_links=[
        "git+https://github.com/seomoz/url-py.git#egg=url-0.1.3",
    ],
)