import math

from .model import *
from .texture_tool import DDSUtils

from typing import List, Iterable

try:
    from bpy_extras import object_utils

    import bmesh
    import bpy
except ImportError:
    bpy = None
    bmesh = None


class ModelTransformToBlender:
    content_path: str
    material_data: List[List[str]]

    points: List[List[tuple]]
    uv_map: List[List[tuple]]
    normals: List[List[tuple]]

    faces: List[List[tuple]]

    def __init__(self, model_path: str):
        res = load_model(model_path)

        self.content_path = model_path[:model_path.find("\\meshes\\")]
        self.content_path = str(self.content_path)

        self.material_data, self.points, self.uv_map, self.normals, self.faces = [list(),
                                                                                  list(),
                                                                                  list(),
                                                                                  list(),
                                                                                  list()]

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
                self.add_mesh("4a_mesh",
                              self.points[i],
                              self.faces[i],
                              self.normals[i],
                              self.uv_map[i],
                              self.material_data[i],
                              context,
                              obj_col)

    def add_mesh(self, name, vertex, faces, normals, uv_map, material_data, context, col):
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(mesh.name, mesh)
        col.objects.link(obj)

        bm = bmesh.new()

        for vert in vertex:
            bm.verts.new(vert)

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

        uv_layer = bm.loops.layers.uv.new('4A_UVMap')

        for face in bm.faces:  # add uv map
            for loop in face.loops:
                uv_coord = uv_map[loop.vert.index]
                loop[uv_layer].uv = (
                    uv_coord[0],
                    1 - uv_coord[1]
                )

        bm.to_mesh(mesh)

        mesh.auto_smooth_angle = math.pi
        mesh.use_auto_smooth = True

        mesh.normals_split_custom_set_from_vertices([
            (
                self.calc_normals(normals[vert.index][0]),  # X normal
                self.calc_normals(normals[vert.index][2]),  # Z normal
                self.calc_normals(normals[vert.index][1])   # Y normal
             ) for vert in bm.verts])

        mesh.update()

        # set material
        self.set_material(obj, material_data[0], material_data[2])

    def calc_normals(self, normal):
        return 2.0 * normal / 255 - 1.0

    def set_material(self, obj, texture_path, material_type):
        texture_path_dds = ""
        texture_path = "{0}\\textures\\{1}.512".format(self.content_path, texture_path)

        if exists(texture_path):
            texture_path_dds = DDSUtils.convert_texture(texture_path)

        if bpy is not None and texture_path_dds != "":
            m_material = bpy.data.materials.new("4a_material")
            m_material.use_nodes = True

            shader = m_material.node_tree.nodes["Principled BSDF"]

            m_texture = m_material.node_tree.nodes.new('ShaderNodeTexImage')
            m_texture.image = bpy.data.images.load(texture_path_dds)

            m_material.node_tree.links.new(shader.inputs['Base Color'], m_texture.outputs['Color'])

            # Add to object
            if obj.data.materials:
                obj.data.materials[0] = m_material
            else:
                obj.data.materials.append(m_material)

    def from_skinned_model(self, skin_model):
        skin_meshes: List[SkinnedMesh] = list(flatten(skin_model.meshes))

        for skin in skin_meshes:
            self.update_model_data(skin.vertex, skin.indies, skin.material, True)

    def from_simple_model(self, h_models):
        simple_models_list: List[SimpleModel] = list(flatten(h_models))

        for simple_model in simple_models_list:
            material = simple_model.material

            vertex = simple_model.vertex.vertex
            indies = simple_model.faces.faces

            self.update_model_data(vertex, indies, material)

    def update_model_data(self, points, faces, material, is_skin=False):
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
                vertex.append((vert.coord.X / scale_factor * -1.0,
                               vert.coord.Z / scale_factor * -1.0,
                               vert.coord.Y / scale_factor
                               ))
                uv.append((
                    vert.uv_coord.X / uv_factor,
                    vert.uv_coord.Y / uv_factor
                ))
            else:
                vertex.append((vert.coord.X * -1.0, vert.coord.Y, vert.coord.Z))
                uv.append((
                    vert.uv_coord.X,
                    vert.uv_coord.Y
                ))

            normal.append((
                ((vert.normal << 16) & 0xFF) / 255.0,
                ((vert.normal << 8) & 0xFF) / 255.0,
                (vert.normal & 0xFF) / 255.0
            )
            )

        for face in faces:
            indies.append((face.X, face.Y, face.Z))

        normal = self.normalize_normal(normal)

        self.material_data.append([material.texture_name, material.shader, material.material_name])

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
