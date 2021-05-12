from struct import pack

from dataclasses import dataclass, field
from typing import List


class DDSUtils:
    @staticmethod
    def convert_texture(metro_texture_path: str):
        if metro_texture_path is "":
            raise Exception("Path cannot be empty")

        with open(metro_texture_path, 'rb+') as image_bytes:
            image_dds_data = image_bytes.read()
            image_bytes.close()

        dds_header = DDSHeader()

        hw = metro_texture_path.split('.')[-1]  # height, width of texture
        hw = int(hw)  # convert to int

        dds_header.flags = 0x1 | 0x2 | 0x4 | 0x1000
        dds_header.caps = 0x1000

        if hw == 512:  # contains mip map
            dds_header.mip_map_count = 10
            dds_header.flags = dds_header.flags | 0x20000
            dds_header.caps = dds_header.caps | 0x400000

        dds_header.height = hw
        dds_header.width = hw

        is_dxt5 = True

        if hw == 512 and len(image_dds_data) == 174776:
            is_dxt5 = False
        elif hw == 1024 and len(image_dds_data) == 524288:
            is_dxt5 = False
        elif hw == 2048 and len(image_dds_data) == 2097152:
            is_dxt5 = False
        elif hw == 4096 and len(image_dds_data) == 16777216:
            is_dxt5 = False
        elif hw == 8192 and len(image_dds_data) == 268435456:
            is_dxt5 = False

        if is_dxt5:
            dds_header.dds_pixels.four_cc = DDSPixelFormat.make_four_cc(four_cc="DXT5")
        else:
            dds_header.dds_pixels.four_cc = DDSPixelFormat.make_four_cc(four_cc="DXT1")

        dds_result = dds_header.get_bytes() + image_dds_data

        dds_result_path = metro_texture_path.replace(f'.{hw}', '.dds')

        with open(dds_result_path, 'wb+') as dds_image:
            dds_image.write(dds_result)
            dds_image.close()

        return dds_result_path

    @staticmethod
    def pack_i32(num: int) -> bytes:
        return pack('<i', num)

    @staticmethod
    def pack_u32(num: int) -> bytes:
        return pack('<I', num)

    @staticmethod
    def pack_list_i32(nums: List[int]) -> bytes:
        res = bytes()

        for num in nums:
            res += DDSUtils.pack_i32(num)

        return res

    @staticmethod
    def pack_list_u32(nums: List[int]) -> bytes:
        res = bytes()

        for num in nums:
            res += DDSUtils.pack_u32(num)

        return res


@dataclass
class DDSPixelFormat:
    size: int = 32
    flags: int = 4
    four_cc: bytes = field(default_factory=bytes)
    rgb_bit_count: int = 0
    red_bit_mask: int = 0
    green_bit_mask: int = 0
    blue_bit_mask: int = 0
    alpha_bit_mask: int = 0

    def get_bytes(self) -> bytes:
        result = bytes()

        result += DDSUtils.pack_u32(self.size)  # convert size block
        result += DDSUtils.pack_u32(self.flags)  # convert flags pixels
        result += self.four_cc  # add four cc dds
        result += DDSUtils.pack_u32(self.rgb_bit_count)  # convert rgb mask
        result += DDSUtils.pack_u32(self.red_bit_mask)  # convert red mask
        result += DDSUtils.pack_u32(self.green_bit_mask)  # convert green mask
        result += DDSUtils.pack_u32(self.blue_bit_mask)  # convert blue mask
        result += DDSUtils.pack_u32(self.alpha_bit_mask)  # convert alpha mask

        return result

    @staticmethod
    def make_four_cc(four_cc: str) -> bytes:
        return str.encode(four_cc)


@dataclass
class DDSHeader:
    size: int = 124
    flags: int = 0
    height: int = 0
    width: int = 0
    linear_size: int = 0
    depth: int = 0
    mip_map_count: int = 0
    reserved: List[int] = field(default_factory=list)
    dds_pixels: DDSPixelFormat = field(default_factory=DDSPixelFormat)
    caps: int = 0
    caps2: int = 0
    caps3: int = 0
    caps4: int = 0
    reserved2: int = 0

    def get_bytes(self) -> bytes:
        result = bytes()

        if len(self.reserved) != 11:
            self.reserved = [0, 0, 0, 0,
                             0, 0, 0, 0,
                             0, 0, 0]

        result += DDSUtils.pack_u32(542327876)  # add signature of dds
        result += DDSUtils.pack_u32(self.size)  # to byte array size
        result += DDSUtils.pack_u32(self.flags)  # convert flags
        result += DDSUtils.pack_u32(self.height)  # convert height
        result += DDSUtils.pack_u32(self.width)  # convert width
        result += DDSUtils.pack_i32(self.linear_size)  # convert pitch ot linear size
        result += DDSUtils.pack_i32(self.depth)  # convert depth texture
        result += DDSUtils.pack_u32(self.mip_map_count)  # convert count of pixels (mip) maps
        result += DDSUtils.pack_list_i32(self.reserved)  # convert reserved
        result += self.dds_pixels.get_bytes()  # get bytes of pixels
        result += DDSUtils.pack_u32(self.caps)  # convert caps one of dds
        result += DDSUtils.pack_u32(self.caps2)  # convert caps two of dds
        result += DDSUtils.pack_u32(self.caps3)  # convert caps three of dds
        result += DDSUtils.pack_u32(self.caps4)  # convert caps four of dds
        result += DDSUtils.pack_u32(self.reserved2)  # convert reserved two of dds

        return result
