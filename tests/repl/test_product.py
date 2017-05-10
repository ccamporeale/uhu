# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import os
import tempfile
import unittest

from uhu.core.manager import InstallationSetMode
from uhu.core.package import Package
from uhu.repl.repl import UHURepl
from uhu.repl import functions


class ProductTestCase(unittest.TestCase):

    def setUp(self):
        self.repl = UHURepl()

    def test_can_set_product_uid(self):
        self.assertIsNone(self.repl.package.product)
        self.repl.arg = '123456789'
        functions.set_product_uid(self.repl)
        self.assertEqual(self.repl.package.product, '123456789')

    def test_set_product_updates_prompt(self):
        self.assertEqual(self.repl.prompt, 'uhu> ')
        self.repl.arg = '123456789'
        functions.set_product_uid(self.repl)
        # only the first 6 chars must appears
        self.assertEqual(self.repl.prompt, '[123456] uhu> ')

    def test_start_prompt_with_package_updates_prompt(self):
        _, fn = tempfile.mkstemp()
        self.addCleanup(os.remove, fn)
        pkg = Package(InstallationSetMode.Single, product='123456789')
        pkg.dump(fn)
        self.repl = UHURepl(fn)
        self.assertEqual(self.repl.prompt, '[123456] uhu> ')

    def test_set_product_raises_error_if_missing_product(self):
        with self.assertRaises(ValueError):
            functions.set_product_uid(self.repl)
