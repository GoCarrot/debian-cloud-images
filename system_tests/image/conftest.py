import pytest

import collections
import typing


@pytest.fixture(autouse=True)
def raise_test(request) -> None:
    if not hasattr(request, 'param'):
        return

    raise request.param


class Fixtures:
    def __init__(self) -> None:
        self.__func = {}

    def parametrize(self, name: str, metafunc: typing.Any) -> None:
        if func := self.__func.get(name):
            try:
                metafunc.parametrize(name, func(metafunc))
            except BaseException as e:
                metafunc.parametrize('raise_test', [e], indirect=True)

    def register(self, f: typing.Any) -> None:
        self.__func[f.__name__] = f


_fixtures = Fixtures()


PasswdEntry = collections.namedtuple('PasswdEntry', ['name', 'passwd', 'uid', 'gid', 'gecos', 'dir', 'shell'])


# Read infos from /etc/passwd as it apears in the image and create entries as
# test parameters
@_fixtures.register
def image_passwd_entry(metafunc):
    path = metafunc.config.getoption('mount_path') / 'etc' / 'passwd'
    if path.exists():
        with path.open() as f:
            params = []
            for line in f.readlines():
                e = PasswdEntry(*line.strip().split(':'))
                params.append(pytest.param(e, id=e.name))
            return params
    pytest.fail('Unable to read /etc/passwd inside image mount', pytrace=False)


def pytest_generate_tests(metafunc):
    for fixturename in metafunc.fixturenames:
        _fixtures.parametrize(fixturename, metafunc)
