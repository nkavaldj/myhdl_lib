""" setuptools distribution and installation script. """

from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup( name                 = 'myhdl_lib',
       version              = '0.1.0',
       description          = 'TODO: Library of components based on Python and MyHDL',
       long_description     = readme(),
       classifiers          = [
           'Development Status :: 3 - Alpha',
           'License :: OSI Approved :: MIT License',
           'Programming Language :: Python :: 2.7',
           'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
       ],
       keywords             = 'myhdl pihdf fpga',
       url                  = 'https://github.com/nkavaldj/myhdl_lib.git',
       author               = 'Nikolay Kavaldjiev',
       author_email         = 'nikolay.kavaldjiev@gmail.com',
       license              = 'MIT',
       packages             = [
           'myhdl_lib',
           'myhdl_lib.simulation'
       ],
       install_requires     = [
           'myhdl'
       ],
       include_package_data = True,
       zip_safe             = False
    )
