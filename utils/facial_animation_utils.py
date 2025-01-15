import bpy # type: ignore
import os

def link_action(filepath, action_name):
    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        if action_name in data_from.actions:
            data_to.actions.append(action_name)
        else:
            raise ValueError(f"Action '{action_name}' not found in the .blend file.")
    
    return bpy.data.actions.get(action_name)

def link_animation(armature, file_path_for_action, action_name):
    if not armature or armature.type != 'ARMATURE':
        raise ValueError(f"Selected object ({armature}) is not an Armature")
    
    if not os.path.exists(file_path_for_action):
        raise LookupError(f"file path for the animation is not correct. File path: {file_path_for_action}")
    
    try:
        action = link_action(file_path_for_action, action_name)
    
        if action:
            armature.animation_data_create()
            armature.animation_data.action = action
            
            if action.library:
                action.make_local()
                print({'INFO'}, f"Action '{action_name}' is now local.")
            else:
                print({'INFO'}, f"Action '{action_name}' is already local.")
            
            action.library = None
            print({'INFO'}, f"Library unlinked from action: {action_name}")
        else:
            raise NameError(f"Action '{action_name}' not found in the .blend file.")
    
    except Exception as e:
        print(e)
        return {'CANCELLED'}
    
def set_frame_to(frame):
    bpy.context.scene.frame_set(frame)

def convert_frame_to_shapekey(mesh, frame, name_of_shapekey):
    set_frame_to(frame)
    bpy.ops.object.join_shapes()
    # bpy.ops.object.shape_key_add(from_mix=False)

    new_shapekey = mesh.data.shape_keys.key_blocks[-1]
    new_shapekey.name = name_of_shapekey

def convert_animation_to_shapekeys(mesh, shapekey_names):
    for index, name in enumerate(shapekey_names):
        convert_frame_to_shapekey(mesh, index + 1, name)
