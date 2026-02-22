import bpy # type: ignore
from .dev_utils import debug_print, validate

def parent_armature(mesh, armature):
    validate(
        [mesh, armature],
        ["MESH", "ARMATURE"],
        stack_location="ArmatureUtils-ParentArmature",
        input_identifier_strings=["mesh", "armature"],
    )
    
    if mesh.parent == armature:
        debug_print(f"ArmatureUtils-ApplyArmature: Armature is already the mesh's parent")
        return
    
    try:
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.parent_set(type='ARMATURE')
        debug_print(f"Parented mesh '{mesh.name}' to armature '{armature.name}'.")
        
    except Exception as e:
        debug_print(f"ArmatureUtils-ApplyArmature: Error: {e}")
        raise RuntimeError(f"In ArmatureUtils-ApplyArmature: Couldn't Parent mesh {mesh.name} to armature, {armature.name} Error: {e}")

def apply_armature(mesh, armature):
    validate(
        [mesh, armature],
        ["MESH", "ARMATURE"],
        stack_location="ArmatureUtils-ApplyArmature",
        input_identifier_strings=["mesh", "armature"],
    )
    
    if mesh.parent != armature:
        raise ValueError(f"In ArmatureUtils-ApplyArmature: Mesh '{mesh.name}' is not parented to the armature '{armature.name}'.")
    
    try:   
        bpy.context.view_layer.objects.active = mesh
        for modifier in mesh.modifiers:
            if modifier.type == 'ARMATURE' and modifier.object == armature:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
                print(f"Applied armature modifier on mesh: {mesh.name}")
                return
        debug_print("ArmatureUtils-ApplyArmature: No armature modifier found to apply.")
    except Exception as e:
        debug_print(f"In ArmatureUtils-ApplyArmature: Error: {e}")
        raise e

def clear_all_armatures(mesh):
    validate(
        [mesh],
        ["MESH"],
        stack_location="ArmatureUtils-ClearAllArmatures",
        input_identifier_strings=["mesh"],
    )
    try:

        armature_modifiers = [mod for mod in mesh.modifiers if mod.type == 'ARMATURE']
        for mod in armature_modifiers:
            debug_print(f"Removing armature modifier: {mod.name} from {mesh.name}")
            mesh.modifiers.remove(mod)

        if mesh.parent and mesh.parent.type == 'ARMATURE':
            debug_print(f"Clearing parent armature: {mesh.parent.name} from {mesh.name}")
            mesh.parent = None

        print(f"All armatures cleared from {mesh.name}.")
    except Exception as e:
        debug_print(f"In ArmatureUtils-ClearAllArmatures: Error: {e}")
        raise e

def delete_armature(armature):
    validate(
        [armature],
        ["ARMATURE"],
        stack_location="ArmatureUtils-DeleteArmature",
        input_identifier_strings=["armature"],
    )
    try:
        bpy.context.view_layer.objects.active = armature
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.ops.object.delete()
    except Exception as e:
        debug_print(f"In ArmatureUtils-DeleteArmature: Error: {e}")
        raise RuntimeError(f"In ArmatureUtils-DeleteArmature: Error: {e}")



def apply_pose_as_rest_pose(armature):
    validate(
        [armature],
        ["ARMATURE"],
        stack_location="ArmatureUtils-ApplyPoseAsRestPose",
        input_identifier_strings=["armature"],
    )
    try:   
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply()
        debug_print(f"Applied pose as the new rest pose for armature: {armature.name}.")
    except Exception as e:
        debug_print(f"In ArmatureUtils-ApplyPoseAsRestPose: Error: {e}")
        raise e


def scale_selected_armature_with_child_meshes(armature, scale_factor=100):
    validate(
        [armature],
        ["ARMATURE"],
        stack_location="ArmatureUtils-ScaleSelectedArmatureWithChildMeshes",
        input_identifier_strings=["armature"],
    )

    try:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        empty = bpy.context.object

        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True)

        children = [child for child in armature.children if child.type == 'MESH']

        for obj in [armature] + children:
            obj.parent = empty

        empty.scale = (scale_factor, scale_factor, scale_factor)

        bpy.ops.object.select_all(action='DESELECT')
        empty.select_set(True)
        for obj in [armature] + children:
            obj.select_set(True)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = armature
        armature.select_set(True) 
        for child in children:
            child.select_set(True)
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

        bpy.data.objects.remove(empty)
    except Exception as e:
        debug_print(f"In ArmatureUtils-ScaleSelectedArmatureWithChildMeshes: Error: {e}")
        raise e

def find_armature_by_name(armature_name):
    validate(
        [armature_name],
        ["str"],
        stack_location="ArmatureUtils-FindArmatureByName",
        input_identifier_strings=["armature_name"],
    )
    armature = bpy.data.objects.get(armature_name)
    try:
        validate(
            [armature],
            ["ARMATURE"],
            stack_location="ArmatureUtils-FindArmatureByName",
            input_identifier_strings=["armature"],
        )
    except ValueError:
        print(f"Armature '{armature_name}' not found. Please Import a UE5 SKM")
        return {'CANCELLED'}
    return armature
