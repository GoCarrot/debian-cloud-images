import pytest

import collections


PasswdEntry = collections.namedtuple('PasswdEntry', ['name', 'passwd', 'uid', 'gid', 'gecos', 'dir', 'shell'])


@pytest.fixture(scope="session")
def image_passwd_entry():
    pytest.fail('Unable to read /etc/passwd', pytrace=False)


# Read infos from /etc/passwd as it apears in the image and create entries as
# test parameters
def _read_image_passwd_entry(metafunc):
    path = metafunc.config.getoption('mount_path') / 'etc' / 'passwd'
    if path.exists():
        params = []
        with path.open() as f:
            for line in f.readlines():
                e = PasswdEntry(*line.strip().split(':'))
                params.append(pytest.param(e, id=e.name))
        metafunc.parametrize('image_passwd_entry', params)


def pytest_generate_tests(metafunc):
    if 'image_passwd_entry' in metafunc.fixturenames:
        _read_image_passwd_entry(metafunc)
