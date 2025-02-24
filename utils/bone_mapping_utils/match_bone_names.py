import re
from difflib import SequenceMatcher

side_indicator_list = {
    "right": ['_right', 'right_',':right', 'right:','.right', 'right.','-right', 'right-', 'right', "_r", "r_", "-r", "r-", ".r", "r."],
    "left": ['_left', 'left_',':left', 'left:', '.left', 'left.','-left', 'left-', 'left', "_l", "l_", "-l", "l-", ".l", "l."],
}

separator_list = ['-', '_', '.', ';', ',', ':']

bone_synonym_map = [
    ["hips", "pelvis"],
    ["thumb", "handThumb"],
    ["index", "handIndex" ,"pointer"],
    ["middle","handMiddle"],
    ["ring","handRing"],
    ["pinky", "little", "handPinky", "handLittle"],
    ["thigh", 'upLeg'],
    ["calf", "leg", "lowerLeg", "LowLeg", "shin"],
    ["foot", "feet"],
    ["toe", "ball", "toes", "toeBase"],
    ["shoulder", "clavicle"],
    ["upperarm", "uparm", "firstarm", "arm"],
    ["lowerarm", "lowarm", "secondarm", "forearm"],
    ["spine", "back"],
    ["head", "skull"]
]

bone_number_exceptions = {
    "metacarpal": 0,
    "palm": 0
}
#______________________________________________________________________________________________________________________________________________
def string_similarity_ratio(str1, str2):
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() * 100

def find_common_prefix(bone_names):
    if not bone_names:
        return bone_names

    def camel_case_split(s):
        return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', '_', s).lower()

    normalized_bone_names = [camel_case_split(s).replace('.', '_').replace(':', '_').replace('-', '_') for s in bone_names]
    
    split_parts = [s.split('_') for s in normalized_bone_names]
    
    common_prefix_parts = split_parts[0]
    for parts in split_parts[1:]:
        common_prefix_parts = [p for p, q in zip(common_prefix_parts, parts) if p == q]
        if not common_prefix_parts:
            break

    common_prefix = '_'.join(common_prefix_parts)

    results = []
    for original, normalized in zip(bone_names, normalized_bone_names):
        match = re.match(rf"^{re.escape(common_prefix).replace('_', '[._-]?')}", original, re.IGNORECASE)
        prefix_with_original_case = match.group() if match else ""
        clean_string = original[len(prefix_with_original_case):]
        
        if clean_string and clean_string[0] in '.-_':
            prefix_with_original_case += clean_string[0]
            clean_string = clean_string[1:]

        results.append({
            'original_bone_name': original,
            'prefix': prefix_with_original_case.rstrip('._-'),
            'clean_string': clean_string,
        })
    return results

def find_number_in_string(input_string):
    for bone_name, bone_number in bone_number_exceptions.items():
        if bone_name.lower() in input_string.lower():
            start_index = input_string.lower().index(bone_name.lower())
            original_substring = input_string[start_index:start_index + len(bone_name)]
            return {'number': bone_number, 'substring': original_substring}
    
        match = re.search(r'\d+', input_string)
        if match:
            return {'number': int(match.group()), 'substring': match.group()}

    return None

def is_valid_indicator(indicator, bone_name_lower):
    for separator in separator_list:
        if separator in indicator:
            if indicator.endswith(separator):
                start_index = bone_name_lower.index(indicator)
                if start_index > 0 and bone_name_lower[start_index - 1].islower():
                    return False
                else:
                    return True
            elif indicator.startswith(separator):
                end_index = bone_name_lower.index(indicator) + len(indicator)
                if end_index < len(bone_name_lower) and bone_name_lower[end_index].islower():
                    return False
                else:
                    return True
    return True

def find_side_indicator_in_bone_name(bone_name, side_indicator_list_object):
    bone_name_lower = bone_name.lower()
    for key, side_synonim_list in side_indicator_list_object.items():
        for side_indicator in side_synonim_list:
            if side_indicator.lower() in bone_name_lower:
                start_index = bone_name_lower.index(side_indicator.lower())
                original_substring = bone_name[start_index:start_index + len(side_indicator)]
                match = None
                if any(separator in side_indicator.lower() for separator in separator_list): #validate the side indicator substring, by checking if its part of a word or not, to filter out false matches like_ index_finge(r_)left, where the r_ would be found instead of the actual indicator(_left)
                    match = is_valid_indicator(side_indicator.lower(), bone_name_lower)
                else:
                    pattern = (
                        r'(?<=[a-z])' + re.escape(original_substring) + r'(?![a-zA-Z])' +
                        r'|' +  # Or
                        r'(?<![a-zA-Z])' + re.escape(original_substring) + r'(?=[A-Z])'
                    )
                    match = re.search(pattern, bone_name)
                if match:
                    return {"list_key": key, "substring": original_substring}
    return None


def remove_substring(base_string, substring):
    return base_string.replace(substring, '')

def analize_bone_name(bone_name, prefix):
    side = find_side_indicator_in_bone_name(bone_name, side_indicator_list)
    bone = bone_name
    if prefix:
        bone = remove_substring(bone, prefix)
    if side is not None:
        bone = remove_substring(bone, side['substring'])
    number_in_name = find_number_in_string(bone)
    if number_in_name is not None:
        bone = remove_substring(bone, number_in_name['substring'])
    
    for separator in separator_list:
        bone = remove_substring(bone, separator)

    return {
        "bone_name": bone_name,
        "bone_root": bone,
        "side": side["list_key"] if side is not None else None,
        "bone_number": number_in_name["number"] if number_in_name is not None else None 
        }

#_____________________________________________________________________________________________________

def bone_name_in_list(target_bone_name, source_bone_name_list):
    for index, source_bone_name in enumerate(source_bone_name_list):
        if target_bone_name.lower() == source_bone_name.lower():
            return {target_bone_name: source_bone_name_list[index]}
    return None


def find_bone_synonym_match_from_source_bone_list(target_bone_name, source_bone_name_list):
    for source_bone_name in source_bone_name_list:
        for synonim_list in bone_synonym_map:
            lower_synonim_list = [synonim.lower() for synonim in synonim_list]
            lower_target_bone_name = target_bone_name.lower()
            lower_source_bone_name = source_bone_name.lower()
            if lower_target_bone_name in lower_synonim_list and lower_source_bone_name in lower_synonim_list:
                return {target_bone_name:source_bone_name}
    return None

def match_target_bone_name_to_source_list(target_bone_name, source_bone_name_list):
    direct_match = bone_name_in_list(target_bone_name, source_bone_name_list)
    if direct_match is not None:
        return direct_match
    synonim_match = find_bone_synonym_match_from_source_bone_list(target_bone_name, source_bone_name_list)   
    if synonim_match is not None:
        return synonim_match    
    similarity_match = find_best_bone_name_match_in_source_bones_by_similarity(target_bone_name, source_bone_name_list)
    if similarity_match is not None:
        return similarity_match     
    return None

def find_best_bone_name_match_in_source_bones_by_similarity(target_bone_name, source_bone_list):
    matched_pairs = []
    for source_bone_name in source_bone_list:
            for synonim_list in bone_synonym_map:
                lower_synonim_list = [synonim.lower() for synonim in synonim_list]
                lower_target_bone_name = target_bone_name.lower()
                lower_source_bone_name = source_bone_name.lower()
                source_bone_name_highest = 0
                target_bone_name_highest = 0
                for synonim in lower_synonim_list:
                    str_sim = string_similarity_ratio(synonim, lower_target_bone_name) #80
                    list_i_sim = string_similarity_ratio(synonim, lower_source_bone_name) #80 
                    source_bone_name_highest = list_i_sim if list_i_sim > source_bone_name_highest else source_bone_name_highest
                    target_bone_name_highest = str_sim if str_sim > target_bone_name_highest else target_bone_name_highest

                if source_bone_name_highest > 66 and target_bone_name_highest > 66:
                    matched_pairs.append({target_bone_name:source_bone_name, "combined": source_bone_name_highest+target_bone_name_highest})
    if not matched_pairs:
        return None
    else:
        best_match = max(matched_pairs, key=lambda x: x['combined'])
        best_match.pop('combined')
        return best_match


#______________________________________________________________________________________________________________________________________________


def map_bone_lists(target_bone_list, source_bone_list):
    bone_mapping = {}
    analized_target_bone_list = []
    analized_source_bone_list = []
    source_bone_base_name_list = []
    target_bone_prefix = find_common_prefix(target_bone_list)[0]["prefix"]
    source_bone_prefix = find_common_prefix(source_bone_list)[0]["prefix"]
    for bone in target_bone_list:
        analized_target_bone_list.append(analize_bone_name(bone, target_bone_prefix))
    for bone in source_bone_list:
        analized_bone_name = analize_bone_name(bone, source_bone_prefix)
        analized_source_bone_list.append(analized_bone_name)
        source_bone_base_name_list.append(analized_bone_name["bone_root"])
    for target_bone_object in analized_target_bone_list:
        match_name = None
        best_root_match = match_target_bone_name_to_source_list(target_bone_object["bone_root"], source_bone_base_name_list)       
        if best_root_match is not None:
            match_name = best_root_match[target_bone_object["bone_root"]]
        else:
            bone_mapping[target_bone_object['bone_name']] = None
            continue

        for index, source_bone_object in enumerate(analized_source_bone_list):
            if(source_bone_object["side"] == target_bone_object['side'] and source_bone_object["bone_number"] == target_bone_object['bone_number'] and source_bone_object['bone_root'] == match_name):
                bone_mapping[target_bone_object['bone_name']] = source_bone_object["bone_name"]
                break
            if(source_bone_object["side"] == target_bone_object['side'] and source_bone_object['bone_root'] == match_name):
                if source_bone_object['bone_number'] == None and (target_bone_object['bone_number'] == 0 or  target_bone_object['bone_number'] == 1) and not bone_mapping.get(target_bone_object['bone_name']): 
                    bone_mapping[target_bone_object['bone_name']] = source_bone_object["bone_name"]
                    break
                if target_bone_object['bone_number'] == None and (source_bone_object['bone_number'] == 0 or  source_bone_object['bone_number'] == 1) and not bone_mapping.get(target_bone_object['bone_name']): 
                    bone_mapping[target_bone_object['bone_name']] = source_bone_object["bone_name"]
                    break
            if index+1 == len(analized_source_bone_list):
                bone_mapping[target_bone_object['bone_name']] = None
                break
    return bone_mapping
