bl_info = {
    "name": "SkeleSwap",
    "blender": (2, 83, 0),
    "category": "Rigging",
    "description": "Replaces the skeleton of a skeletal mesh to the armature of an other mesh, and some other stuff...we will see",
    "author": "UncleJester",
    "version": (1, 0, 0),
}


from . import skeleswap
from . import create_bone_mapping
from . import create_transform_map
from . import create_skeleswap_template
from . import create_unreal_control_rig
from .utils import initialize_persistent_data_store, reset_persistent_data_store_cache

def register():
    initialize_persistent_data_store()
    skeleswap.register()
    create_bone_mapping.register()
    create_transform_map.register()
    create_skeleswap_template.register()
    create_unreal_control_rig.register()

def unregister():
    create_unreal_control_rig.unregister()
    create_skeleswap_template.unregister()
    create_transform_map.unregister()
    create_bone_mapping.unregister()
    skeleswap.unregister()
    reset_persistent_data_store_cache()

if __name__ == "__main__":
    register()
