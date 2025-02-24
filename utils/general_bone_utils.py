import bpy # type: ignore
from .bone_mapping_utils import find_side_indicator_in_bone_name, side_indicator_list
from .dev_utils import debug_print

def match_case(base, sample):
    if sample.isupper():
        return base.upper()
    elif sample.islower():
        return base.lower()
    elif sample[0].isupper() and sample[1:].islower():
        return base.capitalize()
    elif sample[-1].isupper() and sample[:-1].islower():
        return base[:-1].lower() + base[-1].upper()
    elif sample[0].isupper() and sample[-1].isupper():
        return base[0].upper() + base[1:-1].lower() + base[-1].upper()
    else:
        return base # I know this is bad and ugly. but i was in a hurry.

def find_mirror_bone_name(armature, bone_name):
    bpy.context.view_layer.objects.active = armature
    if bpy.context.object.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    
    bpy.ops.armature.select_all(action='DESELECT')
    if bone_name in armature.data.edit_bones:
        armature.data.edit_bones[bone_name].select = True
        bpy.context.object.data.edit_bones.active = armature.data.edit_bones[bone_name]
        
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT') ## This back and forth swap is because otherwise the armature.select_mirror doesnt work. No clue why. There seems to be a difference between making a bone selected and active via script and clicking on it

        bpy.ops.armature.select_mirror(only_active=True)
        
        mirrored_bone_name = None
        for bone in armature.data.edit_bones:
            if bone.select:
                mirrored_bone_name = bone.name
                break
        
        if mirrored_bone_name:
            bpy.ops.object.mode_set(mode='POSE')
            return mirrored_bone_name
    else:
        bpy.ops.object.mode_set(mode='POSE')
        debug_print(f"Bone, {bone_name} was not in the bone list: {armature.data.edit_bones}")
    
    bpy.context.view_layer.objects.active = armature
    
    if bpy.context.object.mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')   

    pose_bones = armature.pose.bones
    if bone_name not in pose_bones:
        debug_print(f"Bone '{bone_name}' not found in pose bones.")
        return None

    if mirrored_bone_name:
        debug_print(f"Mirrored bone for '{bone_name}' is '{mirrored_bone_name}'")
    else:
        debug_print(f"GeneralBoneUtils-FindMirrorBoneName: No mirrored bone found for '{bone_name}' using blenders inbuilt mirror bone finder. Trying simple side_indicator_swap")
        side_indicator = find_side_indicator_in_bone_name(bone_name, side_indicator_list)
        if side_indicator is not None:
            opposite_side_indicator_index = side_indicator_list[side_indicator["list_key"]].index(side_indicator["substring"].lower())
            opposite_side_list_key = "left" if side_indicator["list_key"] == "right" else "right"
            opposite_side_indicator = side_indicator_list[opposite_side_list_key][opposite_side_indicator_index]
            opposite_side_indicator = match_case(opposite_side_indicator, side_indicator["substring"])
            debug_print("GeneralBoneUtils-FindMirrorBoneName: opposite_side_indicator: {opposite_side_indicator}")
            potential_mirrored_bone_name = bone_name.replace(side_indicator["substring"], opposite_side_indicator) 
            for pose_bone_name in pose_bones.keys():
                if potential_mirrored_bone_name == pose_bone_name:
                    mirrored_bone_name = potential_mirrored_bone_name
                    break

    return mirrored_bone_name

def get_foot_z_location(target_armature, foot_bone_name):
    foot_l = target_armature.pose.bones.get(foot_bone_name)

    if foot_l :
        foot_z_location = foot_l.head.z
        return foot_z_location
    else:
        debug_print(f"GeneralBoneUtils-GetFootZLocation: Foot bone not found in armature. Foot Bone Name: {foot_l}, Armature: {target_armature.name}")
        return None

def remove_connected_relation(armature, bone_name):
    if armature.type != 'ARMATURE':
        raise ValueError(f"In RemoveConnectedRelation: Error: {armature.name} is not an armature.")

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.context.view_layer.objects.active = armature

    if bone_name not in armature.data.bones:
        raise ValueError(f"In RemoveConnectedRelation: Error: Bone '{bone_name}' not found in armature '{armature.name}'.")

    try:
        bpy.ops.object.mode_set(mode='EDIT')
        bone = armature.data.edit_bones.get(bone_name)
        if bone and bone.use_connect:
            bone.use_connect = False
            debug_print(f"GeneralBoneUtils-RemoveConnectedRelation: Unchecked 'Connected' for bone: {bone_name}")
    except Exception as e:
        debug_print(f"GeneralBoneUtils-RemoveConnectedRelation: {e}")
        raise RuntimeError(f"In RemoveConnectedRelation: Failed to remove connection for bone '{bone_name}' in armature '{armature.name}'. Error: {e}")
    finally:
        bpy.ops.object.mode_set(mode='POSE')

def add_copy_location_constraint(armature, bone_to_constraint, bone_to_constraint_to):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    bone = armature.pose.bones.get(bone_to_constraint)
    if not bone:
        debug_print(f"Bone '{bone_to_constraint}' not found.")
        return

    constraint = bone.constraints.new(type='COPY_LOCATION')
    constraint.target = armature
    constraint.subtarget = bone_to_constraint_to
    debug_print(f"Added Copy Location constraint to '{bone_to_constraint}' targeting '{bone_to_constraint_to}'.")


def add_copy_rotation_constraint(armature, bone_to_constraint, bone_to_constraint_to):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')

    bone = armature.pose.bones.get(bone_to_constraint)
    if not bone:
        debug_print(f"Bone '{bone_to_constraint}' not found.")
        return

    constraint = bone.constraints.new(type='COPY_ROTATION')
    constraint.target = armature
    constraint.subtarget = bone_to_constraint_to
    debug_print(f"Added Copy Rotation constraint to '{bone_to_constraint}' targeting '{bone_to_constraint_to}'.")

def apply_bone_constraints(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    bpy.ops.nla.bake(
        frame_start=1, 
        frame_end=1, 
        step=1, 
        only_selected=False, 
        visual_keying=True, 
        clear_constraints=True, 
        use_current_action=True
    )

def rename_bone(armature, bone_name, new_name):

    if armature.type != 'ARMATURE':
        raise ValueError("The provided object is not an armature.")
    
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bone = armature.data.edit_bones.get(bone_name)
    
    if not edit_bone:
        raise ValueError(f"Bone '{bone_name}' not found in armature.")

    edit_bone.name = new_name

    bpy.ops.object.mode_set(mode='OBJECT')
