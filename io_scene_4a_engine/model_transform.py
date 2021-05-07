import math

from .model import *
from typing import List, Iterable

try:
    from bpy_extras import object_utils

    import bmesh
    import bpy
except ImportError:
    bpy = None
    bmesh = None


class ModelTransformToBlender:
    points: List[List[tuple]]
    uv_map: List[List[tuple]]
    normals: List[List[tuple]]

    faces: List[List[tuple]]

    def __init__(self, model_path: str):
        res = load_model(model_path)

        self.points, self.uv_map, self.normals, self.faces = [list(), list(), list(), list()]

        if type(res) is SimpleModel:
            self.from_simple_model(res)
        elif type(res) is HierarchyModel:
            if len(res.lod0) > 0:
                self.from_simple_model(res.lod0)
            elif len(res.meshes) > 0:
                self.from_simple_model(res.meshes)
            elif len(res.lod1) > 0:
                self.from_simple_model(res.lod1)
        elif type(res) is SkinnedModel:
            self.from_skinned_model(res)
        elif type(res) is RigModel:
            if len(res.lod0) > 0:
                res.lod0 = list(flatten(res.lod0))

                for skin_model in res.lod0:
                    print(type(skin_model))
                    self.from_skinned_model(skin_model)
            elif len(res.lod1) > 0:
                res.lod1 = list(flatten(res.lod1))

                for skin_model in res.lod1:
                    self.from_skinned_model(skin_model)
            elif len(res.lod2) > 0:
                res.lod2 = list(flatten(res.lod2))

                for skin_model in res.lod2:
                    self.from_skinned_model(skin_model)

    def render_model(self, context, operator):
        if bpy:
            mesh_count = len(self.points)

            obj_col = bpy.data.collections.new("4a_hierarchy")
            context.scene.collection.children.link(obj_col)

            for i in range(mesh_count):
                self.add_mesh("4a_mesh", self.points[i], self.faces[i], self.normals[i], self.uv_map[i], obj_col)

    def add_mesh(self, name, vertex, faces, normals, uv_map, col):
        normals2 = []
        vertex_count = len(vertex)

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(mesh.name, mesh)
        col.objects.link(obj)

        bm = bmesh.new()

        for i in range(0, vertex_count):
            bm.verts.new(vertex[i])
            normals2.append((
                self.calc_normal(normals[i][0]),
                self.calc_normal(normals[i][1]),
                self.calc_normal(normals[i][2])
            ))

        bm.verts.ensure_lookup_table()
        bm.verts.index_update()

        for idx in faces:
            try:
                face = bm.faces.new([bm.verts[i] for i in idx])
                face.smooth = True
            except ValueError:  # Face already exist
                pass

        bm.faces.ensure_lookup_table()
        bm.normal_update()

        bm.to_mesh(mesh)

        uv_layer = bm.loops.layers.uv.new('4A Texture')

        for f in bm.faces:
            for loop in f.loops:
                luv = loop[uv_layer]
                luv.uv = uv_map[loop.vert.index]

        mesh.auto_smooth_angle = math.pi
        mesh.use_auto_smooth = True

        mesh.normals_split_custom_set_from_vertices(normals2)

        mesh.update()

    def calc_normal(self, normal):
        return 2.0 * normal - 1.0

    def from_skinned_model(self, skin_model):
        skin_meshes = list(flatten(skin_model.meshes))

        for skin in skin_meshes:
            self.update_model_data(skin.vertex, skin.indies, True)

    def from_simple_model(self, h_models):
        simple_models_list: List[SimpleModel] = list(flatten(h_models))

        for simple_model in simple_models_list:
            vertex = simple_model.vertex.vertex
            indies = simple_model.faces.faces

            self.update_model_data(vertex, indies)

    def update_model_data(self, points, faces, is_skin=False):
        scale_factor = 2720.0
        uv_factor = 2048.0

        points = list(flatten(points))
        faces = list(flatten(faces))

        vertex = list()
        normal = list()
        uv = list()

        indies = list()

        for vert in points:
            if is_skin:
                vertex.append((vert.coord.X / scale_factor, vert.coord.Y / scale_factor, vert.coord.Z / scale_factor))
                uv.append((vert.uv_coord.X / uv_factor, vert.uv_coord.Y / uv_factor))
            else:
                vertex.append((vert.coord.X, vert.coord.Y, vert.coord.Z))
                uv.append((vert.uv_coord.X, vert.uv_coord.Y))

            normal.append((((vert.normal << 16) & 0xFF) / 255.0,
                           ((vert.normal << 8) & 0xFF) / 255.0,
                           (vert.normal & 0xFF) / 255.0))

        for face in faces:
            indies.append((face.X, face.Y, face.Z))

        normal = self.normalize_normal(normal)

        self.normals.append(normal)
        self.points.append(vertex)
        self.uv_map.append(uv)

        self.faces.append(indies)

    def normalize_normal(self, normals: List[tuple]):
        normals2 = list()

        for normal in normals:
            length = math.sqrt(float(normal[0] ** 2) + float(normal[1] ** 2) + float(normal[2] ** 2))
            if length > 0:
                normals2.append((normal[0] / length, normal[1] / length, normal[2] / length))
            else:
                normals2.append((normal[0], normal[1], normal[2]))

        return normals
