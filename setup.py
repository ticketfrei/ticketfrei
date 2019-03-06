from setuptools import setup
import sys
import os

PACKAGE_NAME = "ticketfrei"

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), PACKAGE_NAME))

setup(
    name=PACKAGE_NAME,
    version='',
    packages=[
        PACKAGE_NAME
    ],
    url='https://github.com/ticketfrei/ticketfrei',
    license='ISC',
    author='',
    author_email='',
    description='',
    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'bottle',
        'gitpython',
        'pyjwt',
        'Markdown',
        'Mastodon.py',
        'pylibscrypt',
        'pytoml',
        'tweepy',
        'twx',
    ],
    tests_require=[
        'pytest',
    ],
)
