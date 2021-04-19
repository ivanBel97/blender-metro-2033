from .match import *

from typing import List, TYPE_CHECKING
from dataclasses import dataclass, field

from .reader import Reader
from .chunk import Chunk


# Chunk IDs of Bones
CHUNK_VERSION = 1
CHUNK_BONES = 13
CHUNK_LOCATORS = 14
CHUNK_BONE_PARTS = 17
CHUNK_ANIM_PATH = 19
CHUNK_PARAMS = 27


@dataclass
class Locator:
    name: str = ""
    parent_name: str = ""
    orientation: FVec3 = field(default_factory=FVec3)
    q: FVec4 = field(default_factory=FVec4)
    position: FVec3 = field(default_factory=FVec3)
    flags: int = 0
    parent_id: int = 0

    @staticmethod
    def read2033(rd: Reader):
        name = rd.read_string()
        parent_name = rd.read_string()
        origin = FVec3.read(rd=rd)
        pos = FVec3.read(rd=rd)

        return Locator(name, parent_name, origin, None, pos, 0, 0)


@dataclass
class Bone:
    name: str
    parent_name: str
    orientation: FVec3
    position: FVec3
    bone_part: int
    parent_id: int

    @staticmethod
    def read2033(rd: Reader):
        n = rd.read_string()
        pn = rd.read_string()
        origin = FVec3.read(rd=rd)
        pos = FVec3.read(rd=rd)
        bp = rd.read_word()

        return Bone(n, pn, origin, pos, bp, 0)


@dataclass
class BonePart:
    name: str
    weights: List[int]

    @staticmethod
    def read2033(rd: Reader, bone_count: int):
        bone_parts: List[BonePart] = list()
        count = rd.read_word()

        for i in range(bone_count):
            name = rd.read_string()
            weights = [rd.read_byte() for i in range(count)]

            bone_parts.append(BonePart(name, weights))

        return bone_parts


@dataclass
class Skeleton:
    rd: Reader = None

    version: int = 0
    check_sum: int = 0
    count_bones: int = 0
    bones: List[Bone] = field(default_factory=list)
    locators: List[Locator] = field(default_factory=list)
    bones_part: List[BonePart] = field(default_factory=list)
    animation_path: str = ""

    def start(self, path: str):
        with open(path, 'rb+') as skeleton_data:
            self.rd = Reader(skeleton_data.read() , path)

    def read2033(self):
        result: bool = True

        if Chunk.check(rd=self.rd, id_to_check=CHUNK_VERSION):
            self.version = self.rd.read_long_word()
        elif result is True:
            result = False

        if Chunk.check(rd=self.rd, id_to_check=CHUNK_BONES):
            self.check_sum = self.rd.read_long_word()
            self.count_bones = self.rd.read_word()
            self.bones = [Bone.read2033(rd=self.rd) for i in range(self.count_bones)]
        elif result is True:
            result = False

        if Chunk.check(rd=self.rd, id_to_check=CHUNK_LOCATORS):
            count = self.rd.read_word()

            self.locators = [Locator.read2033(rd=self.rd) for i in range(count)]
        elif result is True:
            result = False

        if Chunk.check(rd=self.rd, id_to_check=CHUNK_BONE_PARTS):
            self.bones_part = BonePart.read2033(rd=self.rd, bone_count=self.count_bones)
        elif result is True:
            result = False

        if Chunk.check(rd=self.rd, id_to_check=CHUNK_ANIM_PATH):
            self.animation_path = self.rd.read_string()
        elif result is True:
            result = False

        for bone in self.bones:
            bone.parent_id = self.get_bone_id(bone.parent_name)

        for locator in self.locators:
            locator.parent_id = self.get_bone_id(locator.parent_name)

        return result

    def get_bone_id(self, parent_name: str) -> int:
        for i in range(self.count_bones):
            if self.bones[i].name == parent_name:
                return i

        return 0
