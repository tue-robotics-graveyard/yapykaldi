from __future__ import print_function
import os
from setuptools import setup, Extension

VERSION = "0.0.1"
PACKAGE = "yapykaldi"


def _generate_ext():
    _ext_modules = []
    _cmdclass = {}

    return _ext_modules, _cmdclass


def _create_version_file(vfdir):
    print('-- Building version ' + VERSION)

    vfpath = os.path.join(vfdir, 'version.py')
    with open(vfpath, 'w') as vfh:
        vfh.write("__version__ = '{}'\n".format(VERSION))


if __name__ == "__main__":
    # Create version files
    cwd = os.path.dirname(os.path.abspath(__file__))
    version_file_dir = os.path.join(cwd, 'src', PACKAGE)
    _create_version_file(version_file_dir)

    # Get long description
    with open('README.md', 'r') as f:
        long_description = f.read()

    # Get extension module configurations and build commands
    ext_modules, cmdclass = _generate_ext()

    setup(
        name=PACKAGE,
        version='0.0.1',
        description='Yet Another Python interface to Kaldi Speech Recognition Toolkit',
        long_description=long_description,
        author='Arpit Aggarwal',
        author_email='ar13pit@gmail.com',
        maintainer='Arpit Aggarwal',
        maintainer_email='ar13pit@gmail.com',
        url='https://github.com/tue-robotics/yapykaldi',
        packages=[PACKAGE],
        package_dir={'': 'src'},
        cmdclass=cmdclass,
        ext_modules=ext_modules,
        classifiers=[
            'Operating System :: POSIX :: Linux',
            'License :: OSI Approved :: MIT License',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: C++',
            'Intended Audience :: Developers',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Multimedia :: Sound/Audio :: Speech'
        ],
        license='MIT',
        keywords='python kaldi asr',
        include_package_data=True,
        install_requires=[
            'numpy',
            'pybind11',
        ],
    )
