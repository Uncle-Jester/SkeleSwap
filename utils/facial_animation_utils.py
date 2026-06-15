import bpy # type: ignore
import os
from .dev_utils import validate

def link_action(filepath, action_name):
    validate(
        [filepath, action_name],
        ["str", "str"],
        stack_location="FacialAnimationUtils-LinkAction",
        input_identifier_strings=["filepath", "action_name"],
    )
    print(f"FacialAnimationUtils-LinkAction: Attemting to link action: {action_name}")
    with bpy.data.libraries.load(filepath, link=True) as (data_from, data_to):
        resolved_action_name = action_name if action_name in data_from.actions else None
        if not resolved_action_name:
            case_insensitive_matches = [
                name
                for name in data_from.actions
                if name.casefold() == action_name.casefold()
            ]
            if len(case_insensitive_matches) == 1:
                resolved_action_name = case_insensitive_matches[0]
                print(
                    "FacialAnimationUtils-LinkAction: "
                    f"Using case-insensitive action match, {resolved_action_name}"
                )

        if not resolved_action_name:
            raise ValueError(f"Action '{action_name}' not found in the .blend file.")

        print(f"FacialAnimationUtils-LinkAction: Action in target file exists")
        data_to.actions.append(resolved_action_name)
        print(f"FacialAnimationUtils-LinkAction: Action, {resolved_action_name}, appended")
    
    return data_to.actions[-1]

def link_animation(armature, file_path_for_action, action_name):
    validate(
        [armature, file_path_for_action, action_name],
        ["ARMATURE", "str", "str"],
        stack_location="FacialAnimationUtils-LinkAnimation",
        input_identifier_strings=["armature", "file_path_for_action", "action_name"],
    )
    
    if not os.path.exists(file_path_for_action):
        raise LookupError(f"file path for the animation is not correct. File path: {file_path_for_action}")
    
    try:
        action = link_action(file_path_for_action, action_name)
        print(f"FacialAnimationUtils-LinkAnimation: Action, {action_name}, from {file_path_for_action}, has been linked")
    
        if action:
            print(f"FacialAnimationUtils-LinkAnimation: Action is valid, attempting to create animation data")
            armature.animation_data_create()
            armature.animation_data.action = action
            print(f"FacialAnimationUtils-LinkAnimation: Animation data created")
            
            if action.library:
                print(f"FacialAnimationUtils-LinkAnimation: Action library exists. Attempting to make it local")
                action.make_local(clear_proxy=True)
                print(f"FacialAnimationUtils-LinkAnimation: Action has been made local")

            if (
                hasattr(action, "slots")
                and action.slots
                and hasattr(armature.animation_data, "action_slot")
                and armature.animation_data.action_slot is None
            ):
                action_slot = next(
                    (
                        slot
                        for slot in action.slots
                        if slot.target_id_type == 'OBJECT'
                    ),
                    action.slots[0],
                )
                armature.animation_data.action_slot = action_slot
                print(
                    "FacialAnimationUtils-LinkAnimation: "
                    f"Assigned action slot, {action_slot.identifier}"
                )
            
            print({'INFO'}, f"Library unlinked from action: {action_name}")
        else:
            raise NameError(f"Action '{action_name}' not found in the .blend file.")
    
    except Exception as e:
        print(f"An Error occured when trying to link animation. Error: {e}")
        raise RuntimeError(f"Could not link animation '{action_name}'. Error: {e}") from e

    return {'FINISHED'}
    
def set_frame_to(frame):
    bpy.context.scene.frame_set(frame)

def convert_frame_to_shapekey(mesh, frame, name_of_shapekey):
    set_frame_to(frame)
    bpy.ops.object.join_shapes()

    new_shapekey = mesh.data.shape_keys.key_blocks[-1]
    new_shapekey.name = name_of_shapekey

def convert_animation_to_shapekeys(mesh, shapekey_names):
    for index, name in enumerate(shapekey_names):
        convert_frame_to_shapekey(mesh, index + 1, name)

def convert_transform_animation_to_shapekeys(source_mesh, target_mesh, shapekey_names):
    validate(
        [source_mesh, target_mesh, shapekey_names],
        ["MESH", "MESH", "list"],
        stack_location="FacialAnimationUtils-ConvertTransformAnimationToShapekeys",
        input_identifier_strings=["source_mesh", "target_mesh", "shapekey_names"],
    )

    if len(source_mesh.data.vertices) != len(target_mesh.data.vertices):
        raise ValueError(
            f"Source mesh '{source_mesh.name}' and target mesh '{target_mesh.name}' "
            "must have the same vertex count"
        )

    set_frame_to(1)
    basis_matrix_world_inverse = source_mesh.matrix_world.inverted()

    for index, name in enumerate(shapekey_names):
        set_frame_to(index + 1)
        relative_transform = basis_matrix_world_inverse @ source_mesh.matrix_world
        shape_key = target_mesh.shape_key_add(name=name, from_mix=False)
        shape_key.data.foreach_set(
            "co",
            [
                component
                for vertex in source_mesh.data.vertices
                for component in relative_transform @ vertex.co
            ],
        )
