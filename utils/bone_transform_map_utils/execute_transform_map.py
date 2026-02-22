from .. import match_pose_bone_head_pos, match_pose_bone_orientation, chain_pose_bone_position, match_edit_bone_pos, rotate_bone, scale_pose_bone, match_edit_bone_z_location, match_edit_bone_chain_scale, copy_bone_between_armatures
from ..dev_utils import validate

def apply_transform_map(transform_map, foot_z_loc, global_target_armature, global_source_armature):
    validate(
        [transform_map, global_target_armature, global_source_armature],
        ["list", "ARMATURE", "ARMATURE"],
        stack_location="ExecuteTransformMap-ApplyTransformMap",
        input_identifier_strings=["transform_map", "global_target_armature", "global_source_armature"],
    )
    for transform in transform_map:
        transform_type = transform.get("transform_type")
        target_armature_indicator = transform.get("target_armature_indicator")
        source_armature_indicator = transform.get("source_armature_indicator")
        source_bone_name = transform.get("source_bone_name")
        target_bone_name = transform.get("target_bone_name")
        source_chain = transform.get("source_chain")
        target_chain = transform.get("target_chain")
        new_bone_name = transform.get("new_bone_name")
        axis = transform.get("axis")
        transform_value = transform.get("transform_value")
        foot_z_location = foot_z_loc if transform.get("foot_z_location") else None
        unreal_right = transform.get("unreal_right") if transform.get("unreal_right") else False
        mirror =  transform.get("mirror") if transform.get("mirror") else False

        target_armature = (
            global_target_armature if target_armature_indicator == "T"
            else global_source_armature if target_armature_indicator == "S"
            else None
        ) # this is necessary, the target armature of a transform can be the globally saved source_armature. the indicator is there to tell us that the source/target armature of a transform was the saved global/source armature... I am too lazy to change the naming, please forgive me
        source_armature = (
            global_source_armature if source_armature_indicator == "S"
            else global_target_armature if source_armature_indicator == "T"
            else None
        )

        if transform_type == 'rotate_bone':
            rotate_bone(target_armature, target_bone_name, axis, transform_value, mirror) # calls the function and saves the return value, which can be used to revert the changes
        elif transform_type == 'scale_bone':
            scale_pose_bone(target_armature, target_bone_name, transform_value, axis)
        elif transform_type == 'match_pose_bone_head_pos':
            match_pose_bone_head_pos(target_armature, source_armature, target_bone_name, source_bone_name, foot_z_location)
        elif transform_type == 'match_pose_bone_orientation':
            match_pose_bone_orientation(target_armature, source_armature, target_bone_name, source_bone_name, unreal_right)
        elif transform_type == 'chain_pose_bone_position':
            chain_pose_bone_position(target_armature, target_bone_name, source_bone_name)
        elif transform_type == 'match_edit_bone_pos':
            match_edit_bone_pos(target_armature, source_armature, target_bone_name, source_bone_name)
        elif transform_type == 'match_edit_bone_z_location':
            match_edit_bone_z_location(target_armature, source_armature, target_bone_name, source_bone_name)
        elif transform_type == 'match_edit_bone_chain_scale':
            match_edit_bone_chain_scale(target_armature, source_armature, target_chain, source_chain)
        elif transform_type == 'copy_bone_between_armatures':
            copy_bone_between_armatures(target_armature, source_armature, source_bone_name, target_bone_name, new_bone_name)
        else:
            print("ExecuteTransfromMap: Unknown transform type")
