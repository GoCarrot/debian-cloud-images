import collections
import functools


@functools.total_ordering
class AzureImageVersion(collections.namedtuple('AzureImageVersion', ['major', 'minor', 'patch'])):
    def __new__(cls, major, minor, patch):
        return super().__new__(cls, int(major), int(minor), int(patch))

    @classmethod
    def from_string(cls, s):
        return cls(*s.split('.'))

    def __eq__(self, other):
        return (self.major == other.major
                and self.minor == other.minor   # noqa:W503
                and self.patch == other.patch)  # noqa:W503

    def __lt__(self, other):
        if self.major < other.major:
            return True
        elif self.major > other.major:
            return False
        if self.minor < other.minor:
            return True
        elif self.minor > other.minor:
            return False
        return self.patch < other.patch

    def __hash__(self):
        return hash(self.major) + hash(self.minor) + hash(self.patch)

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'
