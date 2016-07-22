# Copyright (C) 2016 O.S. Systems Software LTDA.
# This software is released under the MIT License

import hashlib
import os
from itertools import count

from ..utils import get_chunk_size

from . import exceptions


class FileChunk(object):

    _number = count()

    def __new__(cls, chunk):
        return super().__new__(cls) if chunk else None

    def __init__(self, chunk):
        self.number = next(self._number)
        self.sha256sum = hashlib.sha256(chunk).hexdigest()

    def as_dict(self):
        return {
            'sha256sum': self.sha256sum,
            'number': self.number,
        }

    @classmethod
    def reset_number_generator(cls):
        cls._number = count()


class File(object):

    _id = count()

    def __new__(cls, fn):
        if os.path.isfile(fn):
            return super().__new__(cls)
        raise exceptions.InvalidFileError(
            'file {} does not exist'.format(fn))

    def __init__(self, fn):
        self.id = next(self._id)
        self.name = fn
        self.size = os.path.getsize(self.name)
        self.sha256sum, self.chunks = self._generate_file_hashes()

    def _generate_file_hashes(self):
        sha256sum = hashlib.sha256()
        chunks = []
        with open(self.name, 'br') as fp:
            for chunk in iter(lambda: fp.read(get_chunk_size()), b''):
                chunks.append(FileChunk(chunk))
                sha256sum.update(chunk)
        FileChunk.reset_number_generator()
        return (sha256sum.hexdigest(), chunks)

    def as_dict(self):
        return {
            'id': self.id,
            'sha256sum': self.sha256sum,
            'parts': [chunk.as_dict() for chunk in self.chunks],
            'metadata': {
                'sha256sum': self.sha256sum
            }
        }

    @property
    def metadata(self):
        return {
            'filename': self.name,
            'sha256sum': self.sha256sum,
            'size': self.size
        }

    @property
    def n_chunks(self):
        return len(self.chunks)

    @classmethod
    def __reset_id_generator(cls):
        cls._id = count()