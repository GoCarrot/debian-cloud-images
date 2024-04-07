from __future__ import annotations

import pytest

from dataclasses import (
    dataclass,
)
from io import StringIO
from typing import Optional

from debian_cloud_images.utils.dataclasses_deb822 import (
    field_deb822,
    read_deb822,
    write_deb822,
    Deb822DecodeError,
)


@dataclass
class DTestDefault:
    field_str: str = field_deb822('Str')
    field_int: int = field_deb822('Int', default_factory=int)
    field_optional: Optional[str] = field_deb822('Optional', default=None)


@dataclass
class DTestSpecial:
    field_list: list[str] = field_deb822(
        'List',
        deb822_load=lambda a: a.split(),
        deb822_dump=lambda a: ' '.join(a),
    )


def test_default():
    i = '''Str: string1\nInt: 1\n\nStr: string2\n continuation\nInt: 2\nOptional: optional\n\n'''
    o: list[DTestDefault] = list(read_deb822(DTestDefault, StringIO(i)))

    assert len(o) == 2

    assert o[0].field_str == 'string1'
    assert o[1].field_str == 'string2\n continuation'

    assert o[0].field_int == 1
    assert o[1].field_int == 2

    assert o[0].field_optional is None
    assert o[1].field_optional == 'optional'

    f = StringIO()
    write_deb822(o, f)
    assert f.getvalue() == i


def test_default_unknown():
    i = '''Str: string1\nInt: 1\nUnknown: text\n continuation\n\n'''

    with pytest.raises(Deb822DecodeError):
        list(read_deb822(DTestDefault, StringIO(i)))

    o: list[DTestDefault] = list(read_deb822(DTestDefault, StringIO(i), ignore_unknown=True))

    assert len(o) == 1

    assert o[0].field_str == 'string1'


def test_special():
    i = '''List: a b c\n\n'''
    o: list[DTestSpecial] = list(read_deb822(DTestSpecial, StringIO(i)))

    assert o[0].field_list == ['a', 'b', 'c']

    f = StringIO()
    write_deb822(o, f)
    assert f.getvalue() == i
