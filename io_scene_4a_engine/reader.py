import struct
import string


class Reader:
    last_length: int = 0
    bytes_data: bytes
    full_path: str

    def __init__(self, bytes_data: bytes, path: str):
        self.full_path = path
        self.bytes_data = bytes_data

    def cursor_to_start(self):
        self.last_length = 0

    def get_bytes(self, length: int) -> bytes:
        try:
            result: bytes = bytes([self.bytes_data[i] for i in range(self.last_length, self.last_length + length)])
            self.last_length += length

            return result
        except:
            raise Exception('Cannot get bytes from file!')

    def get_bytes_range(self, size: int):
        result = bytes([self.bytes_data[i] for i in range(self.last_length, self.last_length + size)])
        self.last_length += size

        return result

    def read_string(self) -> str:
        result = ""
        can_read = True

        while can_read:
            char = struct.unpack('<c', self.get_bytes(1))
            can_read = Reader.is_ascii(char)

            if can_read is True:
                result += str(char[0], 'ascii')

            if ',' in result:
                result.replace(',', '')
                can_read = False

        return result

    def get_content_path(self):
        return self.full_path[:self.full_path.find('\\meshes\\')]

    def read_long_word(self) -> int:
        return struct.unpack("<I", self.get_bytes(4))[0]

    def read_word(self) -> int:
        return struct.unpack("<H", self.get_bytes(2))[0]

    def read_byte(self) -> int:
        return struct.unpack("<B", self.get_bytes(1))[0]

    def back_cursor(self, number_to_backup: int):
        self.last_length -= number_to_backup

    def can_read(self):
        return len(self.bytes_data) > self.last_length

    @staticmethod
    def is_ascii(s):
        printable_chars = bytes(string.printable, 'ascii')
        return all(char in printable_chars for char in s)
