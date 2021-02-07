import collections


class AzureImageVersion(collections.namedtuple('AzureImageVersion', ['major', 'minor', 'patch'])):
    def __new__(cls, major, minor, patch):
        return super().__new__(cls, int(major), int(minor), int(patch))

    @classmethod
    def from_string(cls, s):
        return cls(*s.split('.'))

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'
