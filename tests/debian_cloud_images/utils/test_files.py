import bisect
import io
import os
import pytest

from debian_cloud_images.utils.files import ChunkedFile


class HoleFile(io.RawIOBase):
    """ Simulate file with support for SEEK_DATA and SEEK_HOLE. """

    def __init__(self, size, blocks):
        self.size = size

        # Files end with an implicit hole
        blocks[size] = False
        self.blocks = blocks
        self.__blocks_start = sorted(blocks.keys())

        self.seek(0)

    def _block_find(self, offset):
        """ Find number and start of block offset belongs to """
        n = bisect.bisect_left(self.__blocks_start, offset)
        return n, self.__blocks_start[n]

    def fileno(self):
        raise io.UnsupportedOperation

    def readinto(self, b):
        n = len(b)
        b[:] = b'1' * n
        return n

    def seek(self, offset, whence=os.SEEK_SET):
        if whence == os.SEEK_SET:
            if offset > self.size:
                raise ValueError
            n, start = self._block_find(offset)
            self.__current = offset
            self.__current_block = n
            return self.__current

        if whence == os.SEEK_END:
            if offset == 0:
                self.__current = self.size
                self.__current_block = len(self.__blocks_start) - 1
                return self.__current

        if whence == os.SEEK_DATA:
            n, start = self._block_find(offset)
            is_data = self.blocks[start]
            if is_data:
                # Returns self if within data
                pass
            else:
                # Returns start of next block
                n += 1
            self.__current = self.__blocks_start[n]
            self.__current_block = n
            return self.__current

        if whence == os.SEEK_HOLE:
            n, start = self._block_find(offset)
            is_data = self.blocks[start]
            if is_data:
                # Returns start of next block
                n += 1
            else:
                # Returns self if within hole
                pass
            self.__current = self.__blocks_start[n]
            self.__current_block = n
            return self.__current

        raise io.UnsupportedOperation

    def truncate(self):
        raise io.UnsupportedOperation

    def write(self):
        raise io.UnsupportedOperation


def test_ChunkedFile():
    fileobj = HoleFile(12, {
        0: True,
        2: False,
        4: True,
        9: False,
        10: True,
    })

    with ChunkedFile(fileobj, 2) as f:
        assert f.size == 12
        it = iter(f)

        c = next(it)
        assert c.offset == 0
        assert c.size == 2
        assert c.read(2) == b'11'

        c = next(it)
        assert c.offset == 4
        assert c.size == 2
        assert c.read(2) == b'11'

        c = next(it)
        assert c.offset == 6
        assert c.size == 2
        assert c.read(2) == b'11'

        c = next(it)
        assert c.offset == 8
        assert c.size == 1
        assert c.read(2) == b'1'

        c = next(it)
        assert c.offset == 10
        assert c.size == 2
        assert c.read(2) == b'11'

        with pytest.raises(StopIteration):
            next(it)
