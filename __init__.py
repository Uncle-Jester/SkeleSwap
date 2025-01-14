bl_info = {
    "name": "SkeleSwap",
    "blender": (2, 83, 0),
    "category": "Rigging",
    "description": "Replaces the skeleton of a skeletal mesh to the armature of an other mesh",
    "author": "BrownbusTheJester",
    "version": (1, 0, 0),
}


from . import skeleswap
from . import create_transform_map
from . import create_bone_mapping
from . import create_skeleswap_template

def register():
    skeleswap.register()
    create_transform_map.register()
    create_bone_mapping.register()
    create_skeleswap_template.register()

def unregister():
    skeleswap.unregister()
    create_transform_map.unregister()
    create_bone_mapping.unregister()
    create_skeleswap_template.unregister()

if __name__ == "__main__":
    register()