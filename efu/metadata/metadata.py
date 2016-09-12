# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import json
import os

from jsonschema import Draft4Validator, FormatChecker, RefResolver
from jsonschema.exceptions import ValidationError


SCHEMAS_DIR = os.path.dirname(__file__)


def validate(schema_fn, obj):
    base_uri = 'file://{}/'.format(SCHEMAS_DIR)
    with open(os.path.join(SCHEMAS_DIR, schema_fn)) as fp:
        schema = json.load(fp)
    resolver = RefResolver(base_uri, schema)
    format_checker = FormatChecker(formats=['uri'])
    validator = Draft4Validator(
        schema, resolver=resolver, format_checker=format_checker)
    validator.validate(obj)


class ObjectMetadata:

    def __init__(self, fn, sha256sum, size, options):
        self.filename = fn
        self.sha256sum = sha256sum
        self.size = size
        self._options = options if options is not None else {}

    def serialize(self):
        obj = {
            'filename': self.filename,
            'sha256sum': self.sha256sum,
            'size': self.size
        }
        if self._options is not None:
            obj.update(self._options)
        return obj

    def is_valid(self):
        schema = '{}-image.json'.format(self._options.get('install-mode'))
        try:
            validate(schema, self.serialize())
            return True
        except (ValidationError, FileNotFoundError):
            return False

    def __getattr__(self, attr):
        try:
            return self._options[attr.replace('_', '-')]
        except KeyError:
            raise AttributeError('{} is not a metadata option'.format(attr))
