#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

__dev_suffix__ = ''  # commonly ".dev"
__dev_build__ = ''   # commonly pipeline number

setup(
    name='webss',
    version='0.1a3' + __dev_suffix__ + __dev_build__,  # Required
    description='WebScreenShotter - simple command-line utility for creating website screenshots',
    url='https://github.com/ph20/webss',
    author='Alexander Grynchuk',
    author_email='agrynchuk@gmail.com',  # Optional
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='screenshot selenium web',
    package_dir={'': 'src'},
    packages=['webss'],
    python_requires='>=3.6',
    install_requires=[
        'selenium~=4.1',
        'Click~=8.0',
                      ],
    entry_points={
        'console_scripts': [
            'webss=webss.screenshot:main',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/ph20/webss/issues',
        'Source': 'https://github.com/ph20/webss/tree/main',
    },
)
