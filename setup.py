from setuptools import setup
import os
import aja_tools

version_file = open(os.path.join('.', 'VERSION.txt'))
version_number = version_file.read().strip()
version_file.close()

setup(
    name = 'aja_tools',
    description = 'Wrangle AJA Sputter tool log files easier.',
    version = version_number,
    author = 'Faustin Carter',
    author_email = 'faustin.carter@gmail.com',
    license = 'MIT',
    url = 'http://github.com/sebastianbocquet/pygtc',
    packages = ['aja_tools'],
    long_description = open('README.rst').read(),
    install_requires = [
        'numpy',
        'matplotlib',
        'pandas',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Visualization'
    ]

)
