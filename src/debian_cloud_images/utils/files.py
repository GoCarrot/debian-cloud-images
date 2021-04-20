import errno
import os


class ChunkedFile:
    """
    Read chunks of a file with a maximum size.
    """

    class ChunkData:
        is_data = True
        is_hole = False

        def __init__(self, fileobj, offset: int, size: int) -> None:
            self.fileobj = fileobj
            self.offset = offset
            self.size = size

        def read(self, length=None) -> bytes:
            self.fileobj.seek(self.offset, os.SEEK_SET)
            return self.fileobj.read(self.size)

    class ChunkHole:
        is_data = False
        is_hole = True

        def __init__(self, fileobj, offset: int, size: int) -> None:
            self.fileobj = fileobj
            self.offset = offset
            self.size = size

        def read(self, length=None) -> bytes:
            return b'\0' * self.size

    def __init__(self, fileobj, chunk_size: int) -> None:
        self.fileobj = fileobj
        self.size = fileobj.seek(0, os.SEEK_END)
        self.chunk_size = chunk_size

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fileobj.close()

    def __iter__(self):
        data_offset = hole_offset = self.fileobj.seek(0, os.SEEK_SET)

        while True:
            # Detect start next data section
            try:
                data_offset = self.fileobj.seek(hole_offset, os.SEEK_DATA)
            except OSError as e:
                if e.errno != errno.ENXIO:
                    raise
                # Next data section would be after end of file
                yield from self.chunks(hole_offset, self.size, self.ChunkHole)
                return

            yield from self.chunks(hole_offset, data_offset, self.ChunkHole)

            # Detect start next hole section
            hole_offset = self.fileobj.seek(data_offset, os.SEEK_HOLE)
            yield from self.chunks(data_offset, hole_offset, self.ChunkData)

    def chunks(self, begin: int, end: int, cls):
        blocks, remainder = divmod(end - begin, self.chunk_size)

        for b in range(blocks):
            start = begin + b * self.chunk_size
            yield cls(self.fileobj, start, self.chunk_size)

        if remainder:
            start = begin + blocks * self.chunk_size
            yield cls(self.fileobj, start, remainder)
