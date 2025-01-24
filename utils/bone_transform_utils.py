import math
import bpy # type: ignore
from mathutils import Matrix, Vector # type: ignore
from .general_bone_utils import find_mirror_bone_name, remove_connected_relation
from .dev_utils import debug_print
from .ue_specific_utils import is_flipped_unreal_bone

# TBD: Create a separate function for validating inputs, to get rid of the unholy amount of code duplication in every function when validating armatures/bone_names/etc. 

def normalize_matrix(matrix):
    rotation = matrix.to_3x3().normalized()
    return rotation.to_4x4() @ Matrix.Translation(matrix.to_translation())


def rotate_bone(armature, bone_name, axis, degrees, globalAxis=False, mirror=False): 
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-RotateBone: Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-RotateBone: No Armature Provided")
    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-RotateBone: No Bone Name Provided")
    
    debug_print(f"BoneTransformUtils-RotateBone: Rotating {bone_name}, of the armature {armature.name}, on the {axis} axis, by {degrees} degrees")
    try:
        bpy.context.view_layer.objects.active = armature
        if bpy.context.object.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')

        pose_bones = armature.pose.bones

        if bone_name not in pose_bones:
            raise ValueError(f"In BoneTransformUtils-RotateBone: Bone Name: '{bone_name}', could not be found within the the bones of the provided armature: {armature}")

        if axis not in ["X", "Y", "Z"]:
            raise ValueError(f"In BoneTransformUtils-RotateBone: Invalid rotation axis '{axis}' given for bone '{bone_name}'")

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

        if mirror: #TBD: test if mirror works for both normal and epic skeletons
            debug_print(f"BoneTransformUtils-RotateBone-Mirror: Mirror: True")
            is_epic_skeleton = bpy.context.scene.target_is_epic_skeleton and bpy.context.scene.target_armature == armature
            debug_print(f"BoneTransformUtils-RotateBone-Mirror: is_epic_skeleton: {is_epic_skeleton}")
            mirror_bone_name = find_mirror_bone_name(armature, bone_name)        
            debug_print(f"BoneTransformUtils-RotateBone->Mirror: Mirrored Bone Name: {mirror_bone_name}")
            if mirror_bone_name:
                unreal_mirror = is_epic_skeleton and is_flipped_unreal_bone(mirror_bone_name, is_epic_skeleton)
                mirror_bone = pose_bones[mirror_bone_name]
                mirror_rotation = [0, 0, 0]
                if unreal_mirror:
                    debug_print(f"BoneTransformUtils-RotateBone-Mirror: Target is epic skeleton")
                    if not globalAxis:
                        debug_print(f"BoneTransformUtils-RotateBone-Mirror: Mirroring epic skeleton bone on LOCAL axis")
                        mirror_bone.rotation_mode = 'XYZ'
                        mirror_bone.rotation_euler.rotate_axis(axis, radians)
                    else:
                        debug_print(f"BoneTransformUtils-RotateBone-Mirror: Mirroring epic skeleton bone on GLOBAL axis")
                        mirror_rotation = rotation.copy()
                        mirror_bone.rotation_mode = 'XYZ'
                        mirror_bone.rotation_euler = [sum(x) for x in zip(mirror_bone.rotation_euler, mirror_rotation)]
                else:
                    debug_print(f"BoneTransformUtils-RotateBone-Mirror: Target is NOT epic skeleton")
                    if not globalAxis:
                        mirror_bone.rotation_mode = 'XYZ'
                        mirror_bone.rotation_euler.rotate_axis(axis, radians) # Wut? When it is -radians as it should be, it doesnt mirror properly....WHAT? WHY IS MIRROR ON ROTATE BONE IS THE FEATURE  HAVE TO SPEND THE MOST TIME ON? WHY?!?!?!
                    else:
                        mirror_rotation["XYZ".index(axis)] = radians # Wut?
                        mirror_bone.rotation_mode = 'XYZ'
                        mirror_bone.rotation_euler = [sum(x) for x in zip(mirror_bone.rotation_euler, mirror_rotation)]
            else:
                mirror = False
        return {"axis": axis, "degrees": degrees*-1, "bone_name": bone_name, "armature": armature, "mirror": mirror, "global_axis": globalAxis}
    except Exception as e:
        raise RuntimeError(f"In BoneTransformUtils-RotateBone: Could not rotate bone. Error: {e}")

def match_edit_bone_pos(target_armature, source_armature, target_bone_name, source_bone_name):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: No Target Armature Provided")    
    if not target_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: No Target Bone Name Provided")
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: No Source Armature Provided")    
    if not source_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchEditBonePos: No Source Bone Name Provided")
    
    try:
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
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MatchEditBonePos: Could not Match Edit Bone Position. Error: {e}") 

def move_edit_bone(target_armature, target_bone_name, offset):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MoveEditBone: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MoveEditBone: No Target Armature Provided")    
    if not target_bone_name:
        raise ValueError(f"In BoneTransformUtils-MoveEditBone: No Target Bone Name Provided")
    try:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = target_armature
        bpy.ops.object.mode_set(mode='EDIT')
        target_edit_bones = target_armature.data.edit_bones

        if target_bone_name not in target_edit_bones:
            raise ValueError(f"In BoneTransformUtils-MoveEditBone: Error: Bone '{target_bone_name}' not found in the armature '{target_armature.name}'.")


        target_bone = target_edit_bones[target_bone_name]
        debug_print(f"BoneTransformUtils-MoveEditBone: target_bone original position: {target_bone.head}, {target_bone.tail}")

        target_bone.head += offset
        target_bone.tail += offset
        bpy.ops.object.mode_set(mode='POSE')
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MoveEditBone: Could not Match Edit Bone Position. Error: {e}") 

def match_pose_bone_head_pos(target_armature, source_armature, target_bone_name, source_bone_name, foot_z_location = None):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: No Target Armature Provided")    
    if not target_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: No Target Bone Name Provided")
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: No Source Armature Provided")    
    if not source_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: No Source Bone Name Provided")
    
    try:
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
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MatchPoseBoneHeadPos: Could not Match Pose Bone Head Position. Error: {e}") 

def match_edit_bone_z_location(target_armature, source_armature, target_bone_name, source_bone_name):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: No Target Armature Provided")    
    if not target_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: No Target Bone Name Provided")
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: No Source Armature Provided")    
    if not source_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: No Source Bone Name Provided")

    try:
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = source_armature
        bpy.ops.object.mode_set(mode='EDIT')
        source_edit_bones = source_armature.data.edit_bones
        source_bone = source_edit_bones[source_bone_name]
        source_head_global = source_armature.matrix_world @ source_bone.head

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.context.view_layer.objects.active = target_armature
        bpy.ops.object.mode_set(mode='EDIT')
        target_edit_bones = target_armature.data.edit_bones

        if target_bone_name not in target_edit_bones:
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneZLocation: Error: Bone '{target_bone_name}' not found in the armature '{target_armature.name}'.")

        target_bone = target_edit_bones[target_bone_name]
        source_head_local = target_armature.matrix_world.inverted() @ source_head_global

        offset_z = source_head_local.z - target_bone.head.z

        offset = Vector((0.0, 0.0, offset_z))  # Create an offset vector with only the Z component
        debug_print(f"BoneTransformUtils-MatchEditBoneZLocation: Offset to move bone by on Z-axis: {offset_z}")

        move_edit_bone(target_armature, target_bone_name, offset)
        debug_print(f"BoneTransformUtils-MatchEditBoneZLocation: target_bone new position: {target_bone.head}, {target_bone.tail}")
        return {"target_armature": target_armature, "target_bone_name": target_bone_name, "offset": offset*-1}
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MatchEditBoneZLocation: Could not Match Edit Bone Z Position. Error: {e}") 


def chain_pose_bone_position(armature, bone_to_move, bone_to_move_to):
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-ChainPoseBones: Armature Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-ChainPoseBones: No Armature Provided")    
    if not bone_to_move:
        raise ValueError(f"In BoneTransformUtils-ChainPoseBones: No Bone to Move Provided")
    if not bone_to_move_to:
        raise ValueError(f"In BoneTransformUtils-ChainPoseBones: No Bone to Move to Provided")

    debug_print(f"BoneTransformUtils-ChainPoseBones: Bone to move: {bone_to_move}, Bone to move to: {bone_to_move_to}, Armature: {armature.name}")
    try:
        if bpy.context.view_layer.objects.active != armature:
            bpy.ops.object.mode_set(mode='POSE')

        head_position, tail_position = get_bone_positions_from_armature(armature, bone_to_move_to)
        original_bone = armature.pose.bones.get(bone_to_move)


        if not original_bone:
            raise ValueError(f"In ChainPoseBones: Target Bone {bone_to_move}, not found in armature: {armature.name}")
        original_head = original_bone.head.copy()
        move_pose_bone(armature, bone_to_move, tail_position)

        return { "previous_head_position" : original_head, "armature": armature, "bone_name": bone_to_move }
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-ChainPoseBones: Could not chain pose bones. Error: {e}") 

def get_bone_positions_from_armature(armature, bone_name):
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-GetBonePositionsFromArmature: Armature Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-GetBonePositionsFromArmature: No Armature Provided")    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-GetBonePositionsFromArmature: No Bone to Move Provided")

    bone = armature.data.bones.get(bone_name)
    
    if not bone:
        raise ValueError(f"In BoneTransformUtils-GetBonePositionsFromArmature: Given bone, {bone_name} doesn't exist in armature {armature.name}")

    try:
        bone_head_world = armature.matrix_world @ bone.head_local
        bone_tail_world = armature.matrix_world @ bone.tail_local

        debug_print(f"location of the {bone_name}: {bone_head_world}")
        return bone_head_world, bone_tail_world
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-GetBonePositionsFromArmature: Could not get bone positions. Error: {e}") 

def move_pose_bone(armature, bone_name, new_head, foot_head_Z=None):
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-MovePoseBone: Armature Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MovePoseBone: No Armature Provided")    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-MovePoseBone: No Bone to Move Provided")


    pose_bone = armature.pose.bones.get(bone_name)
    if not pose_bone:
        raise ValueError(f"In BoneTransformUtils-MovePoseBone: Given bone, {bone_name} doesn't exist in armature {armature.name}")

    if bpy.context.object.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')

    try:
        remove_connected_relation(armature, bone_name)

        if "foot" in bone_name and foot_head_Z is not None:
            debug_print(f'moving foot from {pose_bone.head}, to {new_head}')
            translation_vector = new_head - pose_bone.head
            translation_vector.z = foot_head_Z - pose_bone.head.z
            translation_matrix = Matrix.Translation(translation_vector)
            pose_bone.matrix = translation_matrix @ pose_bone.matrix
            debug_print(f"{bone_name} is now at {pose_bone.matrix}")


        else:
            debug_print(f'Moving bone, {bone_name}, from {pose_bone.head}, to {new_head}')
            translation_matrix = Matrix.Translation(new_head - pose_bone.head)
            pose_bone.matrix = translation_matrix @ pose_bone.matrix

        bpy.context.view_layer.update()
    
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MovePoseBone: Could not move pose bone. Error: {e}") 

def match_pose_bone_orientation(target_armature, source_armature, target_bone_name, source_bone_name, UE_right=False):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: No Target Armature Provided")    
    if not target_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: No Target Bone Name Provided")
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: No Source Armature Provided")    
    if not source_bone_name:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: No Source Bone Name Provided")

    if bpy.context.view_layer.objects.active != target_armature:
        bpy.context.view_layer.objects.active = target_armature
    bpy.ops.object.mode_set(mode='POSE')

    target_bone = target_armature.pose.bones.get(target_bone_name)
    source_bone = source_armature.pose.bones.get(source_bone_name)

    if not target_bone:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: Target bone, {target_bone_name} does not exist in target armature, {target_armature.name}")
    if not source_bone:
        raise ValueError(f"In BoneTransformUtils-MatchPoseBoneOrientation: Source bone, {source_bone_name} does not exist in source armature, {source_armature.name}")

    try:
        if target_bone.constraints:
            debug_print(f"Warning: {target_bone_name} has constraints, which may prevent proper alignment.")

        source_head_world = source_armature.matrix_world @ source_bone.head
        source_tail_world = source_armature.matrix_world @ source_bone.tail
        target_head_world = target_armature.matrix_world @ target_bone.head


        source_direction = (source_tail_world - source_head_world).normalized()

        if UE_right: # Some of the epic's skeleton's bones are flipped, which means the orientation needs to be flipped as well
            source_direction = -source_direction 
        target_direction = (target_bone.tail - target_bone.head).normalized().copy()

        orient_bone(target_armature, target_bone_name, source_direction)

        debug_print(f"Aligned {target_bone_name} to {source_bone_name} successfully.")
        return {"orientation": target_direction, "armature": target_armature, "bone_name": target_bone_name} # This is the original direction of the bone, it can be used later to revert the orientation back to the original
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MatchPoseBoneOrientation: Could not match pose bone orientation. Error: {e}") 

def orient_bone(armature, bone_name, orientation):
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-OrientBone: Armature Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-OrientBone: No Armature Provided")    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-OrientBone: No Bone to Move Provided")
    
    try:
        bone = armature.pose.bones.get(bone_name)
        target_head_world = armature.matrix_world @ bone.head
        target_direction = (bone.tail - bone.head).normalized()
        desired_direction = orientation
        rotation_to_align = target_direction.rotation_difference(desired_direction).to_matrix().to_4x4()
        target_matrix = armature.matrix_world @ bone.matrix
        aligned_matrix = rotation_to_align @ target_matrix
        aligned_matrix.translation = target_head_world

        """ if not effectRoll:
            roll_preserved_matrix = aligned_matrix.to_3x3()
            roll_preserved_matrix.col[2] = bone.matrix.to_3x3().col[2]
            aligned_matrix = roll_preserved_matrix.to_4x4()
            aligned_matrix.translation = target_head_world"""
        
        bone.matrix = armature.matrix_world.inverted() @ aligned_matrix

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-OrientBone: Could not orient bone. Error: {e}") 

def scale_pose_bone(armature, bone_name, scale_value, axis=None, global_axis=False): #TBD Implement Mirror
    if not armature or armature.type != "ARMATURE":
        if armature:
            raise ValueError(f"In BoneTransformUtils-ScalePoseBone: Armature Input is type: {armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-ScalePoseBone: No Armature Provided")    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-ScalePoseBone: No Bone to Move Provided")

    pose_bone = armature.pose.bones.get(bone_name)
    if not pose_bone:
        raise ValueError(f"In BoneTransformUtils-ScalePoseBone: Source bone, {bone_name} does not exist in armature, {armature.name}")
    
    try:
        bpy.context.view_layer.objects.active = armature
        if bpy.context.object.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')


        bpy.ops.pose.select_all(action='DESELECT')
        pose_bone.bone.select = True

        if axis is None:
            bpy.ops.transform.resize(value=(scale_value, scale_value, scale_value), constraint_axis=(False, False, False))
        else:
            if axis not in ["X", "Y", "Z"]:
                debug_print(f"Invalid scale axis '{axis}' for {bone_name}.")
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
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-ScalePoseBone: Could not scale pose bone. Error: {e}") 

def copy_bone_between_skeletons(source_armature, target_armature, bone_name, bone_to_parent_to):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: No Target Armature Provided")    
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: No Source Armature Provided")
    
    if not bone_name:
        raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: No Bone Name Provided")

    bpy.context.view_layer.objects.active = source_armature
    bpy.ops.object.mode_set(mode='EDIT')

    source_bone = source_armature.data.edit_bones.get(bone_name)
    
    if not source_bone:
        raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: Bone to copy, {bone_name} does not exist in armature, {source_armature.name}")

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
        raise ValueError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: Bone to parent to, {bone_to_parent_to} does not exist in armature, {target_armature.name}")

    try:
        new_bone = target_armature.data.edit_bones.new(bone_name)

        new_bone.head = bone_props["head"]
        new_bone.tail = bone_props["tail"]
        new_bone.roll = bone_props["roll"]
        new_bone.matrix = bone_props["matrix"]

        new_bone.parent = target_bone

        bpy.ops.object.mode_set(mode='OBJECT')

        debug_print(f"Reparented bone '{bone_name}' to '{bone_to_parent_to}' in the target armature.")
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-CopyBoneBetweenSkeletons: Could not copy bone between skeletons. Error: {e}") 


def match_edit_bone_chain_scale(target_armature, source_armature, target_chain, source_chain, onZAxis=False): # TBD: Probably should add some sort of validation that the list of bones are indeed a chain or not
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: No Target Armature Provided")    
    if not target_chain:
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: Target chain is not provided or is an empty list")
    
    if not source_armature or source_armature.type != "ARMATURE":
        if source_armature:
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: Source Armature Input is type: {source_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: No Source Armature Provided")    
    if not source_chain:
        raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: Source chain is not provided or is an empty list")
    try:
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = source_armature
        bpy.ops.object.mode_set(mode='EDIT')
        source_edit_bones = source_armature.data.edit_bones
        debug_print(f"BoneTransformUtils-MatchEditBoneChainScale:\n Target Armature: {target_armature.name} \n Source Armature: {source_armature.name} \n Target Bone Chain: {target_chain} \n Source Bone Chain: {source_chain}")

        if not all(bone_name in source_edit_bones for bone_name in source_chain):
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: One or more bones in source_chain {source_chain} do not exist in the source_armature, {source_armature}.")

        source_length = (source_edit_bones[source_chain[-1]].tail - source_edit_bones[source_chain[0]].head).z if onZAxis else (source_edit_bones[source_chain[-1]].tail - source_edit_bones[source_chain[0]].head).length
        debug_print(f"BoneTransformUtils-MatchEditBoneChainScale: Source Length: {source_length}")

        bpy.context.view_layer.objects.active = target_armature
        bpy.ops.object.mode_set(mode='EDIT')
        target_edit_bones = target_armature.data.edit_bones

        if not all(bone_name in target_edit_bones for bone_name in target_chain):
            raise ValueError(f"In BoneTransformUtils-MatchEditBoneChainScale: One or more bones in target_chain {target_chain} do not exist in the target_armature, {target_armature}.")

        target_length = (target_edit_bones[target_chain[-1]].tail - target_edit_bones[target_chain[0]].head).z if onZAxis else (target_edit_bones[target_chain[-1]].tail - target_edit_bones[target_chain[0]].head).length
        debug_print(f"BoneTransformUtils-MatchEditBoneChainScale: Target Original Length: {target_length}")


        if target_length == 0:
            raise ValueError("Target chain length is zero, cannot scale.")

        scale_factor = source_length / target_length
        debug_print(f"BoneTransformUtils-MatchEditBoneChainScale: Calculated Scale Factor: {scale_factor}")

        scale_edit_bone_chain(target_armature, target_chain, scale_factor)

        bpy.ops.object.mode_set(mode='OBJECT')
        return {"target_chain": target_chain, "scale_factor": scale_factor, "target_armature": target_armature}
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-MatchEditBoneChainScale: Could not match edit bone chain scale. Error: {e}") 

def scale_edit_bone_chain(target_armature, target_chain, scale_factor, onZAxis=False):
    if not target_armature or target_armature.type != "ARMATURE":
        if target_armature:
            raise ValueError(f"In BoneTransformUtils-ChainEditBoneScale: Target Armature Input is type: {target_armature.type}. Excpected type ARMATURE")
        raise ValueError(f"In BoneTransformUtils-ChainEditBoneScale: No Target Armature Provided")    
    if not target_chain:
        raise ValueError(f"In BoneTransformUtils-ChainEditBoneScale: Target chain is not provided or is an empty list")
    
    target_edit_bones = target_armature.data.edit_bones
    
    try:
        bpy.ops.armature.select_all(action='DESELECT')
        for bone_name in target_chain:
            debug_print(f"BoneTransformUtils-ChainEditBoneScale: Selecting edit bone: {target_edit_bones[bone_name]}")
            target_edit_bones[bone_name].select = True

        bpy.context.view_layer.objects.active = target_armature
        bpy.context.object.data.edit_bones.active = target_edit_bones[target_chain[0]]
        debug_print(f"BoneTransformUtils-ChainEditBoneScale: Made First Bone in the chain Active: {target_edit_bones[target_chain[0]]}")

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT') # Yet again, selection works weird when trying it via script. To achieve the same result as if selecting and making something active in the view port by hand. we have to switch to obj mode after the selection is done, then switch back to edit mode. no clue why

        if onZAxis:
            debug_print(f"BoneTransformUtils-ChainEditBoneScale: Scaling on Z axis")
            bpy.ops.transform.resize(value = (1, 1, scale_factor))
        else: 
            debug_print(f"BoneTransformUtils-ChainEditBoneScale: Scaling uniformly")
            bpy.ops.transform.resize(value = (scale_factor, scale_factor, scale_factor))
    except Exception as e:
       raise RuntimeError(f"In BoneTransformUtils-ChainEditBoneScale: Could not scale edit bone chain. Error: {e}")