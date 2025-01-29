import bpy
from.utils.create_control_rig_utils import create_custom_shape_mesh, add_custom_shape_for_bone, create_deform_bones_collection, add_ik_fk_switch_property, add_copy_transforms_constraints_to_deform_bones_for_drivers, create_driver_bones, duplicate_bone, clear_parent, connect_bone_tail_to_head, extrude_bone, parent_bone_keep_offset, add_IK_constraint, add_copy_location_constraint, add_damped_track_constraint, add_track_to_constraint, add_copy_rotation_constraint, remove_constraint, move_constraint_to_top, move_edit_bone_by_vector, scale_edit_bone, create_bone_at_intersection, assign_bones_to_new_collection, set_bone_collection_visibility


""" main_bones = [
    "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l",
    "thigh_r", "calf_r", "foot_r", "ball_l",
    "pelvis",
    "spine_01", "spine_02", "spine_03", "spine_04", "spine_05",
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


armature = bpy.context.active_object


if not armature or armature.type != 'ARMATURE':
    print("Please select an armature object.")
    exit()

bpy.ops.object.mode_set(mode='EDIT')

armature_data = armature.data



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

def add_driver_to_constraint_influence(constraint, armature, property_name, invert=False):
    driver = constraint.driver_add("influence").driver
    driver.type = 'SCRIPTED'
    
    var = driver.variables.new()
    var.name = "ik_fk_switch"
    var.targets[0].id = armature
    var.targets[0].data_path = f'["{property_name}"]'
    
    driver.expression = "1 - ik_fk_switch" if invert else "ik_fk_switch"



def create_bone_collection(name):
    if name not in armature_data.collections:
        return armature_data.collections.new(name)
    else:
        print(f"Collection with name {name} already exists.")
    
def get_bone_collection(name):
    return armature_data.collections[name]

def create_driver_bones(armature, collection_name, driver_prefix):
    new_collection = create_bone_collection(collection_name)
    bpy.ops.object.mode_set(mode='OBJECT')
    deform_bone_collection = get_bone_collection("DEFORM_BONES")
    deform_bone_names = [bone.name for bone in deform_bone_collection.bones]

    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
  
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

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


def add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, driver_bone_collection_name, driver_prefix, add_transform_constraint_to_flipped_bones=True, add_driver_to_copy_transform_influence = False):
    bpy.ops.object.mode_set(mode='POSE')
    driver_bone_collection = get_bone_collection(driver_bone_collection_name)
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
                    add_driver_to_constraint_influence(copy_transform_constraint, armature, "IK_controls", invert=("FK" in driver_prefix))
                
                if add_transform_constraint_to_flipped_bones:
                    transform_constraint = deform_bone.constraints.new(type='TRANSFORM')
                    transform_constraint.name = f"{driver_prefix.replace('DRV_', '')}_Transform -> {bone.name}"
                    transform_constraint.target = armature
                    transform_constraint.subtarget = bone.name
                    transform_constraint.map_from = 'ROTATION'
                    transform_constraint.map_to = 'ROTATION'
                    transform_constraint.to_min_x_rot = 3.14159
                    if add_driver_to_copy_transform_influence:
                        add_driver_to_constraint_influence(transform_constraint, armature, "IK_controls", invert=("FK" in driver_prefix))
            else:
                copy_transform_constraint = deform_bone.constraints.new(type='COPY_TRANSFORMS')
                copy_transform_constraint.name = f"{driver_prefix.replace('DRV_', '')}_Copy Transforms -> {bone.name}"
                copy_transform_constraint.target = armature
                copy_transform_constraint.subtarget = bone.name
                
                if add_driver_to_copy_transform_influence:
                    add_driver_to_constraint_influence(copy_transform_constraint, armature, "IK_controls", invert=("FK" in driver_prefix))

            deform_bone.bone.select = False
            bone.select = False



def assign_bones_to_new_collection(armature, bone_names, new_collection_name, should_remove_from_previous_collections=True):
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.select_all(action='DESELECT')
    
    for bone_name in bone_names:
        bone = armature_data.edit_bones.get(bone_name)       
        if bone:
            armature_data.edit_bones[bone_name].select = True
            
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    
    if should_remove_from_previous_collections:
        for collection in armature_data.collections:
            bpy.ops.armature.collection_unassign(name=collection.name)
        
    

    new_collection = create_bone_collection(new_collection_name)
    print(f"new_collection: {new_collection}")
    
    if not new_collection:
        new_collection = armature_data.collections[new_collection_name]

    print(f"new_collection: {new_collection}")
    
    armature_data.collections.active = new_collection

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')

    bpy.ops.armature.collection_assign(name=new_collection_name)
    



def create_deform_bones_collection():
    deform_bone_collection = create_bone_collection("DEFORM_BONES")
    bpy.ops.armature.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.armature.collection_assign(name=deform_bone_collection.name)

    bpy.ops.armature.select_all(action='DESELECT')



def set_bone_collection_visibility(armature, collection_name, is_visible):
    bpy.ops.object.mode_set(mode='EDIT')
    bone_collection = get_bone_collection(collection_name)
    if bone_collection:
        armature_data.collections[bone_collection.name].is_visible = is_visible
    else:
        print(f"Collection with name {collection_name} not found.")

#_______________________________________________________________________________________________________________________

def create_curled_plane(name, width, height, curl_factor=1.3):
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

def duplicate_bone(armature, bone_name_to_duplicate, new_bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
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
    bone = armature_data.edit_bones.get(bone_name)
    bpy.ops.armature.select_all(action='DESELECT')
    if bone:
        bone.select = True
        armature_data.edit_bones.active = bone
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.transform.resize(value=scale_value)
        bpy.ops.armature.select_all(action='DESELECT')

def find_intersection_point(bone_name_1, bone_name_2):
    bpy.ops.object.mode_set(mode='EDIT')
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
    tail_bone = armature_data.edit_bones.get(tail_bone_name)
    head_bone = armature_data.edit_bones.get(head_bone_name)
    if tail_bone and head_bone:
        tail_bone.tail = head_bone.head


def create_bone_at_intersection(armature, bone_name_1, bone_name_2, translate_vector, new_bone_name):
    intersection_point = find_intersection_point(bone_name_1, bone_name_2)
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
        if new_bone and unparent:
            new_bone.select = True
            armature_data.edit_bones.active = new_bone
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.parent_clear(type='CLEAR')

def clear_parent(armature, bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    bone = armature_data.edit_bones.get(bone_name)
    if bone:
        bone.parent = None

def move_edit_bone_by_vector(armature, edit_bone_name, translate_vector):
    bpy.ops.object.mode_set(mode='EDIT')
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

def add_copy_location_constraint(armature, target_bone_name, source_bone_name, head_tail=1, target_space='WORLD', owner_space='WORLD', influence=1):
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

def create_custom_shape_mesh(shape, curled=False):
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
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name == mesh_name:
            return obj
    print(f"Mesh with name {mesh_name} not found.")
    return None
 
def add_mesh_to_collection(mesh, collection_name):
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
    pose_bone.bone.color.palette = f"THEME{theme_number}"
    if pose_bone:
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

 """
#_______________________________________________________________________________________________________________________
armature = bpy.context.active_object


if not armature or armature.type != 'ARMATURE':
    print("Please select an armature object.")
    exit()

bpy.ops.object.mode_set(mode='EDIT')


create_deform_bones_collection(armature)
add_ik_fk_switch_property(armature, "IK_controls")
create_driver_bones(armature, "IK_DRIVER_BONES", "DRV_IK")
create_driver_bones(armature, "FK_DRIVER_BONES", "DRV_FK")
add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, "IK_DRIVER_BONES", "DRV_IK", True, add_driver_to_copy_transform_influence=True)
add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, "FK_DRIVER_BONES", "DRV_FK", True, add_driver_to_copy_transform_influence=True)

duplicate_bone(armature, "center_of_mass", "CTRL_base")
clear_parent(armature, "CTRL_base")

connect_bone_tail_to_head(armature, "DRV_IK_lowerarm_l", "DRV_IK_hand_l")
connect_bone_tail_to_head(armature, "DRV_IK_lowerarm_r", "DRV_IK_hand_r")

extrude_bone(armature, "DRV_IK_hand_l", "CTRL_hand_l", (0, 20, 0))
parent_bone_keep_offset(armature, "DRV_IK_hand_l", "CTRL_hand_l")
extrude_bone(armature, "DRV_IK_lowerarm_l", "PT_elbow_l", (0, 20, 0))
move_edit_bone_by_vector(armature, "PT_elbow_l", (0, 30, 0))
add_IK_constraint(armature, "DRV_IK_lowerarm_l", "CTRL_hand_l", "PT_elbow_l", 2, 135)
add_copy_location_constraint(armature, "DRV_IK_hand_l", "DRV_IK_lowerarm_l", 1)

extrude_bone(armature, "DRV_IK_hand_r", "CTRL_hand_r", (0, 20, 0))
parent_bone_keep_offset(armature, "DRV_IK_hand_r", "CTRL_hand_r")
extrude_bone(armature, "DRV_IK_lowerarm_r", "PT_elbow_r", (0, 20, 0))
move_edit_bone_by_vector(armature, "PT_elbow_r", (0, 30, 0))
add_IK_constraint(armature, "DRV_IK_lowerarm_r", "CTRL_hand_r", "PT_elbow_r", 2)
add_copy_location_constraint(armature, "DRV_IK_hand_r", "DRV_IK_lowerarm_r", 1)

connect_bone_tail_to_head(armature, "DRV_IK_calf_r", "DRV_IK_foot_r")
extrude_bone(armature, "DRV_IK_foot_r", "foot_r_CTRL", (0, 20, 0))
parent_bone_keep_offset(armature, "DRV_IK_foot_r", "foot_r_CTRL")
extrude_bone(armature, "DRV_IK_calf_r", "PT_knee_r", (0, -20, 0))
move_edit_bone_by_vector(armature, "PT_knee_r", (0, -40, 0))
add_IK_constraint(armature, "DRV_IK_calf_r", "foot_r_CTRL", "PT_knee_r", 2, -172)
add_copy_location_constraint(armature, "DRV_IK_foot_r", "DRV_IK_calf_r", 1)

connect_bone_tail_to_head(armature, "DRV_IK_calf_l", "DRV_IK_foot_l")
extrude_bone(armature, "DRV_IK_foot_l", "foot_l_CTRL", (0, 20, 0))
parent_bone_keep_offset(armature, "DRV_IK_foot_l", "foot_l_CTRL")
extrude_bone(armature, "DRV_IK_calf_l", "PT_knee_l", (0, -20, 0))
move_edit_bone_by_vector(armature, "PT_knee_l", (0, -40, 0))
add_IK_constraint(armature, "DRV_IK_calf_l", "foot_l_CTRL", "PT_knee_l", 2, -8)
add_copy_location_constraint(armature, "DRV_IK_foot_l", "DRV_IK_calf_l", 1)

extrude_bone(armature, "DRV_IK_spine_01", "CTRL_center_of_gravity", (0, 20, 0))
parent_bone_keep_offset(armature, "DRV_IK_spine_01", "CTRL_center_of_gravity")
parent_bone_keep_offset(armature, "DRV_IK_pelvis", "CTRL_center_of_gravity")

duplicate_bone(armature, "DRV_IK_head", "CTRL_head")
move_edit_bone_by_vector(armature, "CTRL_head", (0, -30, 0))
clear_parent(armature, "CTRL_head")

duplicate_bone(armature, "DRV_IK_head", "MCH_head")
scale_edit_bone(armature, "MCH_head", (1.1, 1.1, 1.1))
parent_bone_keep_offset(armature, "DRV_IK_head", "MCH_head")
parent_bone_keep_offset(armature, "MCH_head", "DRV_IK_neck_02")
add_track_to_constraint(armature, "MCH_head", "CTRL_head", "X", "Y")
add_copy_rotation_constraint(armature, "DRV_IK_head", "CTRL_head", (1, 1, 1), "LOCAL", "LOCAL")

create_bone_at_intersection(armature, "DRV_IK_clavicle_l", "CTRL_hand_l", (0, 20, 0), "MCH_clavicle_target_l")
add_damped_track_constraint(armature, "DRV_IK_clavicle_l", "MCH_clavicle_target_l")
add_copy_location_constraint(armature, "MCH_clavicle_target_l", "CTRL_hand_l", 0, "LOCAL", "LOCAL", 0.3)

duplicate_bone(armature, "DRV_IK_clavicle_l", "MCH_clavicle_l")
scale_edit_bone(armature, "MCH_clavicle_l", (1.1, 1.1, 1.1))

parent_bone_keep_offset(armature, "DRV_IK_clavicle_l", "MCH_clavicle_l")
remove_constraint(armature, "DRV_IK_clavicle_l", "DAMPED_TRACK")

create_bone_at_intersection(armature, "DRV_IK_clavicle_r", "CTRL_hand_r", (0, 20, 0), "MCH_clavicle_target_r")
add_damped_track_constraint(armature, "DRV_IK_clavicle_r", "MCH_clavicle_target_r")
add_copy_location_constraint(armature, "MCH_clavicle_target_r", "CTRL_hand_r", 0, "LOCAL", "LOCAL", 0.3)

duplicate_bone(armature, "DRV_IK_clavicle_r", "MCH_clavicle_r")
scale_edit_bone(armature, "MCH_clavicle_r", (1.1, 1.1, 1.1))

parent_bone_keep_offset(armature, "DRV_IK_clavicle_r", "MCH_clavicle_r")
remove_constraint(armature, "DRV_IK_clavicle_r", "DAMPED_TRACK")

extrude_bone(armature, "DRV_IK_ball_l", "CTRL_PV_ball_l", (0, 0, 10))
parent_bone_keep_offset(armature, "CTRL_PV_ball_l", "DRV_IK_ball_l")
parent_bone_keep_offset(armature, "foot_l_CTRL", "CTRL_PV_ball_l")
clear_parent(armature, "DRV_IK_ball_l")

extrude_bone(armature, "DRV_IK_ball_r", "CTRL_PV_ball_r", (0, 0, 10))
parent_bone_keep_offset(armature, "CTRL_PV_ball_r", "DRV_IK_ball_r")
parent_bone_keep_offset(armature, "foot_r_CTRL", "CTRL_PV_ball_r")
clear_parent(armature, "DRV_IK_ball_r")




add_copy_rotation_constraint(armature, "DRV_IK_thumb_03_l", "DRV_IK_thumb_02_l", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_index_02_l", "DRV_IK_index_01_l", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_index_03_l", "DRV_IK_index_02_l", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_middle_02_l", "DRV_IK_middle_01_l", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_middle_03_l", "DRV_IK_middle_02_l", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_ring_02_l", "DRV_IK_ring_01_l", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_ring_03_l", "DRV_IK_ring_02_l", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_pinky_02_l", "DRV_IK_pinky_01_l", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_pinky_03_l", "DRV_IK_pinky_02_l", (0, 0, 1), "LOCAL", "LOCAL")


add_copy_rotation_constraint(armature, "DRV_IK_thumb_03_r", "DRV_IK_thumb_02_r", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_index_02_r", "DRV_IK_index_01_r", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_index_03_r", "DRV_IK_index_02_r", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_middle_02_r", "DRV_IK_middle_01_r", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_middle_03_r", "DRV_IK_middle_02_r", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_ring_02_r", "DRV_IK_ring_01_r", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_ring_03_r", "DRV_IK_ring_02_r", (0, 0, 1), "LOCAL", "LOCAL")

add_copy_rotation_constraint(armature, "DRV_IK_pinky_02_r", "DRV_IK_pinky_01_r", (0, 0, 1), "LOCAL", "LOCAL")
add_copy_rotation_constraint(armature, "DRV_IK_pinky_03_r", "DRV_IK_pinky_02_r", (0, 0, 1), "LOCAL", "LOCAL")


remove_constraint(armature, "ball_l", "COPY_TRANSFORMS")
add_copy_rotation_constraint(armature, "ball_l", "DRV_IK_ball_l", (1, 1, 1), "WORLD", "WORLD")
move_constraint_to_top(armature, "ball_l", "Copy Rotation")


remove_constraint(armature, "ball_r", "COPY_TRANSFORMS")
add_copy_rotation_constraint(armature, "ball_r", "DRV_IK_ball_r", (1, 1, 1), "WORLD", "WORLD")
move_constraint_to_top(armature, "ball_r", "Copy Rotation")




# Parenting all MCH and CTRL bones to the CTRL_base bone
parent_bone_keep_offset(armature, "MCH_clavicle_target_l", "CTRL_base")
parent_bone_keep_offset(armature, "MCH_clavicle_target_r", "CTRL_base")
parent_bone_keep_offset(armature, "CTRL_center_of_gravity", "CTRL_base")
parent_bone_keep_offset(armature, "CTRL_head", "CTRL_base")
parent_bone_keep_offset(armature, "CTRL_hand_l", "CTRL_base")
parent_bone_keep_offset(armature, "CTRL_hand_r", "CTRL_base")
parent_bone_keep_offset(armature, "PT_elbow_r", "CTRL_base")
parent_bone_keep_offset(armature, "PT_knee_r", "CTRL_base")
parent_bone_keep_offset(armature, "PT_elbow_l", "CTRL_base")
parent_bone_keep_offset(armature, "PT_knee_l", "CTRL_base")
parent_bone_keep_offset(armature, "DRV_IK_ball_l", "CTRL_base")
parent_bone_keep_offset(armature, "DRV_IK_ball_r", "CTRL_base")




####################### Adding all custom shapes to the control rig bones

create_custom_shape_mesh("cube")
create_custom_shape_mesh("circle")
create_custom_shape_mesh("sphere")
create_custom_shape_mesh("plane", curled=True)

add_custom_shape_for_bone(armature, "CTRL_base", "circle", "14", wireframe=False, scale=[50,50,50], mode="IK")

add_custom_shape_for_bone(armature, "CTRL_head", "sphere", "01", wireframe=False, scale=[5,5,5], mode="IK")

add_custom_shape_for_bone(armature, "PT_elbow_l", "sphere", "05", wireframe=True, scale=[5,5,5], mode="IK")
add_custom_shape_for_bone(armature, "PT_elbow_r", "sphere", "05", wireframe=True, scale=[5,5,5], mode="IK")

add_custom_shape_for_bone(armature, "PT_knee_l", "sphere", "11", wireframe=True, scale=[5,5,5], mode="IK")
add_custom_shape_for_bone(armature, "PT_knee_r", "sphere", "11", wireframe=True, scale=[5,5,5], mode="IK")

add_custom_shape_for_bone(armature, "CTRL_center_of_gravity", "cube", "09", wireframe=True, scale=[ 20,30,40], mode="IK")


add_custom_shape_for_bone(armature, "DRV_IK_neck_01", "sphere", "04", wireframe=True, scale=[ 2,2,2], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_neck_02", "sphere", "04", wireframe=True, scale=[ 2,2,2], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_spine_01", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_spine_02", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_spine_03", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_spine_04", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_spine_05", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode="IK")

add_custom_shape_for_bone(armature, "DRV_IK_ball_r", "circle", "02", wireframe=True, scale=[5,10,0], translation=[-1.5, -12, -1], rotation=[0,90,0], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_ball_l", "circle", "02", wireframe=True, scale=[5,10,0], translation=[-1.5, -12, -1], rotation=[0,90,0], mode="IK")
add_custom_shape_for_bone(armature, "CTRL_PV_ball_r", "circle", "02", wireframe=True, scale=[5,5,5], translation=[0, -1.5, 0], rotation=[90,0,0], mode="IK")
add_custom_shape_for_bone(armature, "CTRL_PV_ball_l", "circle", "02", wireframe=True, scale=[5,5,5], translation=[0, -1.5, 0], rotation=[90,0,0], mode="IK")

add_custom_shape_for_bone(armature, "DRV_IK_thumb_02_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_index_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_middle_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_ring_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_pinky_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")

add_custom_shape_for_bone(armature, "CTRL_hand_l", "cube", "02", wireframe=True, scale=[ 15,8,1], translation=[10, -3, 5], rotation=[0,10,-10], mode="IK")

add_custom_shape_for_bone(armature, "DRV_IK_thumb_02_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_index_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_middle_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_ring_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_pinky_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode="IK")

add_custom_shape_for_bone(armature, "CTRL_hand_r", "cube", "02", wireframe=True, scale=[ 15,8,1], translation=[-10, 3, 5], rotation=[0,-10,10], mode="IK")

add_custom_shape_for_bone(armature, "DRV_IK_clavicle_l", "curled_plane", "02", wireframe=True, scale=[5,10,10], translation=[0, 10, 8.5], rotation=[0,15,90], mode="IK")
add_custom_shape_for_bone(armature, "DRV_IK_clavicle_r", "curled_plane", "02", wireframe=True, scale=[5,10,10], translation=[0, 10, 8.5], rotation=[0,15,90], mode="IK")



assign_bones_to_new_collection(armature, ["MCH_head", "MCH_clavicle_l", "MCH_clavicle_target_l", "MCH_clavicle_r", "MCH_clavicle_target_r"], "MCH_BONES")

add_custom_shape_for_bone(armature, "DRV_FK_thumb_02_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_thumb_02_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_thumb_03_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_thumb_03_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_index_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_index_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_index_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_middle_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ring_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_pinky_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_clavicle_l", "sphere", "03", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_upperarm_l", "sphere", "12", wireframe=True, scale=[5,5,5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_lowerarm_l", "sphere", "03", wireframe=True, scale=[3,3,3], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_hand_l", "sphere", "12", wireframe=True, scale=[2,2,2], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_clavicle_r", "sphere", "03", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_upperarm_r", "sphere", "12", wireframe=True, scale=[5,5,5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_lowerarm_r", "sphere", "03", wireframe=True, scale=[3,3,3], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_hand_r", "sphere", "12", wireframe=True, scale=[2,2,2], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_thigh_l", "sphere", "03", wireframe=True, scale=[5,5,5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_calf_l", "sphere", "03", wireframe=True, scale=[5,5,5], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_foot_l", "sphere", "07", wireframe=True, scale=[3,3,3], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ball_l", "sphere", "07", wireframe=True, scale=[2,2,2], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_thigh_r", "sphere", "03", wireframe=True, scale=[5,5,5], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_calf_r", "sphere", "03", wireframe=True, scale=[5,5,5], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_foot_r", "sphere", "07", wireframe=True, scale=[3,3,3], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_ball_r", "sphere", "07", wireframe=True, scale=[2,2,2], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_pelvis", "sphere", "04", wireframe=True, scale=[3,3,3], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_spine_01", "sphere", "03", wireframe=True, scale=[2,2,2], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_spine_02", "sphere", "03", wireframe=True, scale=[2,2,2], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_spine_03", "sphere", "03", wireframe=True, scale=[2,2,2], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_spine_04", "sphere", "03", wireframe=True, scale=[2,2,2], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_spine_05", "sphere", "03", wireframe=True, scale=[3,3,3], mode="FK")

add_custom_shape_for_bone(armature, "DRV_FK_neck_01", "sphere", "12", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_neck_02", "sphere", "12", wireframe=True, scale=[1,1,1], mode="FK")
add_custom_shape_for_bone(armature, "DRV_FK_head", "sphere", "07", wireframe=True, scale=[5,5,5], mode="FK")


assign_bones_to_new_collection(armature, [
"DRV_FK_index_metacarpal_r",
"DRV_FK_middle_metacarpal_r",
"DRV_FK_ring_metacarpal_r",
"DRV_FK_pinky_metacarpal_r",
"DRV_FK_index_metacarpal_l",
"DRV_FK_middle_metacarpal_l",
"DRV_FK_ring_metacarpal_l",
"DRV_FK_pinky_metacarpal_l",
"DRV_FK_thumb_02_r",
"DRV_FK_index_01_r",
"DRV_FK_middle_01_r",
"DRV_FK_ring_01_r",
"DRV_FK_pinky_01_r",
"DRV_FK_thumb_02_l",
"DRV_FK_index_01_l",
"DRV_FK_middle_01_l",
"DRV_FK_ring_01_l",
"DRV_FK_pinky_01_l",
"DRV_FK_thumb_03_r",
"DRV_FK_index_02_r",
"DRV_FK_middle_02_r",
"DRV_FK_ring_02_r",
"DRV_FK_pinky_02_r",
"DRV_FK_thumb_03_l",
"DRV_FK_index_02_l",
"DRV_FK_middle_02_l",
"DRV_FK_ring_02_l",
"DRV_FK_pinky_02_l",
"DRV_FK_index_03_r",
"DRV_FK_middle_03_r",
"DRV_FK_ring_03_r",
"DRV_FK_pinky_03_r",
"DRV_FK_index_03_l",
"DRV_FK_middle_03_l",
"DRV_FK_ring_03_l",
"DRV_FK_pinky_03_l",
"DRV_FK_clavicle_l",
"DRV_FK_upperarm_l",
"DRV_FK_lowerarm_l",
"DRV_FK_hand_l",
"DRV_FK_clavicle_r",
"DRV_FK_upperarm_r",
"DRV_FK_lowerarm_r",
"DRV_FK_hand_r",
"DRV_FK_thigh_l",
"DRV_FK_calf_l",
"DRV_FK_foot_l",
"DRV_FK_ball_l",
"DRV_FK_thigh_r",
"DRV_FK_calf_r",
"DRV_FK_foot_r",
"DRV_FK_ball_r",
"DRV_FK_pelvis",
"DRV_FK_spine_01",
"DRV_FK_spine_02",
"DRV_FK_spine_03",
"DRV_FK_spine_04",
"DRV_FK_spine_05",
"DRV_FK_neck_01",
"DRV_FK_neck_02",
"DRV_FK_head"
],"CONTROL_RIG", False)

assign_bones_to_new_collection(armature, [
"CTRL_base",
"CTRL_head",
"DRV_IK_neck_01",
"DRV_IK_neck_02",
"DRV_IK_spine_01",
"DRV_IK_spine_02",
"DRV_IK_spine_03",
"DRV_IK_spine_04",
"DRV_IK_spine_05",
"CTRL_hand_l",
"CTRL_hand_r",
"PT_elbow_l",
"PT_elbow_r",
"DRV_IK_thumb_02_l",
"DRV_IK_index_01_l",
"DRV_IK_middle_01_l",
"DRV_IK_ring_01_l",
"DRV_IK_pinky_01_l",
"DRV_IK_thumb_02_r",
"DRV_IK_index_01_r",
"DRV_IK_middle_01_r",
"DRV_IK_ring_01_r",
"DRV_IK_pinky_01_r",
"CTRL_center_of_gravity",
"PT_knee_l",
"PT_knee_r",
"CTRL_PV_ball_l",
"CTRL_PV_ball_r",
"DRV_IK_ball_r",
"DRV_IK_ball_l",
"DRV_IK_clavicle_l",
"DRV_IK_clavicle_r"
], "CONTROL_RIG")

set_bone_collection_visibility(armature, "DEFORM_BONES", False)
set_bone_collection_visibility(armature, "IK_DRIVER_BONES", False)
set_bone_collection_visibility(armature, "FK_DRIVER_BONES", False)
set_bone_collection_visibility(armature, "MCH_BONES", False)

bpy.ops.object.mode_set(mode='POSE')