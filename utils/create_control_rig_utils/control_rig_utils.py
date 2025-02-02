import bpy
from mathutils import Vector
from .. import remove_connected_relation

######################################## Unreal Specific Utils ##########################################################
main_bones = [
    "pelvis",
    "spine_01", "spine_02", "spine_03", "spine_04", "spine_05",
    "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
    "thigh_r", "calf_r", "foot_r", "ball_l",
    "neck_01", "neck_02", "head",
    "thumb_01_l", "thumb_02_l", "thumb_03_l",
    "index_metacarpal_l", "index_01_l", "index_02_l", "index_03_l",
    "middle_metacarpal_l", "middle_01_l", "middle_02_l", "middle_03_l",
    "ring_metacarpal_l", "ring_01_l", "ring_02_l", "ring_03_l",
    "pinky_metacarpal_l", "pinky_01_l", "pinky_02_l", "pinky_03_l",
]
flipped_bones = [
    "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thigh_l", "calf_l",
    "foot_l", "ball_r",
    "thumb_01_r", "thumb_02_r", "thumb_03_r",
    "index_metacarpal_r", "index_01_r", "index_02_r", "index_03_r",
    "middle_metacarpal_r", "middle_01_r", "middle_02_r", "middle_03_r",
    "ring_metacarpal_r", "ring_01_r", "ring_02_r", "ring_03_r",
    "pinky_metacarpal_r", "pinky_01_r", "pinky_02_r", "pinky_03_r"
]

def apply_ik_transforms(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    ik_driver_collection = get_bone_collection(armature, "IK_DRIVER_BONES")
    ik_ctrl_collection = get_bone_collection(armature, "IK_CTRL_BONES")
    if not ik_ctrl_collection:
        return
    
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    armature_eval = armature.evaluated_get(depsgraph)

    for bone in ik_ctrl_collection.bones:
        pose_bone = armature.pose.bones.get(bone.name)
        eval_bone = armature_eval.pose.bones.get(bone.name)

        if pose_bone and eval_bone:
           pose_bone.matrix = eval_bone.matrix
    
    for bone in ik_driver_collection.bones:
        pose_bone = armature.pose.bones.get(bone.name)
        eval_bone = armature_eval.pose.bones.get(bone.name)

        if pose_bone and eval_bone:
           pose_bone.matrix = eval_bone.matrix

    print("IK transforms locked in without baking.")

def apply_fk_transforms(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    fk_driver_collection = get_bone_collection(armature, "FK_DRIVER_BONES")
    if not fk_driver_collection:
        return
    
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    armature_eval = armature.evaluated_get(depsgraph)

    for bone in fk_driver_collection.bones:
        pose_bone = armature.pose.bones.get(bone.name)
        eval_bone = armature_eval.pose.bones.get(bone.name)

        if pose_bone and eval_bone:
           pose_bone.matrix = eval_bone.matrix

    print("IK transforms locked in without baking.")

def add_transform_constraint_to_flipped_bone_with_driver(armature, bone, constraint_name, driver):
    transform_constraint = bone.constraints.new(type='TRANSFORM')
    transform_constraint.name = constraint_name
    transform_constraint.target = armature
    transform_constraint.subtarget = bone.name
    transform_constraint.map_from = 'ROTATION'
    transform_constraint.map_to = 'ROTATION'
    transform_constraint.to_min_x_rot = 3.14159
    if driver is not None:
        driver_property_name = driver.get("property_name")
        invert = driver.get("invert")
        add_driver_to_constraint_influence(armature, transform_constraint, driver_property_name, invert=invert)



def add_copy_transforms_constraint_with_driver(armature, bone_name, target_bone_name, constraint_name, driver):
    bone = armature.pose.bones.get(bone_name)
    if not bone:
        return
    copy_transform_constraint = bone.constraints.new(type='COPY_TRANSFORMS')
    copy_transform_constraint.name = constraint_name
    copy_transform_constraint.target = armature
    copy_transform_constraint.subtarget = target_bone_name
    
    if driver is not None:
        driver_property_name = driver.get("property_name")
        invert = driver.get("invert")
        add_driver_to_constraint_influence(armature, copy_transform_constraint, driver_property_name, invert=invert)

def add_copy_rotation_constraint_with_driver(armature, bone_name, target_bone_name, constraint_name, driver):
    bone = armature.pose.bones.get(bone_name)
    if not bone:
        return
    copy_transform_constraint = bone.constraints.new(type='COPY_ROTATION')
    copy_transform_constraint.name = constraint_name
    copy_transform_constraint.target = armature
    copy_transform_constraint.subtarget = target_bone_name
    
    if driver is not None:
        driver_property_name = driver.get("property_name")
        invert = driver.get("invert")
        add_driver_to_constraint_influence(armature, copy_transform_constraint, driver_property_name, invert=invert)

def add_copy_location_constraint_with_driver(armature, bone_name, target_bone_name, constraint_name, driver):
    bone = armature.pose.bones.get(bone_name)
    if not bone:
        return
    copy_transform_constraint = bone.constraints.new(type='COPY_LOCATION')
    copy_transform_constraint.name = constraint_name
    copy_transform_constraint.target = armature
    copy_transform_constraint.subtarget = target_bone_name
    
    if driver is not None:
        driver_property_name = driver.get("property_name")
        invert = driver.get("invert")
        add_driver_to_constraint_influence(armature, copy_transform_constraint, driver_property_name, invert=invert)

# driver = {"property_name": driver_property_name, "invert_condition" : invert_condition} src IK trg SNAP
def add_driver_bone_constraints_to_collection_of_bones(armature, source_driver_bone_collection_name, source_driver_prefix, target_driver_bone_collection_name, target_driver_prefix, add_transform_constraint_to_flipped_bones=True, driver=None):
    bpy.ops.object.mode_set(mode='POSE')
    source_driver_bone_collection = get_bone_collection(armature, source_driver_bone_collection_name)
    target_driver_bone_collection = get_bone_collection(armature, target_driver_bone_collection_name)
    pose_bones = armature.pose.bones
    for bone in source_driver_bone_collection.bones:
        bone.select = True
        driven_bone = pose_bones.get(bone.name.replace(f"{source_driver_prefix}_", f"{target_driver_prefix}_"))
        
        if driven_bone and driven_bone.name in target_driver_bone_collection.bones:
            copy_constraint_name = f"Copy {source_driver_prefix.replace('DRV_', '')} Transforms -> {bone.name}"
            driven_bone.bone.select = True
            armature.data.bones.active = driven_bone.bone
            
            if driven_bone.name.replace(f"{target_driver_prefix}_", "") in flipped_bones:                
                add_copy_transforms_constraint_with_driver(armature, driven_bone.name, bone.name, copy_constraint_name, driver)                
            
                if add_transform_constraint_to_flipped_bones:
                    transform_constraint_name = f"{target_driver_prefix}_TRANSFORM (FLIP rotation) -> {bone.name}"
                    add_transform_constraint_to_flipped_bone_with_driver(armature, driven_bone, transform_constraint_name, driver)
            
            else:
                add_copy_transforms_constraint_with_driver(armature, driven_bone.name, bone.name, copy_constraint_name, driver)

            driven_bone.bone.select = False
            bone.select = False

def add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, driver_bone_collection_name, driver_prefix, add_transform_constraint_to_flipped_bones=True, add_driver_to_copy_transform_influence = False):
    bpy.ops.object.mode_set(mode='POSE')
    driver_bone_collection = get_bone_collection(armature, driver_bone_collection_name)
    pose_bones = armature.pose.bones
    for bone in driver_bone_collection.bones:
        bone.select = True
        deform_bone = pose_bones.get(bone.name.replace(f"{driver_prefix}_", ""))
        if deform_bone:
            deform_bone.bone.select = True
            armature.data.bones.active = deform_bone.bone
            if deform_bone.name in flipped_bones:
                copy_transform_constraint = deform_bone.constraints.new(type='COPY_TRANSFORMS')
                copy_transform_constraint.name = f"{driver_prefix.replace('DRV_', '')}_Copy Transforms -> {bone.name}"
                copy_transform_constraint.target = armature
                copy_transform_constraint.subtarget = bone.name
                
                if add_driver_to_copy_transform_influence:
                    add_driver_to_constraint_influence(armature, copy_transform_constraint, "IK_controls", invert=("FK" in driver_prefix))
                
                if add_transform_constraint_to_flipped_bones:
                    transform_constraint = deform_bone.constraints.new(type='TRANSFORM')
                    transform_constraint.name = f"{driver_prefix.replace('DRV_', '')}_Transform -> {bone.name}"
                    transform_constraint.target = armature
                    transform_constraint.subtarget = bone.name
                    transform_constraint.map_from = 'ROTATION'
                    transform_constraint.map_to = 'ROTATION'
                    transform_constraint.to_min_x_rot = 3.14159
                    if add_driver_to_copy_transform_influence:
                        add_driver_to_constraint_influence(armature, transform_constraint, "IK_controls", invert=("FK" in driver_prefix))
            else:
                copy_transform_constraint = deform_bone.constraints.new(type='COPY_TRANSFORMS')
                copy_transform_constraint.name = f"{driver_prefix.replace('DRV_', '')}_Copy Transforms -> {bone.name}"
                copy_transform_constraint.target = armature
                copy_transform_constraint.subtarget = bone.name
                
                if add_driver_to_copy_transform_influence:
                    add_driver_to_constraint_influence(armature, copy_transform_constraint, "IK_controls", invert=("FK" in driver_prefix))

            deform_bone.bone.select = False
            bone.select = False

######################################## Overly Specific bone creation Utils #####################################

def create_driver_bones(armature, collection_name, driver_prefix):
    new_collection = create_bone_collection(armature, collection_name)
    bpy.ops.object.mode_set(mode='OBJECT')
    deform_bone_collection = get_bone_collection(armature, "DEFORM_BONES")
    deform_bone_names = [bone.name for bone in deform_bone_collection.bones]

    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
  
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data


    for bone_name in main_bones:
        if bone_name in armature_data.edit_bones and bone_name in deform_bone_names:
            armature_data.edit_bones[bone_name].select = True

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.duplicate()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    duplicated_bones = [bone for bone in armature_data.edit_bones if bone.select]

    print(f"duplicated_bones: {duplicated_bones}")

    for edit_bone in duplicated_bones:
        edit_bone.use_deform = False
        edit_bone.use_connect = False
        edit_bone_obj = armature_data.bones.get(edit_bone.name)
        if edit_bone_obj:
            bone_name = edit_bone_obj.name
            if ".001" in bone_name or ".002" in bone_name or ".003" in bone_name:
                if ".001" in bone_name:
                    bone_name = bone_name.replace(".001", "")
                elif ".002" in bone_name:
                    bone_name = bone_name.replace(".002", "")
                elif ".003" in bone_name:
                    bone_name = bone_name.replace(".003", "")
            armature_data.bones.get(edit_bone.name).name = f"{driver_prefix}_{bone_name}"


    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.collection_assign(name=new_collection.name)
    bpy.ops.armature.symmetrize()


    armature_data.collections.active = new_collection
    bpy.ops.armature.collection_select()
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.collection_unassign(name=deform_bone_collection.name)
    bpy.ops.armature.collection_assign(name=new_collection.name)
    bpy.ops.armature.select_all(action='DESELECT')


######################################## Edit Bone Operation Utils ###############################################
# TBD: A lot of the below util functions should be moved to the bone_transform_utils.py file

def duplicate_bone(armature, bone_name_to_duplicate, new_bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bone = armature_data.edit_bones.get(bone_name_to_duplicate)
    bpy.ops.armature.select_all(action='DESELECT')
    if bone:
        bone.select = True
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.duplicate()
        new_bone = armature_data.edit_bones.get(f"{bone_name_to_duplicate}.001")
        if new_bone:
            new_bone.name = new_bone_name
        bpy.ops.armature.select_all(action='DESELECT')

def scale_edit_bone(armature, bone_name, scale_value):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bone = armature_data.edit_bones.get(bone_name)
    bpy.ops.armature.select_all(action='DESELECT')
    if bone:
        bone.select = True
        armature_data.edit_bones.active = bone
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=scale_value)
        bpy.ops.armature.select_all(action='DESELECT')

def find_intersection_point(armature, bone_name_1, bone_name_2):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bone_1 = armature_data.edit_bones.get(bone_name_1)
    bone_2 = armature_data.edit_bones.get(bone_name_2)
    if not bone_1 or not bone_2:
        print(f"One or both bones not found. {bone_1}, {bone_2}")
        return
    direction_vector = bone_1.tail - bone_1.head
    bone_2_head = bone_2.head
    t = (bone_2_head.x - bone_1.head.x) / direction_vector.x
    intersection_point = bone_1.head + direction_vector * t
    
    return intersection_point

def connect_bone_tail_to_head(armature, tail_bone_name, head_bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    tail_bone = armature_data.edit_bones.get(tail_bone_name)
    head_bone = armature_data.edit_bones.get(head_bone_name)
    if tail_bone and head_bone:
        tail_bone.tail = head_bone.head


def create_bone_at_intersection(armature, bone_name_1, bone_name_2, translate_vector, new_bone_name):
    intersection_point = find_intersection_point(armature, bone_name_1, bone_name_2)
    armature_data = armature.data
    if intersection_point:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.select_all(action='DESELECT')
        new_bone = armature_data.edit_bones.new(new_bone_name)
        new_bone.head = intersection_point
        new_bone.tail = intersection_point + Vector(translate_vector)
        new_bone.select = True
        armature_data.edit_bones.active = new_bone
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.parent_clear(type='CLEAR')
        bpy.ops.armature.select_all(action='DESELECT')

def extrude_bone(armature, bone_head_to_extrude_from, bone_name, translate_vector, unparent=True):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bpy.ops.armature.select_all(action='DESELECT')
    bone = armature_data.edit_bones.get(bone_head_to_extrude_from)
    if bone:
        bone.select_head = True
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.extrude()
        bpy.ops.transform.translate(value=translate_vector)
        bpy.ops.armature.select_all(action='DESELECT')
        new_bone = armature_data.edit_bones.get(f"{bone_head_to_extrude_from}.001")
        new_bone.name = bone_name
        if new_bone:
            new_bone.use_deform = False
            new_bone.select = True
            armature_data.edit_bones.active = new_bone
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            if unparent:
                bpy.ops.armature.parent_clear(type='CLEAR')

def clear_parent(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bone = armature_data.edit_bones.get(bone_name)
    if bone:
        bone.parent = None

def move_edit_bone_by_vector(armature, edit_bone_name, translate_vector):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    edit_bone = armature_data.edit_bones.get(edit_bone_name)
    bpy.ops.armature.select_all(action='DESELECT')
    if edit_bone:
        edit_bone.select = True
        armature_data.edit_bones.active = edit_bone
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.translate(value=translate_vector)

def parent_bone_keep_offset(armature, child_bone_name, parent_bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    child_bone = armature_data.edit_bones.get(child_bone_name)
    parent_bone = armature_data.edit_bones.get(parent_bone_name)
    bpy.ops.armature.select_all(action='DESELECT')
    if child_bone and parent_bone:
        child_bone.select = True
        parent_bone.select = True
        armature_data.edit_bones.active = parent_bone
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.armature.parent_set(type='OFFSET')

######################################## Driver and Custom Property Utils ###############################################

def add_ik_fk_switch_property(armature, property_name="IK_controls"):
    if property_name not in armature.keys():
        armature[property_name] = True
        armature["_RNA_UI"] = armature.get("_RNA_UI", {})
        armature["_RNA_UI"][property_name] = {
            "description": "Toggle IK Controls (True = IK, False = FK)",
            "default": True,
            "min": 0,
            "max": 1
        }

def add_driver_to_constraint_influence(armature, constraint, property_name, invert=False):
    driver = constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    
    var = driver.variables.new()
    var.name = "ik_fk_switch"
    var.targets[0].id = armature
    var.targets[0].data_path = f'["{property_name}"]'
    
    driver.expression = "1 - ik_fk_switch" if invert else "ik_fk_switch"

######################################## Collection and Bone collection related Utils ###################################

def create_bone_collection(armature, name):
    if bpy.context.object and bpy.context.object.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    if name not in armature_data.collections:
        return armature_data.collections.new(name)
    else:
        print(f"Collection with name {name} already exists.")
    
def get_bone_collection(armature, name):
    armature_data = armature.data
    return armature_data.collections[name]

def assign_bones_to_new_collection(armature, bone_names, new_collection_name, should_remove_from_previous_collections=True):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    
    armature_data = armature.data

    for bone_name in bone_names:
        bone = armature_data.edit_bones.get(bone_name)       
        if bone:
            armature_data.edit_bones[bone_name].select = True
            
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    
    if should_remove_from_previous_collections:
        for collection in armature_data.collections:
            bpy.ops.armature.collection_unassign(name=collection.name)
        
    

    new_collection = create_bone_collection(armature, new_collection_name)
    print(f"new_collection: {new_collection}")
    
    if not new_collection:
        new_collection = armature_data.collections[new_collection_name]

    print(f"new_collection: {new_collection}")
    
    armature_data.collections.active = new_collection

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.armature.collection_assign(name=new_collection_name)
    



def create_deform_bones_collection(armature):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.context.view_layer.objects.active = armature

    deform_bone_collection = create_bone_collection(armature, "DEFORM_BONES")
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.collection_assign(name=deform_bone_collection.name)

    bpy.ops.armature.select_all(action='DESELECT')



def set_bone_collection_visibility(armature, collection_name, is_visible):
    bpy.ops.object.mode_set(mode='EDIT')
    armature_data = armature.data
    bone_collection = get_bone_collection(armature, collection_name)
    if bone_collection:
        armature_data.collections[bone_collection.name].is_visible = is_visible
    else:
        print(f"Collection with name {collection_name} not found.")

######################################## Constraint Utils ###############################################################

def add_IK_constraint(armature, target_bone_name, effector_bone_name, pole_target_name, chain_length=2, pole_angle=0):
    bpy.ops.object.mode_set(mode='POSE')
    pole_angle = pole_angle * 0.0174533
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(target_bone_name)
    effector_bone = pose_bones.get(effector_bone_name)
    pole_target = pose_bones.get(pole_target_name)
    bpy.ops.pose.select_all(action='DESELECT')
    if target_bone and effector_bone and pole_target:
        target_bone.bone.select = True
        effector_bone.bone.select = True
        pole_target.bone.select = True
        armature.data.bones.active = target_bone.bone
        bpy.ops.pose.constraint_add(type='IK')
        ik_constraint = target_bone.constraints.get("IK")
        if ik_constraint:
            ik_constraint.target = armature
            ik_constraint.subtarget = effector_bone_name
            ik_constraint.pole_target = armature
            ik_constraint.pole_subtarget = pole_target_name
            ik_constraint.pole_angle = pole_angle
            ik_constraint.chain_count = chain_length

def add_copy_location_constraint(armature, target_bone_name, source_bone_name, head_tail=1, target_space='WORLD', owner_space='WORLD', influence=1, driver=None):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(target_bone_name)
    source_bone = pose_bones.get(source_bone_name)
    bpy.ops.pose.select_all(action='DESELECT')
    if target_bone and source_bone:
        target_bone.bone.select = True
        source_bone.bone.select = True
        armature.data.bones.active = target_bone.bone
        bpy.ops.pose.constraint_add(type='COPY_LOCATION')
        copy_location_constraint = target_bone.constraints.get("Copy Location")
        if copy_location_constraint:
            copy_location_constraint.target = armature
            copy_location_constraint.subtarget = source_bone_name
            copy_location_constraint.head_tail = head_tail
            copy_location_constraint.target_space = target_space
            copy_location_constraint.owner_space = owner_space
            copy_location_constraint.influence = influence

def add_damped_track_constraint(armature, target_bone_name, source_bone_name):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(target_bone_name)
    source_bone = pose_bones.get(source_bone_name)
    bpy.ops.pose.select_all(action='DESELECT')
    if target_bone and source_bone:
        target_bone.bone.select = True
        source_bone.bone.select = True
        armature.data.bones.active = target_bone.bone
        bpy.ops.pose.constraint_add(type='DAMPED_TRACK')
        damped_track_constraint = target_bone.constraints.get("Damped Track")
        if damped_track_constraint:
            damped_track_constraint.target = armature
            damped_track_constraint.subtarget = source_bone_name

def add_track_to_constraint(armature, target_bone_name, source_bone_name, track_axis="X", up="Y"):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(target_bone_name)
    source_bone = pose_bones.get(source_bone_name)
    if target_bone and source_bone:
        target_bone.bone.select = True
        source_bone.bone.select = True
        armature.data.bones.active = target_bone.bone
        bpy.ops.pose.constraint_add(type='TRACK_TO')
        track_to_constraint = target_bone.constraints.get("Track To")
        if track_to_constraint:
            track_to_constraint.target = armature
            track_to_constraint.subtarget = source_bone_name
            track_to_constraint.track_axis = f'TRACK_{track_axis}'
            track_to_constraint.up_axis = f'UP_{up}'

def add_copy_rotation_constraint(armature, bone_constrain, bone_to_copy, axes=(1, 1, 1), space='LOCAL', to_space='LOCAL'):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(bone_constrain)
    source_bone = pose_bones.get(bone_to_copy)
    bpy.ops.pose.select_all(action='DESELECT')
    if target_bone and source_bone:
        target_bone.bone.select = True
        source_bone.bone.select = True
        armature.data.bones.active = target_bone.bone
        bpy.ops.pose.constraint_add(type='COPY_ROTATION')
        copy_rotation_constraint = target_bone.constraints.get("Copy Rotation")
        if copy_rotation_constraint:
            copy_rotation_constraint.target = armature
            copy_rotation_constraint.subtarget = bone_to_copy
            copy_rotation_constraint.use_x = bool(axes[0])
            copy_rotation_constraint.use_y = bool(axes[1])
            copy_rotation_constraint.use_z = bool(axes[2])
            copy_rotation_constraint.target_space = space
            copy_rotation_constraint.owner_space = to_space

def remove_constraint(armature, target_bone_name, constraint_type):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    target_bone = pose_bones.get(target_bone_name)
    if target_bone:
        for constraint in target_bone.constraints:
            if constraint.type == constraint_type:
                target_bone.constraints.remove(constraint)
                break


def move_constraint_to_top(armature, bone_name, constraint_name="Copy Rotation"):
    bpy.ops.object.mode_set(mode='POSE')
    pose_bones = armature.pose.bones
    bone = pose_bones.get(bone_name)
    if bone:
        constraint = bone.constraints.get(constraint_name)
        if constraint:
            while bone.constraints[0] != constraint:
                bone.constraints.move(len(bone.constraints) - 1, 0)

######################################## Custom Bone Shape Utils ########################################################

def create_curled_plane(name, width, height, curl_factor=1.3):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(size=1)
    plane = bpy.context.active_object
    plane.name = name

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.subdivide(number_cuts=4)
    bpy.ops.transform.resize(value=(width, height, 1))
    bpy.ops.object.mode_set(mode='OBJECT')

    for vert in plane.data.vertices:
        vert.co.z = -curl_factor * vert.co.y ** 2

    return plane

def create_custom_shape_mesh(shape, curled=False):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    
    if shape == 'circle':
        bpy.ops.mesh.primitive_circle_add(radius=1)
    elif shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1)
    elif shape == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=1)
    elif shape == 'plane':
        if curled:
            curled_plane = create_curled_plane(f"curled_plane", 1, 1)
            bpy.context.view_layer.objects.active = curled_plane
            custom_shape = bpy.context.active_object
            custom_shape.name = f"curled_plane_custom_shape"
            add_mesh_to_collection(custom_shape, "rig_shapes")
            return
        else:
            bpy.ops.mesh.primitive_plane_add(size=1)
    else:
        print("Invalid shape option. Choose from: circle, sphere, box, cube.")
        return
    
    custom_shape = bpy.context.active_object
    custom_shape.name = f"{shape}_custom_shape"
    add_mesh_to_collection(custom_shape, "rig_shapes")

def find_mesh_by_name(mesh_name):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name == mesh_name:
            return obj
    print(f"Mesh with name {mesh_name} not found.")
    return None
 
def add_mesh_to_collection(mesh, collection_name):
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        collection.hide_viewport = True

    for current_collection in mesh.users_collection:
        current_collection.objects.unlink(mesh)

    if mesh.name not in collection.objects:
        collection.objects.link(mesh)

def add_custom_shape_for_bone(armature, bone_name, shape, theme_number, wireframe=True, scale=[1,1,1], translation=[0,0,0], rotation=[0,0,0], mode=None):
    print(f"MODE FOR SHAPE = {mode}")
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    custom_shape = find_mesh_by_name(f"{shape}_custom_shape")
    if not custom_shape:
        print(f"Custom shape not found. custom shape name param: {shape}_custom_shape")
        return
   
    bpy.context.view_layer.objects.active = armature

    print(f"bone_name: {bone_name}")

    bpy.ops.object.mode_set(mode='POSE')
    pose_bone = armature.pose.bones.get(bone_name)
    if pose_bone:
        pose_bone.bone.color.palette = f"THEME{theme_number}"
        pose_bone.custom_shape = custom_shape
        pose_bone.custom_shape_scale_xyz[0] = scale[0]
        pose_bone.custom_shape_scale_xyz[1] = scale[1]
        pose_bone.custom_shape_scale_xyz[2] = scale[2]
        pose_bone.custom_shape_translation[0] = translation[0]
        pose_bone.custom_shape_translation[1] = translation[1]
        pose_bone.custom_shape_translation[2] = translation[2]
        pose_bone.custom_shape_rotation_euler[0] = rotation[0] * 0.0174533 # this is to convert from degrees to radians
        pose_bone.custom_shape_rotation_euler[1] = rotation[1] * 0.0174533
        pose_bone.custom_shape_rotation_euler[2] = rotation[2] * 0.0174533
        pose_bone.use_custom_shape_bone_size = False
        pose_bone.bone.show_wire = wireframe

        if mode in ["IK", "FK"]:
            print(f"Shape created in mode: {mode}")
            bpy.context.view_layer.objects.active = custom_shape
            driver = pose_bone.bone.driver_add("hide").driver
            driver.type = 'SCRIPTED'

            var = driver.variables.new()
            var.name = "ik_fk_switch"
            var.targets[0].id = armature
            var.targets[0].data_path = '["IK_controls"]'

            if mode == "IK":
                driver.expression = "1 - ik_fk_switch"
                print(f"Driver expression: {driver.expression}")
            elif mode == "FK":
                driver.expression = "ik_fk_switch"
            
            bpy.context.view_layer.objects.active = armature
    else:
        print(f"Bone {bone_name} not found in the armature.")