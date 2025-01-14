
def is_flipped_unreal_bone(bone_name, is_target_unreal_skeleton):
    bones = {
        "_r": ["clavicle", "upperarm", "lowerarm", "hand", "thumb", "index", "ring", "pinky", "ball"],
        "_l": ["thigh", "calf"],
    }

    if is_target_unreal_skeleton:
        for key, substring_list in bones.items():
            if key in bone_name:
                for substring in substring_list:
                    if substring in bone_name:
                        return True
    else:
        return False