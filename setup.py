#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
$ python setup.py register sdist upload

First Time register project on pypi
https://pypi.org/manage/projects/


More secure to use twine to upload
$ pip3 install twine
$ python3 setup.py sdist
$ twine upload dist/keria-0.0.1.tar.gz


Update sphinx /docs
$ cd /docs
$ sphinx-build -b html source build/html
or
$ sphinx-apidoc -f -o source/ ../src/
$ make html

Best practices for setup.py and requirements.txt
https://caremad.io/posts/2013/07/setup-vs-requirement/
"""

from pathlib import Path
from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

this_directory = Path(__file__).parent
if (this_directory / "README.md").exists():  # If building inside a container, like in the `images/keria.dockerfile`, this file won't exist and fails the build
    long_description = (this_directory / "README.md").read_text()
else:
    long_description = "KERIA: KERI Agent in the cloud."

setup(
    name='keria',
    version='0.2.0-rc2',  # also change in src/keria/__init__.py
    license='Apache Software License 2.0',
    description='KERIA: KERI Agent in the cloud',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Philip S. Feairheller',
    author_email='pfeairheller@gmail.com',
    url='https://github.com/WebOfTrust/keria',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: Implementation :: CPython',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: PyPy',
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],
    project_urls={
        'Documentation': 'https://weboftrust.github.io/keridoc',
        'Issue Tracker': 'https://github.com/WebOfTrust/keria/issues',
        'Source': 'https://github.com/WebOfTrust/keria',
    },
    keywords=[
        "secure attribution",
        "authentic data",
        "discovery",
        "resolver"
    ],
    python_requires='>=3.12.2',
    install_requires=[
        'hio==0.6.14',
        'keri==1.2.6',
        'mnemonic==0.21',
        'multicommand==1.0.0',
        'falcon==4.0.2',
        'http_sfv==0.9.9',
        'dataclasses_json==0.6.7',
        'apispec==6.8.1',
        'deprecation==2.1.0',
    ],
    extras_require={
        'test': ['pytest', 'coverage'],
        'docs': ['sphinx', 'sphinx-rtd-theme'],
        'dev': ['ruff>=0.8.0', 'pytest', 'coverage']
    },
    tests_require=[
        'coverage>=7.6.10',
        'pytest>=8.3.4',
    ],
    setup_requires=[
    ],
    entry_points={
        'console_scripts': [
            'keria = keria.app.cli.keria:main',
        ]
    },
)
