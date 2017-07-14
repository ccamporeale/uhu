# Copyright (C) 2017 O.S. Systems Software LTDA.
# SPDX-License-Identifier: GPL-2.0

import unittest
from unittest.mock import patch

from uhu.core.updatehub import get_package_status, UpdateHubError


class PackageStatusTestCase(unittest.TestCase):

    @patch('uhu.core.updatehub.http.get')
    def test_returns_status_when_success(self, mock):
        mock.return_value.ok = True
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {'status': 'done'}
        status = get_package_status('1234')
        self.assertEqual(status, 'done')

    @patch('uhu.core.updatehub.http.get')
    def test_raises_error_if_server_error(self, mock):
        effects = [{}, ValueError]
        mock.return_value.ok = False
        mock.return_value.status_code = 404
        mock.return_value.json.side_effect = effects
        for _ in effects:
            with self.assertRaises(UpdateHubError):
                get_package_status('1234')
