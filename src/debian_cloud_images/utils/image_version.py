import collections
import typing

from datetime import datetime


class ImageVersion(collections.namedtuple('ImageVersion', ['date', 'build'])):
    def __new__(cls, date: typing.Optional[datetime], build: int):
        return super().__new__(cls, date, build)

    @classmethod
    def from_string(cls, s: str):
        sl = s.split('-', 1)
        if len(sl) == 1:
            return cls(None, int(sl[0]))
        return cls(datetime.strptime(sl[0], '%Y%m%d'), int(sl[1]))

    def __str__(self):
        if self.date:
            return f'{self.date.strftime("%Y%m%d")}-{self.build}'
        return f'{self.build}'
