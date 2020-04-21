import sys
import os
import tempfile
from glob import glob
import setuptools
from setuptools import setup, Extension, find_packages
from setuptools.command.build_ext import build_ext
import pybind11
import pkgconfig


VERSION = "0.2.0"
PACKAGE = "yapykaldi"
PACKAGE_DIR = os.path.join('src', 'python')


# As of Python 3.6, CCompiler has a `has_flag` method.
# cf http://bugs.python.org/issue26689
def _has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flagname])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


def _cpp_flag(compiler):
    """Return the -std=c++[11/14/17] compiler flag.

    The newer version is prefered over c++11 (when it is available).
    """
    flags = ['-std=c++17', '-std=c++14', '-std=c++11']

    for flag in flags:
        if _has_flag(compiler, flag):
            return flag

    raise RuntimeError('Unsupported compiler -- at least C++11 support '
                       'is needed!')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc'],
        'unix': [],
    }
    l_opts = {
        'msvc': [],
        'unix': [],
    }

    if sys.platform == 'darwin':
        darwin_opts = ['-stdlib=libc++', '-mmacosx-version-min=10.7']
        c_opts['unix'] += darwin_opts
        l_opts['unix'] += darwin_opts

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        link_opts = self.l_opts.get(ct, [])
        if ct == 'unix':
            opts.append('-DVERSION_INFO="%s"' % self.distribution.get_version())
            opts.append(_cpp_flag(self.compiler))
            if _has_flag(self.compiler, '-fvisibility=hidden'):
                opts.append('-fvisibility=hidden')
        elif ct == 'msvc':
            opts.append('/DVERSION_INFO=\\"%s\\"' % self.distribution.get_version())
        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        build_ext.build_extensions(self)


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

    # Get all .cpp source files
    sources = glob(os.path.join(ext_src, '*'))
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
        'pkgconfig',
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
