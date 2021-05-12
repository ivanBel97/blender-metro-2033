bl_info = {
    "name": "BLI2033",
    "description": "Addon for import meshes, models from Metro 2033",
    "author": "ArkYT, Modera",
    "version": (0, 7, 7),
    "blender": (2, 80, 0),
    "location": "File > Import",
    "support": "COMMUNITY",
    "category": "Import Model",
}

try:
    from .model_import import register, unregister
except ImportError:
    pass
