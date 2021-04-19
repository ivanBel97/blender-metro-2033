import struct
from .reader import Reader


class FVec3:
    X: float = 0
    Y: float = 0
    Z: float = 0

    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(12)
        x, y, z = struct.unpack('<fff', data)

        return FVec3(x, y, z)


class UVec3:
    X: int = 0
    Y: int = 0
    Z: int = 0

    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(12)
        x, y, z = struct.unpack('<III', data)

        return UVec3(x, y, z)


class UVec3S16:
    X: int = 0
    Y: int = 0
    Z: int = 0

    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(6)
        x, y, z = struct.unpack('<HHH', data)

        return UVec3S16(x, y, z)


class UVec4:
    X: int = 0
    Y: int = 0
    Z: int = 0
    W: int = 0

    def __init__(self, x, y, z, w):
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(16)
        x, y, z, w = struct.unpack('<IIII', data)

        return UVec4(x, y, z, w)


class FVec4:
    X: int = 0
    Y: int = 0
    Z: int = 0
    W: int = 0

    def __init__(self, x, y, z, w):
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(16)
        x, y, z, w = struct.unpack('<ffff', data)

        return UVec4(x, y, z, w)


class UVec4S16:
    X: int = 0
    Y: int = 0
    Z: int = 0
    W: int = 0

    def __init__(self, x, y, z, w):
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(8)
        x, y, z, w = struct.unpack('<HHHH', data)

        return UVec4S16(x, y, z, w)


class FVec2:
    X: float = 0
    Y: float = 0

    def __init__(self, x, y):
        self.X = x
        self.Y = y

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(8)
        x, y = struct.unpack('<ff', data)

        return FVec2(x, y)


class UVec2:
    X: int = 0
    Y: int = 0

    def __init__(self, x, y):
        self.X = x
        self.Y = y

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(8)
        x, y = struct.unpack('<II', data)

        return UVec2(x, y)


class UVec2S16:
    X: int = 0
    Y: int = 0

    def __init__(self, x, y):
        self.X = x
        self.Y = y

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(4)
        x, y = struct.unpack('<HH', data)

        return UVec2S16(x, y)


class BBox:
    min: FVec3
    max: FVec3

    def __init__(self, mn, mx):
        self.min = mn
        self.max = mx

    @staticmethod
    def read(rd: Reader):
        return BBox(FVec3.read(rd=rd), FVec3.read(rd=rd))


class BSphere:
    center: FVec3
    radius: float

    def __init__(self, cent: FVec3, r: float):
        self.center = cent
        self.radius = r

    @staticmethod
    def read(rd: Reader):
        rad_bytes: bytes = rd.get_bytes(4)
        rad = struct.unpack('<f', rad_bytes)[0]

        return BSphere(FVec3.read(rd=rd), rad)
