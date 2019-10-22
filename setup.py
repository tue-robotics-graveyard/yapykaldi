from __future__ import print_function, unicode_literals
import sys
import os
import subprocess
import numpy
from setuptools import setup, Extension

VERSION = "0.0.1"
PACKAGE = "yapykaldi"

d_setup = {
    'author': 'Arpit Aggarwal',
    'author_email': 'ar13pit@gmail.com',
    'description': 'Yet Another Python interface to Kaldi Speech Recognition Toolkit',
    'license': 'MIT',
    'maintainer': 'Arpit Aggarwal',
    'maintainer_email': 'ar13pit@gmail.com',
    'name': PACKAGE,
    'url': 'https://github.com/tue-robotics/yapykaldi',
    'version': VERSION
}

try:
    from catkin_pkg.python_setup import generate_distutils_setup
    d = generate_distutils_setup()
    if d != d_setup:
        sys.exit("Catkin package error! Please ensure package.xml and this setup script have the same metadata.")
except Exception:
    d = d_setup


def _getstatusoutput(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    out, _ = process.communicate()
    return process.returncode, out


def find_dependencies():
    default_libdirs = ['/usr/lib', '/usr/lib/x86_64-linux-gnu', '/usr/lib/i386-linux-gnu']
    default_includedirs = ['/usr/include', '/usr/include/x86_64-linux-gnu', '/usr/include/i386-linux-gnu']
    kw = {}

    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}

    print("Looking for atlas library, trying pkg-config first...")

    status, output = _getstatusoutput(
        ["pkg-config", "--libs", "--cflags", "blas-atlas"])

    if status:
        print("looking for atlas library, trying hard-coded paths...")
        found = False
        for libdir, includedir in zip(default_libdirs, default_includedirs):
            if os.path.isfile('{}/libatlas.so'.format(libdir)) and os.path.isdir('{}/atlas'.format(includedir)):
                found = True
                break

        if not found:
            raise Exception('Failed to find libatlas.so and includes on your system.')

        kw.setdefault('libraries', []).append('{}/libatlas.so'.format(libdir))
        kw.setdefault('libraries', []).append('{}/libcblas.so'.format(libdir))
        kw.setdefault('libraries', []).append('{}/libf77blas.so'.format(libdir))
        kw.setdefault('libraries', []).append('{}/liblapack_atlas.so'.format(libdir))
        kw.setdefault('include_dirs', []).append('{}/atlas'.format(includedir))
        print("looking for atlas library, found it.")
    else:
        print("looking for atlas library, pkg-config found it")
        for token in output.split():
            token = token.decode('utf8')
            kw.setdefault(flag_map.get(token[:2]), []).append(token[2:])

    #
    # pkgconfig: kaldi-asr
    #

    status, output = _getstatusoutput(
        ["pkg-config", "--libs", "--cflags", "kaldi-asr"])

    if status:
        raise Exception("*** failed to find pkgconfig for kaldi-asr")

    for token in output.split():
        token = token.decode('utf8')
        kw.setdefault(flag_map.get(token[:2]), []).append(token[2:])

    return kw


def _generate_ext():
    _ext_modules = []
    _cmdclass = {}

    ext_root = os.path.join('src', PACKAGE, 'csrc')
    ext_src = os.path.join(ext_root, 'src')
    ext_include = os.path.join(ext_root, 'include')

    sources = ['gmm_wrappers.cpp']
    sources = [os.path.join(ext_src, f) for f in sources]

    sources = [os.path.join(ext_root, 'python_extensions.cpp')] + sources

    _ext_modules = [
        Extension(PACKAGE + '._Extensions',
                  sources,
                  include_dirs=[ext_include])
    ]

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
        long_description=long_description,
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
        keywords='python kaldi asr',
        include_package_data=True,
        install_requires=[
            'numpy',
            'pybind11',
        ],
        **d
    )
