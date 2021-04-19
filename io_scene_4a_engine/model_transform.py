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
            elif len(res.lod1) > 0:
                self.from_simple_model(res.lod1)
            elif len(res.lod2) > 0:
                self.from_simple_model(res.lod2)
        elif type(res) is SkinnedModel:
            self.from_skinned_model(res)
        elif type(res) is RigModel:
            if len(res.lod0) > 0:
                res.lod0 = list(ModelTransformToBlender.flatten(res.lod0))

                for skin_model in res.lod0:
                    self.from_skinned_model(skin_model)
            elif len(res.lod1) > 0:
                res.lod1 = list(ModelTransformToBlender.flatten(res.lod1))

                for skin_model in res.lod1:
                    self.from_skinned_model(skin_model)
            elif len(res.lod2) > 0:
                res.lod2 = list(ModelTransformToBlender.flatten(res.lod2))

                for skin_model in res.lod2:
                    self.from_skinned_model(skin_model)

    def render_model(self, context):
        if bpy:
            mesh_count = len(self.points)

            # new collection
            obj_col = bpy.data.collections.new('4a_model')
            context.scene.collection.children.link(obj_col)

            for i in range(mesh_count):
                # mesh
                mesh = bpy.data.meshes.new("4A_Model")
                mesh.from_pydata(self.points[i], [], self.faces[i])
                mesh.update()

                # object
                obj = bpy.data.objects.new('4a_object', mesh)

                # link
                obj_col.objects.link(obj)

    def from_skinned_model(self, skin_model):
        skin_meshes = list(ModelTransformToBlender.flatten(skin_model.meshes))

        for skin in skin_meshes:
            if skin.indies_two is not None and len(skin.indies_two) > 1:
                self.update_model_data(skin.vertex, [skin.indies, skin.indies_two])
            else:
                self.update_model_data(skin.vertex, skin.indies)

    def from_simple_model(self, h_models):
        simple_models_list = list(ModelTransformToBlender.flatten(h_models))

        for simple_model in simple_models_list:
            vertex = simple_model.vertex.vertex
            indies = simple_model.faces.faces

            self.update_model_data(vertex, indies)

        print("Models count is ", len(simple_models_list))

    def update_model_data(self, points, faces):
        points = list(ModelTransformToBlender.flatten(points))
        faces = list(ModelTransformToBlender.flatten(faces))

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

    @staticmethod
    def flatten(list_obj):
        for item in list_obj:
            if isinstance(item, Iterable):
                for x in ModelTransformToBlender.flatten(item):
                    yield x
            else:
                yield item
