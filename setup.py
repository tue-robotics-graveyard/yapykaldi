from setuptools import setup


cmdclass = {}
ext_modules = []

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='yapykaldi',
    version='0.0.1',
    description='Yet Another Python interface to Kaldi Speech Recognition Toolkit',
    long_description=long_description,
    author='Arpit Aggarwal',
    author_email='ar13pit@gmail.com',
    maintainer='Arpit Aggarwal',
    maintainer_email='ar13pit@gmail.com',
    url='https://github.com/tue-robotics/yapykaldi',
    packages=['yapykaldi'],
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
