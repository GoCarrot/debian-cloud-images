import os


class ChunkedFile:
    """
    Read chunks of a file with a maximum size.  Holes are excluded.
    """

    class Chunk:
        def __init__(self, fileobj, offset: int, size: int) -> None:
            self.fileobj = fileobj
            self.offset = offset
            self.size = size

        def read(self, length=None) -> bytes:
            self.fileobj.seek(self.offset, os.SEEK_SET)
            return self.fileobj.read(self.size)

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

        while hole_offset < self.size:
            # Detect start and end of next data section
            data_offset = self.fileobj.seek(hole_offset, os.SEEK_DATA)
            hole_offset = self.fileobj.seek(data_offset, os.SEEK_HOLE)
            size = hole_offset - data_offset

            blocks, remainder = divmod(size, self.chunk_size)

            for b in range(blocks):
                start = data_offset + b * self.chunk_size
                yield self.Chunk(self.fileobj, start, self.chunk_size)

            if remainder:
                start = data_offset + blocks * self.chunk_size
                yield self.Chunk(self.fileobj, start, remainder)
