# Copyright (C) 2017 O.S. Systems Software LTDA.
# This software is released under the MIT License

import signal
import sys
from itertools import count

from uhu.core import Package
from uhu.core.manager import InstallationSetMode
from uhu.utils import LOCAL_CONFIG_VAR, CHUNK_SIZE_VAR

from tests.utils import (
    PushFixtureMixin, HTTPTestCaseMixin, UHUTestCase,
    FileFixtureMixin, EnvironmentFixtureMixin, UploadFixtureMixin)


product_uid = count()


def push_cmd(cmd):
    product = ''.rjust(64, str(next(product_uid)))
    name = ' '.join(cmd.__name__.split('_')).upper()

    def wrapped(self):
        pkg_fn = self.create_file('')
        self.set_env_var(LOCAL_CONFIG_VAR, pkg_fn)
        self.set_env_var(CHUNK_SIZE_VAR, 1)
        pkg = Package(
            InstallationSetMode.ActiveInactive, version='1', product=product)
        for _ in range(3):
            pkg.objects.create('raw', {
                'filename': self.create_file('spam'),
                'target-device': '/'
            })
        pkg.dump(pkg_fn)
        kwargs = cmd(self)
        self.set_push(pkg, '100',  **kwargs)
        print('- {}:\nexport {}={}\n'.format(name, LOCAL_CONFIG_VAR, pkg_fn))
    return wrapped


class UHUTestServer(PushFixtureMixin, FileFixtureMixin, UploadFixtureMixin,
                    EnvironmentFixtureMixin, HTTPTestCaseMixin, UHUTestCase):

    def __init__(self):
        self.start_server(port=8000, simulate_application=True)
        super().__init__()
        signal.signal(signal.SIGINT, self.shutdown)

    @push_cmd
    def push_success(self):
        return {}

    @push_cmd
    def push_existent(self):
        return {'upload_exists': True}

    @push_cmd
    def push_finish_push_fail(self):
        return {'finish_success': False}

    def shutdown(self, *args):
        print('Shutting down server...')
        self.clean()
        UHUTestServer.stop_server()

    def main(self):
        print('UHU test server\n')
        print('export UHU_SERVER_URL={}'.format(self.httpd.url('')))
        print('export UHU_CHUNK_SIZE=1')
        print()
        self.push_success()
        self.push_existent()
        self.push_finish_push_fail()


if __name__ == '__main__':
    sys.exit(UHUTestServer().main())
