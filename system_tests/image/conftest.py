import pytest

import collections
import subprocess
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
                metafunc.parametrize(name, [pytest.param(i[1], id=i[0]) for i in sorted(func(metafunc).items())])
            except BaseException as e:
                metafunc.parametrize('raise_test', [e], indirect=True)

    def register(self, f: typing.Any) -> None:
        self.__func[f.__name__ + '_entry'] = f
        return pytest.fixture(f)


_fixtures = Fixtures()


GroupEntry = collections.namedtuple('GroupEntry', ['name', 'passwd', 'gid', 'members'])
PackageEntry = collections.namedtuple('PackageEntry', ['name', 'version', 'architecture', 'status_want', 'status_status'])
PasswdEntry = collections.namedtuple('PasswdEntry', ['name', 'passwd', 'uid', 'gid', 'gecos', 'dir', 'shell'])


# Read infos from /etc/group as it apears in the image and create entries as
# test parameters
@_fixtures.register
def image_etc_group(request):
    path = request.config.getoption('mount_path') / 'etc' / 'group'
    if path.exists():
        with path.open() as f:
            ret = {}
            for line in f.readlines():
                entry = GroupEntry(*line.strip().split(':'))
                ret[entry.name] = entry
            return ret
    pytest.fail('Unable to read /etc/group inside image mount', pytrace=False)


# Read infos from /etc/passwd as it apears in the image and create entries as
# test parameters
@_fixtures.register
def image_etc_passwd(request):
    path = request.config.getoption('mount_path') / 'etc' / 'passwd'
    if path.exists():
        with path.open() as f:
            ret = {}
            for line in f.readlines():
                entry = PasswdEntry(*line.strip().split(':'))
                ret[entry.name] = entry
            return ret
    pytest.fail('Unable to read /etc/passwd inside image mount', pytrace=False)


@_fixtures.register
def image_packages(request):
    path = request.config.getoption('mount_path') / 'var/lib/dpkg'
    proc = subprocess.run(
        [
            'dpkg-query',
            '--show',
            '--showformat=${binary:Package};${Version};${Architecture};${db:Status-Want};${db:Status-Status}\n',
            f'--admindir={path}',
        ],
        check=True,
        encoding='ascii',
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        timeout=10,
    )

    ret = {}
    for line in proc.stdout.splitlines():
        entry = PackageEntry(*line.strip().split(';'))
        ret[entry.name] = entry
    return ret


def pytest_generate_tests(metafunc):
    for fixturename in metafunc.fixturenames:
        _fixtures.parametrize(fixturename, metafunc)
