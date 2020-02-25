import sys
import os
from setuptools import setup, Extension, find_packages

try:
    import pybind11
except ImportError:
    raise Exception("pybind11 is needed to build this library")

try:
    import pkgconfig
except ImportError:
    raise Exception("pkgconfig is needed to build this library. Install with `pip install pkgconfig`.")


VERSION = "0.0.1"
PACKAGE = "yapykaldi"
PACKAGE_DIR = os.path.join('src', 'python')


def _find_dependencies(pkg):
    result_dict = pkgconfig.parse(pkg)
    result_dict['runtime_library_dirs'] = result_dict['library_dirs']
    return result_dict


def _generate_ext(ext_pkgs):
    _ext_modules = []
    _cmdclass = {}
    _cmdclass.update({'build_ext': build_ext})

    ext_root = os.path.join('src', 'cpp')
    ext_src = os.path.join(ext_root, 'src')
    ext_include = os.path.join(ext_root, 'include')

    sources = ['gmm_wrappers.cpp',
               'nnet3_wrappers.cpp']

    sources = [os.path.join(ext_src, f) for f in sources]

    sources = [os.path.join(ext_root, 'python_extensions.cpp')] + sources

    ext_dependencies = _find_dependencies(pkg=ext_pkgs)

    ext_dependencies.setdefault('include_dirs', []).append(ext_include)
    ext_dependencies.setdefault('include_dirs', []).append(pybind11.get_include())
    ext_dependencies.setdefault('include_dirs', []).append(pybind11.get_include(True))

    ext_name = "{}._Extensions".format(PACKAGE)

    _ext_modules = [
        Extension(ext_name,
                  sources,
                  language="c++",
                  extra_compile_args=[
                      '-Wall', '-pthread', '-std=c++11',
                      '-DKALDI_DOUBLEPRECISION=0', '-Wno-sign-compare',
                      '-Wno-unused-local-typedefs', '-Winit-self',
                      '-DHAVE_EXECINFO_H=1', '-DHAVE_CXXABI_H', '-DHAVE_ATLAS',
                      '-g'
                  ],
                  **ext_dependencies)
    ]

    return _ext_modules, _cmdclass


def _create_version_file(vfdir):
    vfpath = os.path.join(vfdir, 'version.py')
    with open(vfpath, 'w') as vfh:
        vfh.write("__version__ = '{}'\n".format(VERSION))


# Create version files
cwd = os.path.dirname(os.path.abspath(__file__))
version_file_dir = os.path.join(cwd, PACKAGE_DIR, PACKAGE)
_create_version_file(version_file_dir)

# Get long description
with open('README.md', 'r') as f:
    long_description = f.read()

# Get extension module configurations and build commands
ext_modules, cmdclass = _generate_ext(ext_pkgs='kaldi')

setup(
    name=PACKAGE,
    version=VERSION,
    packages=find_packages(PACKAGE_DIR),
    package_dir={'': PACKAGE_DIR},
    install_requires=[
        'numpy',
        'pybind11',
        'setuptools',
    ],
    zip_safe=True,
    author='Arpit Aggarwal',
    author_email='ar13pit@gmail.com',
    maintainer='Arpit Aggarwal',
    maintainer_email='ar13pit@gmail.com',
    url='https://github.com/tue-robotics/yapykaldi',
    description='Yet Another Python interface to Kaldi Speech Recognition Toolkit',
    long_description=long_description,
    license='MIT',
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
)
