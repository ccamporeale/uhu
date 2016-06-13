# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from efu.auth import SignatureV1
from efu.request import Request


class RequestTestCase(unittest.TestCase):

    @patch('efu.request.datetime')
    def test_request_has_minimal_headers(self, mock):
        mock_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.utcnow.return_value = mock_date

        request = Request('https://localhost/', 'post', b'\0')

        host = request.headers.get('Host')
        timestamp = request.headers.get('Timestamp')
        sha256 = request.headers.get('Content-sha256')

        self.assertEqual(len(request.headers), 3)
        self.assertEqual(host, 'localhost')
        self.assertEqual(timestamp, 0)
        self.assertEqual(
            sha256,
            '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'
        )

    def test_header_content_sha256_when_bytes(self):
        payload = b'bytes'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)

    def test_header_content_sha256_when_string(self):
        payload = 'string'
        request = Request('localhost', 'post', payload)
        expected = hashlib.sha256(payload.encode()).hexdigest()
        observed = request.headers.get('Content-sha256')
        self.assertEqual(observed, expected)


class CanonicalRequestTestCase(unittest.TestCase):

    @patch('efu.request.datetime')
    def test_canonical_request(self, mock):
        date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        mock.utcnow.return_value = date
        request = Request(
            'http://localhost/upload?c=3&b=2&a=1',
            'post',
            b'\0',
        )
        expected = '''POST
/upload
a=1&b=2&c=3
content-sha256:6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d
host:localhost
timestamp:0.0

6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'''
        self.assertEqual(request.canonical(), expected)

    def test_canonical_query(self):
        url = 'https://localhost/?c=000&bb=111&aaa=222'
        request = Request(url, 'post', '')
        expected = 'aaa=222&bb=111&c=000'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_is_correctly_escaped(self):
        url = 'https://localhost/?to-be-scaped=scape me!&b=1&a=2'
        request = Request(url, 'post', '')
        expected = 'a=2&b=1&to-be-scaped=scape%20me%21'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_handles_repeated_values(self):
        url = 'https://localhost/?b=3&a=3&b=2&a=2&b=1&a=1'
        request = Request(url, 'post', '')
        expected = 'a=1&a=2&a=3&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_query_can_sort_escaped_repeated_values(self):
        url = 'https://localhost/?b=3&a=1&b=2&a=!&b=1&a= '
        request = Request(url, 'post', '')
        expected = 'a=%20&a=%21&a=1&b=1&b=2&b=3'
        observed = request._canonical_query()
        self.assertEqual(observed, expected)

    def test_canonical_headers(self):
        request = Request('http://foo.bar.com.br', 'post', '')
        request.headers = {
            'Host': 'foo.bar.com.br',
            'Content-sha256': '1234',
            'Timestamp': 123456.1234,
            'Accept': 'text/json',
        }
        expected = '''accept:text/json
content-sha256:1234
host:foo.bar.com.br
timestamp:123456.1234'''
        observed = request._canonical_headers()
        self.assertEqual(observed, expected)


class SignedRequestTestCase(unittest.TestCase):

    def test_signed_request_has_the_authorization_header(self):
        request = Request('https://127.0.0.1/upload', 'post', '')
        header = request.headers.get('Authorization', None)
        self.assertIsNone(header)

        request._sign()
        header = request.headers.get('Authorization', None)
        self.assertIsNotNone(header)