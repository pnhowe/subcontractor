#!/usr/bin/env python3

import os
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools import find_packages


class build( build_py ):
  def build_packages( self ):
    # get all the .py files, unless they end in _test.py
    # we don't need testing files in our published product
    for package in self.packages:
      package_dir = self.get_package_dir( package )
      modules = self.find_package_modules( package, package_dir )
      for ( package2, module, module_file ) in modules:
        assert package == package2
        if os.path.basename( module_file ).endswith( '_test.py' ) or os.path.basename( module_file ) == 'tests.py':
          continue
        self.build_module( module, module_file, package )


setup( name='subcontractor',
       version='1.0',
       description='SubContractor, Doer of Contractor',
       author='Peter Howe',
       author_email='pnhowe@gmail.com',
       packages=find_packages(),
       cmdclass={ 'build_py': build }
       )
