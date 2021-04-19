import struct

from .config import *
from .match import *

from typing import List
from dataclasses import dataclass
from os.path import exists

from .reader import Reader
from .skeleton import Skeleton
from .chunk import Chunk, ChunkData


@dataclass
class CheckSum:
    crc32: int = 0

    @staticmethod
    def read(rd: Reader):
        if Chunk.check(rd=rd, id_to_check=MODEL_CHUNK_SKELETON_CRC) is False:
            raise Exception("It's not crc32 chunk...")

        data = rd.get_bytes(4)
        check_sum = struct.unpack('<I', data)[0]

        return CheckSum(check_sum)


@dataclass
class Header:
    version: int
    type: int
    material_id: int
    bound_box: BBox
    bound_sphere: BSphere
    reserved: List[float]

    @staticmethod
    def read(rd: Reader):
        data: bytes = rd.get_bytes(4)

        ver, t, material_id = struct.unpack('<BBH', data)
        bb, bs = BBox.read(rd=rd), BSphere.read(rd=rd)
        r = struct.unpack('<IIIII', rd.get_bytes(20))

        return Header(ver, t, material_id, bb, bs, list(r))


@dataclass
class MaterialModel:
    texture_name: str
    shader: str
    material_name: str
    name: str
    magic_number: int

    @staticmethod
    def read(rd: Reader, header: Header):
        t = rd.read_string()
        s = rd.read_string()
        m = rd.read_string()

        if header.version >= MODEL_VER_LL:
            magic_num = 0
            n = rd.read_string()

            if header.type != MODEL_TYPE_SKINNED and header.type != MODEL_TYPE_SKINNED_MESH:
                magic_num = struct.unpack('<I', rd.get_bytes(4))
            else:
                magic_num = struct.unpack('<H', rd.get_bytes(2))

            return MaterialModel(t, s, m, n, magic_num)
        else:
            return MaterialModel(t, s, m, "", 0)


@dataclass
class VertexOne:
    coord: FVec3
    uv_coord: FVec2
    normal: int = 0
    bi_normal: int = 0
    tangent: int = 0

    @staticmethod
    def read(rd: Reader):
        crd = FVec3.read(rd=rd)
        norm = struct.unpack('<L', rd.get_bytes(4))[0]
        bi = struct.unpack('<L', rd.get_bytes(4))[0]
        tan = struct.unpack('<L', rd.get_bytes(4))[0]
        uv = FVec2.read(rd=rd)

        return VertexOne(crd, uv, norm, bi, tan)


@dataclass
class Poly:
    vertex_format: int
    vertex_count: int
    vertex: List[VertexOne]

    @staticmethod
    def read(rd: Reader):
        vert_format = struct.unpack('<I', rd.get_bytes(4))[0]
        count = struct.unpack('<I', rd.get_bytes(4))[0]
        vert = [VertexOne.read(rd=rd) for i in range(count)]

        return Poly(vert_format, count, vert)


@dataclass
class Indies:
    count: int
    faces: List[UVec3S16]

    @staticmethod
    def read(rd: Reader):
        count = struct.unpack('<I', rd.get_bytes(4))[0]
        count_faces = int(count / 3)

        faces = [UVec3S16.read(rd=rd) for i in range(count_faces)]

        return Indies(count_faces, faces)


@dataclass
class SimpleModel:
    header: Header
    material: MaterialModel
    vertex: Poly
    faces: Indies

    @staticmethod
    def read(rd: Reader):
        chunks_dates = ChunkData.get_all_chunk_data(rd=rd)

        h, m, v, f = (None, None, None, None)

        for chunk_data in chunks_dates:
            if chunk_data.chunk.id == MODEL_CHUNK_HEADER:
                h = Header.read(rd=chunk_data.data)
            if chunk_data.chunk.id == MODEL_CHUNK_TEXTURE:
                m = MaterialModel.read(rd=chunk_data.data, header=h)
            if chunk_data.chunk.id == MODEL_CHUNK_VERTICES:
                v = Poly.read(rd=chunk_data.data)
            if chunk_data.chunk.id == MODEL_CHUNK_INDICES:
                f = Indies.read(rd=chunk_data.data)

        return SimpleModel(h, m, v, f)


@dataclass
class HierarchyModel:
    header: Header

    lod0: List[SimpleModel]
    lod1: List[SimpleModel]
    lod2: List[SimpleModel]

    @staticmethod
    def read(rd: Reader):
        h = None

        l0 = list()
        l1 = list()
        l2 = list()

        rd.cursor_to_start()

        chunks_dates = ChunkData.get_all_chunk_data(rd=rd)

        for chunk_data in chunks_dates:
            if chunk_data.chunk.id == MODEL_CHUNK_HEADER and chunk_data.chunk.size == 64:
                h = Header.read(rd=chunk_data.data)
            elif chunk_data.chunk.id == MODEL_CHUNK_CHILD:
                h_model = HierarchyModel.read(rd=chunk_data.data)
                if len(h_model.lod0) > 0:
                    l0.append(h_model.lod0)
                if len(h_model.lod1) > 0:
                    l1.append(h_model.lod1)
                if len(h_model.lod2) > 0:
                    l2.append(h_model.lod2)
            elif chunk_data.chunk.id == MODEL_CHUNK_LOD0:
                l0.append(HierarchyModel.read(rd=chunk_data.data).lod2)
            elif chunk_data.chunk.id == MODEL_CHUNK_LOD1:
                l1.append(HierarchyModel.read(rd=chunk_data.data).lod2)
            elif chunk_data.chunk.id == MODEL_CHUNK_MTL_SETS:
                print("CHUNK MTL: Will be in further...")
            elif chunk_data.chunk.id == MODEL_CHUNK_COMMENT:
                print("CHUNK COMMENT: Will be in further...")
            elif (0 <= chunk_data.chunk.id < MODEL_CHUNK_MTL_SETS) and chunk_data.chunk.size > 0:
                l2.append(SimpleModel.read(rd=chunk_data.data))

        return HierarchyModel(h, l0, l1, l2)


@dataclass
class BonePosition:
    rotation: List[FVec3]
    offset: FVec3
    half_size: FVec3

    def __init__(self, r, off, half):
        self.rotation = r
        self.offset = off
        self.half_size = half

    @staticmethod
    def read(rd: Reader):
        r = [FVec3.read(rd=rd), FVec3.read(rd=rd), FVec3.read(rd=rd)]
        o = FVec3.read(rd=rd)
        hl = FVec3.read(rd=rd)

        return BonePosition(r, o, hl)


@dataclass
class VertexSkinned:
    coord: UVec4S16
    uv_coord: UVec2S16
    bones: List[int]
    weights: List[int]
    normal: int = 0
    bi_normal: int = 0
    tangent: int = 0

    @staticmethod
    def read(rd: Reader):
        point = UVec4S16.read(rd=rd)
        normal, tangent, bi_normal = struct.unpack('<LLL', rd.get_bytes(12))
        bones = list(struct.unpack('<BBBB', rd.get_bytes(4)))
        weights = list(struct.unpack('<BBBB', rd.get_bytes(4)))
        uv = UVec2S16.read(rd=rd)

        return VertexSkinned(point, uv, bones, weights, normal, bi_normal, tangent)


@dataclass
class SkinnedMesh:
    header: Header
    material: MaterialModel
    bone_id_list: List[int]
    bone_obb_list: List[BonePosition]
    vertex: List[VertexSkinned]
    indies: List[UVec3S16]
    indies_two: List[UVec3S16]

    @staticmethod
    def read(rd: Reader):
        header, material, bone_id, bone_obb, vert, indies, indies_two = (None, None, None, None, None, None, None)
        mesh_chunks = ChunkData.get_all_chunk_data(rd=rd)

        for mesh_chunk in mesh_chunks:
            if mesh_chunk.chunk.id == MODEL_CHUNK_HEADER:
                header = Header.read(rd=mesh_chunk.data)
            elif mesh_chunk.chunk.id == MODEL_CHUNK_TEXTURE:
                material = MaterialModel.read(rd=mesh_chunk.data, header=header)
            elif mesh_chunk.chunk.id == MODEL_CHUNK_SKIN_VERTICES:
                bone_count = mesh_chunk.data.read_byte()

                bone_id = [mesh_chunk.data.read_byte() for i in range(bone_count)]
                bone_obb = [BonePosition.read(rd=mesh_chunk.data) for i in range(bone_count)]

                vertex_length = mesh_chunk.data.read_long_word()

                if header.version >= MODEL_VER_ARCTIC:
                    mesh_chunk.data.read_word()

                vert = [VertexSkinned.read(rd=mesh_chunk.data) for i in range(vertex_length)]
            elif mesh_chunk.chunk.id == MODEL_CHUNK_INDICES:
                indies_length = 0
                indies_two_length = 0

                if header.version >= 18:
                    indies_length = mesh_chunk.data.read_word()
                    indies_two_length = mesh_chunk.data.read_word()
                else:
                    indies_length = int(mesh_chunk.data.read_long_word() / 3)

                indies = [UVec3S16.read(rd=mesh_chunk.data) for i in range(indies_length)]
                indies_two = [UVec3S16.read(rd=mesh_chunk.data) for i in range(indies_two_length)]

        return SkinnedMesh(header, material, bone_id, bone_obb, vert, indies, indies_two)


@dataclass
class SkinnedModel:
    meshes: List[SkinnedMesh]

    @staticmethod
    def read(rd: Reader, is_back: bool = False):
        if is_back is True:
            rd.cursor_to_start()

        meshes_to_add = list()
        chunks_dates = ChunkData.get_all_chunk_data(rd=rd)
        print(chunks_dates)

        for chunk_data in chunks_dates:
            if chunk_data.chunk.id == MODEL_CHUNK_CHILD:
                child_models = ChunkData.get_all_chunk_data(rd=chunk_data.data)
                for child_model in child_models:
                    meshes_to_add.append(SkinnedMesh.read(rd=child_model.data))

        return SkinnedModel(meshes_to_add)


@dataclass
class Material:
    surface: str
    texture: str
    shader: str

    @staticmethod
    def read(rd: Reader):
        surf = rd.read_string()
        tex = rd.read_string()
        shad = rd.read_string()

        return Material(surf, tex, shad)


@dataclass
class MaterialSet:
    name: str
    hit_preset: str
    voice: str
    flags: int
    materials: List[Material]

    def __init__(self, name, hit_prs, voice, flag, mats):
        self.name = name
        self.hit_preset = hit_prs
        self.voice = voice
        self.flags = flag
        self.materials = mats

    @staticmethod
    def read(rd: Reader):
        n = rd.read_string()
        h_p = rd.read_string()
        voice = rd.read_string()
        fl = rd.read_long_word()
        mats = [Material.read() for i in range(rd.read_word())]


@dataclass
class RigModel:
    lod0: List[SkinnedModel]
    lod1: List[SkinnedModel]
    lod2: List[SkinnedModel]
    rig: Skeleton

    @staticmethod
    def load_meshes(rd: Reader):
        meshes = list()

        while rd.can_read():
            meshes.append(SkinnedModel.read(rd=rd))

        return meshes

    @staticmethod
    def read(rd: Reader, header: Header):
        rd.cursor_to_start()

        chunk_dates = ChunkData.get_all_chunk_data(rd=rd)

        skeleton_path = ""
        meshes_name = list()

        l0 = list()
        l1 = list()
        l2 = list()

        rig = None

        for chunk_data in chunk_dates:
            if chunk_data.chunk.id == MODEL_CHUNK_SKELETON_FN:
                skeleton_path = chunk_data.data.read_string()
            elif chunk_data.chunk.id == MODEL_CHUNK_MESHES_FN:
                limit = chunk_data.data.read_long_word()
                meshes_name = [chunk_data.data.read_string() for i in range(limit)]
            elif chunk_data.chunk.id == MODEL_CHUNK_MESHES:
                if Chunk.check(rd=chunk_data.data, id_to_check=0):
                    l2.append(RigModel.load_meshes(rd=chunk_data.data))
                elif Chunk.check(rd=chunk_data.data, id_to_check=1):
                    l1.append(RigModel.load_meshes(rd=chunk_data.data))
                elif Chunk.check(rd=chunk_data.data, id_to_check=2):
                    l0.append(RigModel.load_meshes(rd=chunk_data.data))

        for mesh_name in meshes_name:
            print(mesh_name)

            if mesh_name != "":
                lod0_path = fr"{rd.get_content_path()}\meshes\{mesh_name.replace(',', '')}.mesh"
                lod1_path = fr"{rd.get_content_path()}\meshes\{mesh_name.replace(',', '')}_lod1.mesh"
                lod2_path = fr"{rd.get_content_path()}\meshes\{mesh_name.replace(',', '')}_lod2.mesh"

                if exists(lod0_path):
                    l0.append(load_model(lod0_path))
                if exists(lod1_path):
                    l1.append(load_model(lod1_path))
                if exists(lod2_path):
                    l2.append(load_model(lod2_path))

        if skeleton_path != "":
            if header.version < MODEL_VER_LL:
                skeleton_path = fr"{rd.get_content_path()}\meshes\{skeleton_path}.skeleton"
                rig = Skeleton()

                rig.start(skeleton_path)
                rig.read2033()

        return RigModel(l0, l1, l2, rig)


def load_model(model_path: str):
    with open(model_path, 'rb+') as model_reader:
        g_reader = Reader(model_reader.read(), model_path)

    chunks_dates = ChunkData.get_all_chunk_data(rd=g_reader)

    h = None

    for chunk_data in chunks_dates:
        if chunk_data.chunk.id == MODEL_CHUNK_HEADER:
            h = Header.read(rd=chunk_data.data)

    if h is None:
        raise Exception("Not found header of model")

    if h.type == MODEL_TYPE_NORMAL:
        return SimpleModel.read(rd=g_reader)
    elif h.type == MODEL_TYPE_HIERARCHY:
        return HierarchyModel.read(rd=g_reader)
    elif h.type == MODEL_TYPE_SKELETON or h.type == MODEL_TYPE_ANIMATED:
        return RigModel.read(rd=g_reader, header=h)
    elif h.type == MODEL_TYPE_SKINNED or h.type == MODEL_TYPE_SKINNED_MESH:
        return SkinnedModel.read(rd=g_reader, is_back=True)
