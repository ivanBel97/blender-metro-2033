import bpy, bpy_extras

from .model_transform import ModelTransformToBlender


class ModelImporter(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = "import_4a.model"
    bl_label = "Import 4A Model"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ".model, .mesh"

    filter_glob: bpy.props.StringProperty(
        default="*.model",
        options={'HIDDEN'},
        maxlen=255
    )

    def execute(self, context):
        model_path = self.filepath

        model_importer = ModelTransformToBlender(model_path)
        model_importer.render_model(context)

        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ModelImporter.bl_idname, text='4A Model, Part Model (.model, .mesh)')


def register():
    bpy.utils.register_class(ModelImporter)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ModelImporter)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
