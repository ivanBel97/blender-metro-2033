import struct

from typing import List
from dataclasses import dataclass, field

from .reader import Reader


@dataclass
class Chunk:
    id: int = 0
    size: int = 0

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(8)
        b_id, b_size = struct.unpack('<II', data)
        return Chunk(b_id, b_size)

    @staticmethod
    def check(rd: Reader, id_to_check: List[int]) -> bool:
        result = False
        our_chunk = Chunk.read(rd=rd)

        if type(id_to_check) is int:
            result = id_to_check == our_chunk.id
        elif len(id_to_check) > 0 and len(rd.bytes_data) - rd.last_length >= 8:
            for c_id in id_to_check:
                if result is False:
                    result = c_id == our_chunk.id

        if result is False:
            rd.back_cursor(8)

        return result


@dataclass
class ChunkData:
    chunk: Chunk
    data: Reader

    @staticmethod
    def get_all_chunk_data(rd: Reader):
        parts = list()

        while rd.can_read():
            chunk_part = Chunk.read(rd=rd)
            data_part = rd.get_bytes_range(chunk_part.size)

            reader_part = Reader(data_part, rd.full_path)
            chunk_data = ChunkData(chunk_part, reader_part)

            parts.append(chunk_data)

        return parts
