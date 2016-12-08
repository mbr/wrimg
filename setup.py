#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(name='wrimg',
      version='0.3',
      description='An alternative to dd for writing images to sd-cards',
      long_description=read('README.rst'),
      author='Marc Brinkmann',
      author_email='git@marcbrinkmann.de',
      url='http://github.com/mbr/wrimg',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      install_requires=['click'],
      entry_points={
          'console_scripts': [
              'wrimg = wrimg.cli:wrimg',
          ],
      },
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
      ])
