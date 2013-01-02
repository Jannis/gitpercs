#!/usr/bin/env python
#
# Copyright (C) 2012 Jannis Pohlmann <jannis.pohlmann@codethink.co.uk>
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import glob
import os
import subprocess

from distutils.core import Command, setup


class Clean(Command):
    pass


class Test(Command):
    
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        # run unit test coverage check
        subprocess.check_call(['python', '-m', 'CoverageTestRunner',
                               '--ignore-missing-from=modules-without-tests',
                               'gitpercs'])
        os.remove('.coverage')

        # run behaviorial test suite
        subprocess.check_call(['cmdtest', 'tests'])


setup(name='gitpercs',
      version='0.0.0',
      description='Versioned per-commit key/value store for Git',
      long_description='Versioned per-commit key/value store for Git',
      author='Jannis Pohlmann',
      author_email='jannis.pohlmann@codethink.co.uk',
      url='http://github.com/jannis/gitpercs',
      packages=['gitpercs'],
      cmdclass={
          'test': Test,
          'clean': Clean,
      })
