import math
import bpy
import os
from mathutils import Matrix, Vector
from .general_bone_utils import find_mirror_bone_name, remove_connected_relation
from .dev_utils import debug_print

def normalize_matrix(matrix):
    rotation = matrix.to_3x3().normalized()
    return rotation.to_4x4() @ Matrix.Translation(matrix.to_translation())


def rotate_bone(armature, bone_name, axis, degrees, globalAxis=False, mirror=False):
    debug_print(f"BoneTransformUtils-RotateBone: Rotating {bone_name}, of the armature {armature.name}, on the {axis} axis, by {degrees} degrees")
    bpy.context.view_layer.objects.active = armature
    if bpy.context.object.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    
    pose_bones = armature.pose.bones

    if bone_name not in pose_bones:
        raise ValueError(f"In Rotate Bone: Bone Name: '{bone_name}', could not be found within the the bones of the provided armature: {armature}")

    if axis not in ["X", "Y", "Z"]:
        raise ValueError(f"In Rotate Bone: Invalid rotation axis '{axis}' given for bone '{bone_name}'")
    
    bone = pose_bones[bone_name]
    debug_print(f"BoneTransformUtils-RotateBone: Current rotation of {bone_name} is {bone.rotation_euler}")
    radians = math.radians(degrees)
    rotation = [0, 0, 0]

    if globalAxis:
        rotation["XYZ".index(axis)] = radians
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = [sum(x) for x in zip(bone.rotation_euler, rotation)]
    else:
        bone.rotation_mode = "XYZ"
        bone.rotation_euler.rotate_axis(axis, radians)
    debug_print(f"BoneTransformUtils-RotateBone: Rotation of {bone_name} after rotating is {bone.rotation_euler}")
    
    if mirror: #TBD Fix the mirror!!!!! Currently it only works if the the target of the rotation is the unreal skeleton, and its bones are flipped on the opposite axis. normal skeleton's bone would just rotate the opposite directon when mirrored
        mirror_bone_name = find_mirror_bone_name(armature, bone_name)
        debug_print(f"BoneTransformUtils-RotateBone->Mirror: Mirrored Bone Name: {mirror_bone_name}")
        if mirror_bone_name:
            mirror_bone = pose_bones[mirror_bone_name]
            if not globalAxis:
                mirror_bone.rotation_mode = 'XYZ'
                mirror_bone.rotation_euler.rotate_axis(axis, radians)
            else:
                mirror_rotation = rotation.copy()
                mirror_bone.rotation_mode = 'XYZ'
                mirror_bone.rotation_euler = [sum(x) for x in zip(mirror_bone.rotation_euler, mirror_rotation)]
        else:
            mirror = False
    return {"axis": axis, "degrees": degrees*-1, "bone_name": bone_name, "armature": armature, "mirror": mirror, "global_axis": globalAxis}

def spread_bones(target_armature, source_armature, source_bone_range, target_bone_range): # DONT USE, DOESNT WORK. TBD: Fix it 
    try:

        if not source_armature or not target_armature:
            raise ValueError(f"Armature not found.")

        source_bones = [source_armature.pose.bones.get(b) for b in source_bone_range]
        if None in source_bones:
            raise ValueError(f"One or more bones in source_bone_range '{source_bone_range}' do not exist in armature '{source_armature}'.")


        target_bones = [target_armature.pose.bones.get(b) for b in target_bone_range]
        if None in target_bones:
            raise ValueError(f"One or more bones in target_bone_range '{target_bone_range}' do not exist in armature '{target_armature}'.")

        source_head = source_bones[0].head
        source_tail = source_bones[-1].tail
        source_distance = (source_tail - source_head).length

        target_positions = [bone.head.copy() for bone in target_bones]
        target_total_distance = (target_positions[-1] - target_positions[0]).length
        relative_offsets = [(pos - target_positions[0]).length / target_total_distance for pos in target_positions]

        new_positions = []
        for ratio in relative_offsets:
            new_position = target_positions[0] + (source_distance * ratio) * (target_positions[-1] - target_positions[0]).normalized()
            new_positions.append(new_position)

        for bone, new_position in zip(target_bones, new_positions):
            bone.location = new_position - bone.head


        for bone, pos in zip(target_bones, new_positions):
            print(f"Bone '{bone.name}' -> New Position: {pos}")

    except Exception as e:
        print(f"Error in spread_bones: {e}")
        raise


def match_edit_bone_pos(target_armature, source_armature, target_bone_name, source_bone_name):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = source_armature
    bpy.ops.object.mode_set(mode='EDIT')
    source_edit_bones = source_armature.data.edit_bones
    source_bone = source_edit_bones[source_bone_name]
    source_head = source_bone.head.copy()
    source_head_global = source_armature.matrix_world @ source_bone.head

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = target_armature

    bpy.ops.object.mode_set(mode='EDIT')
    target_edit_bones = target_armature.data.edit_bones


    if target_bone_name not in target_edit_bones:
        raise ValueError(f"In MatchEditBonePos: Error: Bone '{target_bone_name}' not found in the armature '{target_armature.name}'.")


    target_bone = target_edit_bones[target_bone_name]
    debug_print(f"BoneTransformUtils-MatchEditBonePos: Target_bone desired position:  {source_head}")
    debug_print(f"BoneTransformUtils-MatchEditBonePos: Target_bone original position:  {target_bone.head}, {target_bone.tail}")

    source_head_local = target_armature.matrix_world.inverted() @ source_head_global

    offset = source_head_local - target_bone.head # Using offset instead of just matching the bone positions to avoid messing with the rotation/orientation of the bone, as that breaks the ue5 skeleton
    debug_print(f"BoneTransformUtils-MatchEditBonePos: Offset to move bone by:  {offset}")
    
    move_edit_bone(target_armature, target_bone_name, offset)
    debug_print(f"BoneTransformUtils-MatchEditBonePos: target_bone new position: {target_bone.head}, {target_bone.tail}")
    return {"target_armature": target_armature, "target_bone_name": target_bone_name, "offset": offset*-1}

def move_edit_bone(target_armature, target_bone_name, offset):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='EDIT')
    target_edit_bones = target_armature.data.edit_bones

    if target_bone_name not in target_edit_bones:
        raise ValueError(f"In MoveEditBone: Error: Bone '{target_bone_name}' not found in the armature '{target_armature.name}'.")

    
    target_bone = target_edit_bones[target_bone_name]
    debug_print(f"BoneTransformUtils-MoveEditBone: target_bone original position: {target_bone.head}, {target_bone.tail}")
    
    target_bone.head += offset
    target_bone.tail += offset
    bpy.ops.object.mode_set(mode='POSE')

def match_pose_bone_head_pos(target_armature, source_armature, target_bone_name, source_bone_name, foot_z_location = None):
    if target_armature.type != 'ARMATURE' or source_armature.type != 'ARMATURE':
        debug_print(f"BoneTransformUtils-MatchPoseBoneHeadPos: Source or Target armature is invalid. target: {target_armature}, source: {source_armature}")
        raise ValueError(f"In MatchPoseBoneHeadPos: Error: Source or Target armature is invalid")

    if bpy.context.view_layer.objects.active != target_armature:
        bpy.context.view_layer.objects.active = target_armature
        bpy.ops.object.mode_set(mode='POSE')
    
    if bpy.context.view_layer.objects.active != source_armature:
        bpy.context.view_layer.objects.active = source_armature
        bpy.ops.object.mode_set(mode='POSE')

    new_head, new_tail = get_bone_positions_from_armature(source_armature, source_bone_name)
    debug_print(f'BoneTransformUtils-MatchPoseBoneHeadPos: Bone location for the transform (new_head) for the bone {target_bone_name}: {new_head}')
    original_bone = target_armature.pose.bones.get(target_bone_name)
    original_head = original_bone.head.copy() # This is the matrix value of the original position of the bone, so we can use it later to revert the change
    debug_print(f'BoneTransformUtils-MatchPoseBoneHeadPos: Bone location for the revert transform (original_head) for the bone {target_bone_name}: {original_head}')
    debug_print(f'BoneTransformUtils-MatchPoseBoneHeadPos: Now matching bone locations of {target_bone_name} at {original_head}, to {source_bone_name} at {new_head}')
    
    move_pose_bone(target_armature, target_bone_name, new_head, foot_z_location)

    return { "previous_head_position" : original_head, "armature": target_armature, "bone_name": target_bone_name, "foot_z_location": foot_z_location }


def chain_pose_bone_position(armature, bone_to_move, bone_to_move_to):
    if armature.type != 'ARMATURE':
        print("object must be armatures.")
        raise ValueError(f"In ChainPoseBones: Armature is not valid, please make sure to select the target armature")

    debug_print(f"BoneTransformUtils-ChainPoseBones: Bone to move: {bone_to_move}, Bone to move to: {bone_to_move_to}, Armature: {armature.name}")
    
    if bpy.context.view_layer.objects.active != armature:
        bpy.ops.object.mode_set(mode='POSE')

    head_position, tail_position = get_bone_positions_from_armature(armature, bone_to_move_to)
    original_bone = armature.pose.bones.get(bone_to_move)
    
    
    if not original_bone:
        raise ValueError(f"In ChainPoseBones: Target Bone {bone_to_move}, not found in armature: {armature.name}")
    original_head = original_bone.head.copy()
    move_pose_bone(armature, bone_to_move, tail_position)
    
    return { "previous_head_position" : original_head, "armature": armature, "bone_name": bone_to_move }

def get_bone_positions_from_armature(armature, bone_name):
    if not armature or armature.type != 'ARMATURE':
        print(f"Armature '{armature.name}' not found or not valid.")
        return None, None

    bone = armature.data.bones.get(bone_name)
    if not bone:
        print(f"Bone '{bone_name}' not found in armature '{armature.name}'.")
        return None, None

    bone_head_world = armature.matrix_world @ bone.head_local
    bone_tail_world = armature.matrix_world @ bone.tail_local
    
    print(f"location of the {bone_name}: {bone_head_world}")
    return bone_head_world, bone_tail_world

def move_pose_bone(armature, bone_name, new_head, foot_head_Z=None):
    if not armature or armature.type != 'ARMATURE':
        print(f"Armature '{armature.name}' not found or not valid.")
        return

    pose_bone = armature.pose.bones.get(bone_name)
    if not pose_bone:
        print(f"Pose bone '{bone_name}' not found in armature '{armature.name}'.")
        return

    if bpy.context.object.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')

    remove_connected_relation(armature, bone_name)
    
    if "foot" in bone_name and foot_head_Z is not None:
        print(f'moving foot from {pose_bone.head}, to {new_head}')
        translation_vector = new_head - pose_bone.head
        translation_vector.z = foot_head_Z - pose_bone.head.z
        translation_matrix = Matrix.Translation(translation_vector)
        pose_bone.matrix = translation_matrix @ pose_bone.matrix
        print(f"{bone_name} is now at {pose_bone.matrix}")


    else:
        print(f'Moving bone, {bone_name}, from {pose_bone.head}, to {new_head}')
        translation_matrix = Matrix.Translation(new_head - pose_bone.head)
        pose_bone.matrix = translation_matrix @ pose_bone.matrix

    bpy.context.view_layer.update()


def match_pose_bone_orientation(target_armature, source_armature, target_bone_name, source_bone_name, effectRoll=False, UE_right=False):
    if bpy.context.view_layer.objects.active != target_armature:
        bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    target_bone = target_armature.pose.bones.get(target_bone_name)
    source_bone = source_armature.pose.bones.get(source_bone_name)

    if not target_bone or not source_bone:
        print(f"Bone {target_bone_name} or {source_bone_name} not found in the respective armatures.")
        return


    if target_bone.constraints:
        print(f"Warning: {target_bone_name} has constraints, which may prevent proper alignment.")

    source_head_world = source_armature.matrix_world @ source_bone.head
    source_tail_world = source_armature.matrix_world @ source_bone.tail
    target_head_world = target_armature.matrix_world @ target_bone.head


    source_direction = (source_tail_world - source_head_world).normalized()
    
    if UE_right: # Some of the epic's skeleton's bones are flipped, which means the orientation needs to be flipped as well
        source_direction = -source_direction 
    target_direction = (target_bone.tail - target_bone.head).normalized().copy()
    
    orient_bone(target_armature, target_bone_name, source_direction, effectRoll)

    print(f"Aligned {target_bone_name} to {source_bone_name} successfully.")
    return {"orientation": target_direction, "armature": target_armature, "bone_name": target_bone_name, "effect_roll": effectRoll} # This is the original direction of the bone, it can be used later to revert the orientation back to the original

def orient_bone(armature, bone_name, orientation, effectRoll=False):
    bone = armature.pose.bones.get(bone_name)
    target_head_world = armature.matrix_world @ bone.head
    target_direction = (bone.tail - bone.head).normalized()
    
    desired_direction = orientation

    rotation_to_align = target_direction.rotation_difference(desired_direction).to_matrix().to_4x4()

    target_matrix = armature.matrix_world @ bone.matrix
    aligned_matrix = rotation_to_align @ target_matrix
    aligned_matrix.translation = target_head_world

    if not effectRoll:
        roll_preserved_matrix = aligned_matrix.to_3x3()
        roll_preserved_matrix.col[2] = bone.matrix.to_3x3().col[2]
        aligned_matrix = roll_preserved_matrix.to_4x4()
        aligned_matrix.translation = target_head_world

    bone.matrix = armature.matrix_world.inverted() @ aligned_matrix

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')



def scale_pose_bone(armature, bone_name, scale_value, axis=None, global_axis=False): #TBD Implement Mirror
    if not armature or armature.type != 'ARMATURE':
        print(f"Armature '{armature.name}' not found or not valid.")
        return

    pose_bone = armature.pose.bones.get(bone_name)
    if not pose_bone:
        print(f"Pose bone '{bone_name}' not found in armature '{armature.name}'.")
        return

    bpy.context.view_layer.objects.active = armature
    if bpy.context.object.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')


    bpy.ops.pose.select_all(action='DESELECT')
    pose_bone.bone.select = True

    if axis is None:
        bpy.ops.transform.resize(value=(scale_value, scale_value, scale_value), constraint_axis=(False, False, False))
    else:
        if axis not in ["X", "Y", "Z"]:
            print(f"Invalid scale axis '{axis}' for {bone_name}.")
            return

        constraint_axis = (axis == "X", axis == "Y", axis == "Z")

        if not global_axis:
            bpy.ops.transform.resize(value=(scale_value if axis == "X" else 1,
                                            scale_value if axis == "Y" else 1,
                                            scale_value if axis == "Z" else 1),
                                     constraint_axis=constraint_axis, orient_type='LOCAL')
        else:
            bpy.ops.transform.resize(value=(scale_value if axis == "X" else 1,
                                            scale_value if axis == "Y" else 1,
                                            scale_value if axis == "Z" else 1),
                                     constraint_axis=constraint_axis, orient_type='GLOBAL')

    bpy.context.view_layer.update()
    return {"armature": armature, "bone_name": bone_name, "scale_value": 1/scale_value, "axis": axis, "global_axis": global_axis}

def copy_bone_between_skeletons(source_armature, target_armature, bone_name, bone_to_parent_to):
    if source_armature.type != 'ARMATURE' or target_armature.type != 'ARMATURE':
        raise ValueError("Both source and target objects must be armatures.")

    bpy.context.view_layer.objects.active = source_armature
    bpy.ops.object.mode_set(mode='EDIT')

    source_bone = source_armature.data.edit_bones.get(bone_name)
    if not source_bone:
        raise ValueError(f"Bone '{bone_name}' not found in source armature.")

    bone_props = {
        "head": source_bone.head.copy(),
        "tail": source_bone.tail.copy(),
        "roll": source_bone.roll,
        "matrix": source_bone.matrix.copy()
    }

    bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='EDIT')

    target_bone = target_armature.data.edit_bones.get(bone_to_parent_to)
    if not target_bone:
        raise ValueError(f"Bone '{bone_to_parent_to}' not found in target armature.")

    new_bone = target_armature.data.edit_bones.new(bone_name)

    new_bone.head = bone_props["head"]
    new_bone.tail = bone_props["tail"]
    new_bone.roll = bone_props["roll"]
    new_bone.matrix = bone_props["matrix"]

    new_bone.parent = target_bone

    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Reparented bone '{bone_name}' to '{bone_to_parent_to}' in the target armature.")
