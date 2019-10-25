#!/usr/bin/env python
# -*- coding: utf-8 -*
import codecs
import os
import re
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

with open('README.md') as f:
    long_description = f.read()

setup(
    name='confutils',
    version=find_version('confutils', '__init__.py'),
    packages=['confutils', ],
    entry_points={
        'console_scripts': [
            'process_sessions=confutils.cmd:process_sessions',
            'process_schedule=confutils.cmd:process_schedule',
            'update_website=confutils.cmd:update_website',
            'publish_website=confutils.cmd:publish_website',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    description=(
        'Internal package for uodating the conference website and metadata.'
    ),
    author='Francesco Pierfederici',
    author_email='fpierfed@iram.es',
    license='GNU General Public License v3 or later (GPLv3+)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ADASS-2020/www/confutils',
    install_requires=install_requires,
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: ' +
        'GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
