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

    faces: List[List[tuple]]

    def __init__(self, model_path: str):
        res = load_model(model_path)

        self.points, self.uv_map, self.faces = [list(), list(), list()]

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

    def render_model(self, context):
        if bpy:
            mesh_count = len(self.points)

            for i in range(mesh_count):
                ModelTransformToBlender.add_mesh(name="4a_mesh",
                                                 vert=self.points[i],
                                                 faces=self.faces[i],
                                                 context=context)

    @staticmethod
    def add_mesh(name, vert, faces, context):
        obj_col = bpy.data.collections.new(name)
        context.scene.collection.children.link(obj_col)

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)

        obj_col.objects.link(obj)

        mesh.from_pydata(vert, [], faces)
        mesh.update(calc_edges=True)

    def from_skinned_model(self, skin_model):
        skin_meshes = list(flatten(skin_model.meshes))

        for skin in skin_meshes:
            self.update_model_data(skin.vertex, skin.indies)

    def from_simple_model(self, h_models):
        simple_models_list: List[SimpleModel] = list(flatten(h_models))

        for simple_model in simple_models_list:
            vertex = simple_model.vertex.vertex
            indies = simple_model.faces.faces

            self.update_model_data(vertex, indies)

        print("Models count is ", len(simple_models_list))

    def update_model_data(self, points, faces):
        points = list(flatten(points))
        faces = list(flatten(faces))

        vertex = list()
        uv = list()

        indies = list()

        for vert in points:
            vertex.append((vert.coord.X, vert.coord.Y, vert.coord.Z))
            uv.append((vert.uv_coord.X, vert.uv_coord.Y))

        for face in faces:
            indies.append((face.X, face.Y, face.Z))

        self.points.append(vertex)
        self.uv_map.append(uv)

        self.faces.append(indies)
