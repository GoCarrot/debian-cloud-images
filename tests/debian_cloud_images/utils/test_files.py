import bisect
import errno
import io
import itertools
import os

from debian_cloud_images.utils.files import ChunkedFile


class HoleFile(io.RawIOBase):
    """ Simulate file with support for SEEK_DATA and SEEK_HOLE. """

    def __init__(self, size, blocks):
        self.size = size

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
            try:
                n, start = self._block_find(offset)
                is_data = self.blocks[start]
                if is_data:
                    # Returns self if within data
                    pass
                else:
                    # Returns start of next block
                    n += 1
                self.__current_block = n
                self.__current = self.__blocks_start[n]

            except IndexError:
                raise OSError(errno.ENXIO, 'Behind end of file')

            return self.__current

        if whence == os.SEEK_HOLE:
            try:
                n, start = self._block_find(offset)
                is_data = self.blocks[start]
                if is_data:
                    # Returns start of next block
                    n += 1
                else:
                    # Returns self if within hole
                    pass
                self.__current_block = n
                self.__current = self.__blocks_start[n]

            except IndexError:
                if offset >= self.size:
                    raise OSError(errno.ENXIO, 'Behind end of file')
                self.__current = self.size

            return self.__current

        raise io.UnsupportedOperation

    def truncate(self):
        raise io.UnsupportedOperation

    def write(self):
        raise io.UnsupportedOperation


def test_ChunkedFile_1():
    fileobj = HoleFile(8, {
        0: True,
        2: False,
        4: True,
        7: False,
    })

    result = [
        (True, 0, 2),
        (False, 2, 2),
        (True, 4, 2),
        (True, 6, 1),
        (False, 7, 1),
    ]

    with ChunkedFile(fileobj, 2) as f:
        assert f.size == 8

        for chunk, (want_is_data, want_offset, want_size) in itertools.zip_longest(f, result):
            assert chunk.is_data is want_is_data
            assert chunk.is_hole is not want_is_data
            assert chunk.offset == want_offset
            assert chunk.size == want_size
            assert len(chunk.read()) == want_size


def test_ChunkedFile_2():
    fileobj = HoleFile(8, {
        0: False,
        2: True,
        4: False,
        7: True,
    })

    result = [
        (False, 0, 2),
        (True, 2, 2),
        (False, 4, 2),
        (False, 6, 1),
        (True, 7, 1),
    ]

    with ChunkedFile(fileobj, 2) as f:
        assert f.size == 8

        for chunk, (want_is_data, want_offset, want_size) in itertools.zip_longest(f, result):
            assert chunk.is_data is want_is_data
            assert chunk.is_hole is not want_is_data
            assert chunk.offset == want_offset
            assert chunk.size == want_size
            assert len(chunk.read()) == want_size
