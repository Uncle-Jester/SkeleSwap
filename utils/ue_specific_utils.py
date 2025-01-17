from .dev_utils import debug_print

def is_flipped_unreal_bone(bone_name, is_target_unreal_skeleton):
    bones = {
        "_r": ["clavicle", "upperarm", "lowerarm", "hand", "thumb", "index","middle", "ring", "pinky", "ball"],
        "_l": ["thigh", "calf"],
    }

    if is_target_unreal_skeleton:
        debug_print(f"UESpecificUtils-IsFlippedUnrealBone: Target is unreal. Bone Name: {bone_name}")
        for key, substring_list in bones.items():
            if key in bone_name:
                debug_print(f"UESpecificUtils-IsFlippedUnrealBone: Side indicator is in bone name. Indicator: {key} Bone Name: {bone_name}")
                for substring in substring_list:
                    debug_print(f"UESpecificUtils-IsFlippedUnrealBone: check if: {substring} is in {bone_name} ")
                    if substring in bone_name:
                        debug_print(f"UESpecificUtils-IsFlippedUnrealBone: check PASSED {substring} is in {bone_name} ")
                        return True
    else:
        return False