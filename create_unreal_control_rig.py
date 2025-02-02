import bpy

from.utils.create_control_rig_utils import create_custom_shape_mesh, add_custom_shape_for_bone, create_deform_bones_collection, add_ik_fk_switch_property, add_copy_transforms_constraints_to_deform_bones_for_drivers, create_driver_bones, duplicate_bone, clear_parent, connect_bone_tail_to_head, extrude_bone, parent_bone_keep_offset, add_IK_constraint, add_copy_location_constraint, add_damped_track_constraint, add_track_to_constraint, add_copy_rotation_constraint, remove_constraint, move_constraint_to_top, move_edit_bone_by_vector, scale_edit_bone, create_bone_at_intersection, assign_bones_to_new_collection, set_bone_collection_visibility, get_bone_collection, add_driver_bone_constraints_to_collection_of_bones, apply_fk_transforms, apply_ik_transforms, add_copy_rotation_constraint_with_driver, add_copy_location_constraint_with_driver, add_copy_transforms_constraint_with_driver
#TBD: Clean up this incredible mess

def snap_to_IK(armature):
    if armature.type != 'ARMATURE':
        print("Provided object is not an armature.")
        return
    apply_fk_transforms(armature)
    print("FK bones successfully snapped to IK bones.")

def snap_to_FK(armature):
    if armature.type != 'ARMATURE':
        print("Provided object is not an armature.")
        return
    apply_ik_transforms(armature)
    print("IK bones successfully snapped to FK bones.")


def generate_rig(armature, ik=True, fk=False, snap=False):

    if not armature or armature.type != 'ARMATURE':
        print("Please select an armature object.")
        exit()

    bpy.ops.object.mode_set(mode='EDIT')
    driverSnapToIk = {"property_name": "IK_controls", "invert" : False}
    driverSnapToFk = {"property_name": "IK_controls", "invert" : True}

    create_custom_shape_mesh("cube")
    create_custom_shape_mesh("circle")
    create_custom_shape_mesh("sphere")
    create_custom_shape_mesh("plane", curled=True)
    create_deform_bones_collection(armature)

    # Add copy location and rotation constraints for the hand ik bones
    add_copy_location_constraint(armature, "ik_hand_l", "hand_l")
    add_copy_rotation_constraint(armature, "ik_hand_l", "hand_l")

    add_copy_location_constraint(armature, "ik_hand_r", "hand_r")
    add_copy_rotation_constraint(armature, "ik_hand_r", "hand_r")

    add_copy_location_constraint(armature, "ik_hand_gun", "hand_r")
    add_copy_location_constraint(armature, "ik_hand_gun", "hand_r")
    
    if(ik and fk):
        add_ik_fk_switch_property(armature, "IK_controls")

    if(ik):
        shape_mode = "IK" if ik and fk else None
        print(f"Generating IK rig. Shape mode: {shape_mode}")
        generate_ik_rig(armature, shape_mode)
    if(fk):
        shape_mode = "FK" if ik and fk else None
        print(f"Generating FK rig. Shape mode: {shape_mode}")
        generate_fk_rig(armature, shape_mode)
    
    
    if (ik and fk and snap):
        add_driver_bone_constraints_to_collection_of_bones(armature, "IK_DRIVER_BONES", "DRV_IK", "FK_DRIVER_BONES", "DRV_FK", False, driverSnapToIk)
        add_driver_bone_constraints_to_collection_of_bones(armature, "FK_DRIVER_BONES", "DRV_FK", "IK_DRIVER_BONES", "DRV_IK", False, driverSnapToFk)

        duplicate_bone(armature, "CTRL_head", "SNAP_CTRL_head")
        clear_parent(armature, "SNAP_CTRL_head")
        parent_bone_keep_offset(armature, "SNAP_CTRL_head", "DRV_FK_head")

        ################################ Creat faux pole targets ##############################

        duplicate_bone(armature, "PT_elbow_r", "SNAP_PT_elbow_r")
        clear_parent(armature, "SNAP_PT_elbow_r")
        parent_bone_keep_offset(armature, "SNAP_PT_elbow_r", "DRV_FK_lowerarm_r")

        duplicate_bone(armature, "PT_elbow_l", "SNAP_PT_elbow_l")
        clear_parent(armature, "SNAP_PT_elbow_l")
        parent_bone_keep_offset(armature, "SNAP_PT_elbow_l", "DRV_FK_lowerarm_l")

        duplicate_bone(armature, "PT_knee_l", "SNAP_PT_knee_l")
        clear_parent(armature, "SNAP_PT_knee_l")
        parent_bone_keep_offset(armature, "SNAP_PT_knee_l", "DRV_FK_calf_l")

        duplicate_bone(armature, "PT_knee_r", "SNAP_PT_knee_r")
        clear_parent(armature, "SNAP_PT_knee_r")
        parent_bone_keep_offset(armature, "SNAP_PT_knee_r", "DRV_FK_calf_r")

        duplicate_bone(armature, "MCH_clavicle_target_l", "SNAP_clavicle_target_l")
        clear_parent(armature, "SNAP_clavicle_target_l")
        add_copy_location_constraint(armature ,"SNAP_clavicle_target_l", "SNAP_CTRL_hand_l", 1, "LOCAL", "LOCAL", 0.3)

        duplicate_bone(armature, "MCH_clavicle_target_r", "SNAP_clavicle_target_r")
        clear_parent(armature, "SNAP_clavicle_target_r")
        add_copy_location_constraint(armature ,"SNAP_clavicle_target_r", "SNAP_CTRL_hand_r", 1, "LOCAL", "LOCAL", 0.3)

        ################################ Create faux ctrl bones ##############################

        duplicate_bone(armature, "CTRL_hand_l", "SNAP_CTRL_hand_l")
        clear_parent(armature, "SNAP_CTRL_hand_l")
        parent_bone_keep_offset(armature, "SNAP_CTRL_hand_l", "DRV_FK_hand_l")

        duplicate_bone(armature, "CTRL_hand_r", "SNAP_CTRL_hand_r")
        clear_parent(armature, "SNAP_CTRL_hand_r")
        parent_bone_keep_offset(armature, "SNAP_CTRL_hand_r", "DRV_FK_hand_r")

        duplicate_bone(armature, "CTRL_PV_ball_l", "SNAP_CTRL_PV_ball_l")
        clear_parent(armature, "SNAP_CTRL_PV_ball_l")
        parent_bone_keep_offset(armature, "SNAP_CTRL_PV_ball_l", "DRV_FK_ball_l")

        duplicate_bone(armature, "CTRL_PV_ball_r", "SNAP_CTRL_PV_ball_r")
        clear_parent(armature, "SNAP_CTRL_PV_ball_r")
        parent_bone_keep_offset(armature, "SNAP_CTRL_PV_ball_r", "DRV_FK_ball_r")

        duplicate_bone(armature, "CTRL_center_of_gravity", "SNAP_CTRL_center_of_gravity")
        clear_parent(armature, "SNAP_CTRL_center_of_gravity")
        parent_bone_keep_offset(armature, "SNAP_CTRL_center_of_gravity", "DRV_FK_pelvis")

        ################################ Create faux ctrl bones ##############################

        assign_bones_to_new_collection(armature, ["SNAP_PT_knee_l","SNAP_PT_knee_r","SNAP_PT_elbow_l","SNAP_PT_elbow_r","SNAP_CTRL_head", "SNAP_CTRL_PV_ball_l", "SNAP_CTRL_PV_ball_r", "SNAP_CTRL_center_of_gravity", "SNAP_CTRL_hand_l", "SNAP_CTRL_hand_r"],"SNAP_DRIVER_BONES", True)


        ################################ Add copy transform with driver to the faux pole target bones ##############################
        add_copy_location_constraint_with_driver(armature, "CTRL_head" ,"SNAP_CTRL_head", "Copy SNAP Location -> SNAP_CTRL_head", driver=driverSnapToFk)
        add_copy_rotation_constraint_with_driver(armature, "CTRL_head" ,"SNAP_CTRL_head", "Copy SNAP Rotation -> SNAP_CTRL_head", driver=driverSnapToFk)

        add_copy_location_constraint_with_driver(armature, "PT_elbow_r" ,"SNAP_PT_elbow_r", "Copy SNAP Location -> SNAP_PT_elbow_r", driver=driverSnapToFk)
        add_copy_location_constraint_with_driver(armature, "PT_elbow_l" ,"SNAP_PT_elbow_l", "Copy SNAP Location -> SNAP_PT_elbow_l", driver=driverSnapToFk)
        add_copy_location_constraint_with_driver(armature, "PT_knee_r" ,"SNAP_PT_knee_r", "Copy SNAP Location -> SNAP_PT_knee_r", driver=driverSnapToFk)
        add_copy_location_constraint_with_driver(armature, "PT_knee_l" ,"SNAP_PT_knee_l", "Copy SNAP Location -> SNAP_PT_knee_l", driver=driverSnapToFk)

        add_copy_transforms_constraint_with_driver(armature, "CTRL_hand_l", "SNAP_CTRL_hand_l", 'Copy SNAP Transforms -> SNAP_CTRL_hand_l', driver=driverSnapToFk)
        add_copy_transforms_constraint_with_driver(armature, "CTRL_hand_r", "SNAP_CTRL_hand_r", 'Copy SNAP Transforms -> SNAP_CTRL_hand_r', driver=driverSnapToFk)

        add_copy_transforms_constraint_with_driver(armature, "CTRL_PV_ball_l", "SNAP_CTRL_PV_ball_l", 'Copy SNAP Transforms -> SNAP_CTRL_PV_ball_l', driver=driverSnapToFk)
        add_copy_transforms_constraint_with_driver(armature, "CTRL_PV_ball_r", "SNAP_CTRL_PV_ball_r", 'Copy SNAP Transforms -> SNAP_CTRL_PV_ball_r', driver=driverSnapToFk)

        add_copy_transforms_constraint_with_driver(armature, "CTRL_center_of_gravity", "SNAP_CTRL_center_of_gravity", 'Copy SNAP Transforms -> SNAP_CTRL_center_of_gravity', driver=driverSnapToFk)

        add_copy_transforms_constraint_with_driver(armature, "MCH_clavicle_target_r", "SNAP_clavicle_target_r", 'Copy SNAP Transforms -> SNAP_clavicle_target_r', driver=driverSnapToFk)
        add_copy_transforms_constraint_with_driver(armature, "MCH_clavicle_target_l", "SNAP_clavicle_target_l", 'Copy SNAP Transforms -> SNAP_clavicle_target_l', driver=driverSnapToFk)

        set_bone_collection_visibility(armature, "SNAP_DRIVER_BONES", False)


    set_bone_collection_visibility(armature, "DEFORM_BONES", False)

    bpy.ops.object.mode_set(mode='POSE')

def generate_fk_rig(armature, shape_mode = None):
    create_driver_bones(armature, "FK_DRIVER_BONES", "DRV_FK")
    add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, "FK_DRIVER_BONES", "DRV_FK", True, add_driver_to_copy_transform_influence=True)

    add_custom_shape_for_bone(armature, "DRV_FK_thumb_02_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_01_r", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_thumb_02_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_01_l", "sphere", "07", wireframe=True, scale=[1,1,1], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_thumb_03_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_02_r", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_thumb_03_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_02_l", "sphere", "03", wireframe=True, scale=[0.7,0.7,0.7], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_index_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_03_r", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_03_l", "sphere", "12", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_index_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_metacarpal_r", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_index_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_middle_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ring_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_pinky_metacarpal_l", "sphere", "03", wireframe=True, scale=[0.5,0.5,0.5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_clavicle_l", "sphere", "03", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_upperarm_l", "sphere", "12", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_lowerarm_l", "sphere", "03", wireframe=True, scale=[3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_hand_l", "sphere", "12", wireframe=True, scale=[2,2,2], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_clavicle_r", "sphere", "03", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_upperarm_r", "sphere", "12", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_lowerarm_r", "sphere", "03", wireframe=True, scale=[3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_hand_r", "sphere", "12", wireframe=True, scale=[2,2,2], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_thigh_l", "sphere", "03", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_calf_l", "sphere", "03", wireframe=True, scale=[5,5,5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_foot_l", "sphere", "07", wireframe=True, scale=[3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ball_l", "sphere", "07", wireframe=True, scale=[2,2,2], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_thigh_r", "sphere", "03", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_calf_r", "sphere", "03", wireframe=True, scale=[5,5,5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_foot_r", "sphere", "07", wireframe=True, scale=[3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_ball_r", "sphere", "07", wireframe=True, scale=[2,2,2], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_pelvis", "sphere", "04", wireframe=True, scale=[3,3,3], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_spine_01", "sphere", "03", wireframe=True, scale=[2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_spine_02", "sphere", "03", wireframe=True, scale=[2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_spine_03", "sphere", "03", wireframe=True, scale=[2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_spine_04", "sphere", "03", wireframe=True, scale=[2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_spine_05", "sphere", "03", wireframe=True, scale=[3,3,3], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_FK_neck_01", "sphere", "12", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_neck_02", "sphere", "12", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_FK_head", "sphere", "07", wireframe=True, scale=[5,5,5], mode=shape_mode)

    set_bone_collection_visibility(armature, "FK_DRIVER_BONES", False)
    assign_bones_to_new_collection(armature, [ "DRV_FK_index_metacarpal_r", "DRV_FK_middle_metacarpal_r", "DRV_FK_ring_metacarpal_r", "DRV_FK_pinky_metacarpal_r", "DRV_FK_index_metacarpal_l", "DRV_FK_middle_metacarpal_l", "DRV_FK_ring_metacarpal_l", "DRV_FK_pinky_metacarpal_l", "DRV_FK_thumb_02_r", "DRV_FK_index_01_r", "DRV_FK_middle_01_r", "DRV_FK_ring_01_r", "DRV_FK_pinky_01_r", "DRV_FK_thumb_02_l", "DRV_FK_index_01_l", "DRV_FK_middle_01_l", "DRV_FK_ring_01_l", "DRV_FK_pinky_01_l", "DRV_FK_thumb_03_r", "DRV_FK_index_02_r", "DRV_FK_middle_02_r", "DRV_FK_ring_02_r", "DRV_FK_pinky_02_r", "DRV_FK_thumb_03_l", "DRV_FK_index_02_l", "DRV_FK_middle_02_l", "DRV_FK_ring_02_l", "DRV_FK_pinky_02_l", "DRV_FK_index_03_r", "DRV_FK_middle_03_r", "DRV_FK_ring_03_r", "DRV_FK_pinky_03_r", "DRV_FK_index_03_l", "DRV_FK_middle_03_l", "DRV_FK_ring_03_l", "DRV_FK_pinky_03_l", "DRV_FK_clavicle_l", "DRV_FK_upperarm_l", "DRV_FK_lowerarm_l", "DRV_FK_hand_l", "DRV_FK_clavicle_r", "DRV_FK_upperarm_r", "DRV_FK_lowerarm_r", "DRV_FK_hand_r", "DRV_FK_thigh_l", "DRV_FK_calf_l", "DRV_FK_foot_l", "DRV_FK_ball_l", "DRV_FK_thigh_r", "DRV_FK_calf_r", "DRV_FK_foot_r", "DRV_FK_ball_r", "DRV_FK_pelvis", "DRV_FK_spine_01", "DRV_FK_spine_02", "DRV_FK_spine_03", "DRV_FK_spine_04", "DRV_FK_spine_05", "DRV_FK_neck_01", "DRV_FK_neck_02", "DRV_FK_head"
    ],"CONTROL_RIG", False)



def generate_ik_rig(armature, shape_mode):
    create_driver_bones(armature, "IK_DRIVER_BONES", "DRV_IK")
    add_copy_transforms_constraints_to_deform_bones_for_drivers(armature, "IK_DRIVER_BONES", "DRV_IK", True, add_driver_to_copy_transform_influence=True)

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
    
    
    add_custom_shape_for_bone(armature, "CTRL_base", "circle", "14", wireframe=False, scale=[50,50,50], mode=shape_mode)

    add_custom_shape_for_bone(armature, "CTRL_head", "sphere", "01", wireframe=False, scale=[5,5,5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "PT_elbow_l", "sphere", "05", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "PT_elbow_r", "sphere", "05", wireframe=True, scale=[5,5,5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "PT_knee_l", "sphere", "11", wireframe=True, scale=[5,5,5], mode=shape_mode)
    add_custom_shape_for_bone(armature, "PT_knee_r", "sphere", "11", wireframe=True, scale=[5,5,5], mode=shape_mode)

    add_custom_shape_for_bone(armature, "CTRL_center_of_gravity", "cube", "09", wireframe=True, scale=[ 20,30,40], mode=shape_mode)


    add_custom_shape_for_bone(armature, "DRV_IK_neck_01", "sphere", "04", wireframe=True, scale=[ 2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_neck_02", "sphere", "04", wireframe=True, scale=[ 2,2,2], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_spine_01", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_spine_02", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_spine_03", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_spine_04", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_spine_05", "sphere", "06", wireframe=True, scale=[ 3,3,3], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_IK_ball_r", "circle", "02", wireframe=True, scale=[5,10,0], translation=[-1.5, -12, -1], rotation=[0,90,0], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_ball_l", "circle", "02", wireframe=True, scale=[5,10,0], translation=[-1.5, -12, -1], rotation=[0,90,0], mode=shape_mode)
    add_custom_shape_for_bone(armature, "CTRL_PV_ball_r", "circle", "02", wireframe=True, scale=[5,5,5], translation=[0, -1.5, 0], rotation=[90,0,0], mode=shape_mode)
    add_custom_shape_for_bone(armature, "CTRL_PV_ball_l", "circle", "02", wireframe=True, scale=[5,5,5], translation=[0, -1.5, 0], rotation=[90,0,0], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_IK_thumb_02_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_index_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_middle_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_ring_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_pinky_01_l", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)

    add_custom_shape_for_bone(armature, "CTRL_hand_l", "cube", "02", wireframe=True, scale=[ 15,8,1], translation=[10, -3, 5], rotation=[0,10,-10], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_IK_thumb_02_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_index_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_middle_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_ring_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_pinky_01_r", "sphere", "04", wireframe=True, scale=[1,1,1], mode=shape_mode)

    add_custom_shape_for_bone(armature, "CTRL_hand_r", "cube", "02", wireframe=True, scale=[ 15,8,1], translation=[-10, 3, 5], rotation=[0,-10,10], mode=shape_mode)

    add_custom_shape_for_bone(armature, "DRV_IK_clavicle_l", "curled_plane", "02", wireframe=True, scale=[5,10,10], translation=[0, 10, 8.5], rotation=[0,15,90], mode=shape_mode)
    add_custom_shape_for_bone(armature, "DRV_IK_clavicle_r", "curled_plane", "02", wireframe=True, scale=[5,10,10], translation=[0, 10, 8.5], rotation=[0,15,90], mode=shape_mode)



    assign_bones_to_new_collection(armature, ["PT_knee_l","PT_knee_r","PT_elbow_l","PT_elbow_r","CTRL_head", "CTRL_PV_ball_l", "CTRL_PV_ball_r", "CTRL_center_of_gravity", "CTRL_hand_l", "CTRL_hand_r"],"IK_CTRL_BONES", False)
    assign_bones_to_new_collection(armature, ["MCH_head", "MCH_clavicle_l", "MCH_clavicle_target_l", "MCH_clavicle_r", "MCH_clavicle_target_r"], "MCH_BONES", False)
    assign_bones_to_new_collection(armature, [ "CTRL_base", "CTRL_head", "DRV_IK_neck_01", "DRV_IK_neck_02", "DRV_IK_spine_01", "DRV_IK_spine_02", "DRV_IK_spine_03", "DRV_IK_spine_04", "DRV_IK_spine_05", "CTRL_hand_l", "CTRL_hand_r", "PT_elbow_l", "PT_elbow_r", "DRV_IK_thumb_02_l", "DRV_IK_index_01_l", "DRV_IK_middle_01_l", "DRV_IK_ring_01_l", "DRV_IK_pinky_01_l", "DRV_IK_thumb_02_r", "DRV_IK_index_01_r", "DRV_IK_middle_01_r", "DRV_IK_ring_01_r", "DRV_IK_pinky_01_r", "CTRL_center_of_gravity", "PT_knee_l", "PT_knee_r", "CTRL_PV_ball_l", "CTRL_PV_ball_r", "DRV_IK_ball_r", "DRV_IK_ball_l", "DRV_IK_clavicle_l", "DRV_IK_clavicle_r"
    ], "CONTROL_RIG", False)

    set_bone_collection_visibility(armature, "IK_DRIVER_BONES", False)
    set_bone_collection_visibility(armature, "MCH_BONES", False)



class IK_FK_Properties(bpy.types.PropertyGroup):

    ik_fk_switch: bpy.props.BoolProperty(
        name="IK/FK Switch",
        description="Toggle between IK and FK",
        default=True
    ) # type: ignore
    generate_fk: bpy.props.BoolProperty(
        name="generate_FK",
        description="Boolean to determine whether to generate FK or not",
        default=False
    ) # type: ignore

    generate_ik: bpy.props.BoolProperty(
        name="generate_IK",
        description="Boolean to determine whether to generate IK controls or not",
        default=True
    ) # type: ignore
    
    add_ik_fk_snap: bpy.props.BoolProperty(
        name="add_ik_fk_snap",
        description="Boolean to determine whether to have a IK/FK switch",
        default=True
    ) # type: ignore
    

class OBJECT_PT_control_rig_panel(bpy.types.Panel):
    bl_label = "Control Rig"
    bl_idname = "OBJECT_PT_control_rig_panel"
    bl_parent_id = "OBJECT_PT_skeleswap_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        panel_props = scene.ik_fk_panel_props

        row = layout.row()
        row.prop(panel_props, "generate_ik", text="Generate IK")
        row.prop(panel_props, "generate_fk", text="Generate FK")
        if panel_props.generate_fk and panel_props.generate_ik:
            row = layout.row()
            row.prop(panel_props, "add_ik_fk_snap", text="Add IK/FK Snap")
            

        row = layout.row()
        row.operator("object.generate_rig", text="Generate Rig" )
        
        if panel_props.generate_ik and panel_props.generate_fk:
            row = layout.row()
            row.label(text="Switch IK/FK Mode:")
            row = layout.row()
            row.operator("object.switch_ik_fk", text="IK Mode", depress=panel_props.ik_fk_switch ).mode = 'IK'
            row.operator("object.switch_ik_fk", text="FK Mode", depress=not panel_props.ik_fk_switch ).mode = 'FK'


class OBJECT_OT_Switch_IK_FK(bpy.types.Operator):
    bl_idname = "object.switch_ik_fk"
    bl_label = "Control Rig"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: bpy.props.EnumProperty(
        items=[
            ('IK', "IK Mode", "Switch to IK Mode"),
            ('FK', "FK Mode", "Switch to FK Mode")
        ],
        name="IK/FK Mode"
    ) # type: ignore

    def execute(self, context):
        panel_props = context.scene.ik_fk_panel_props
        armature = context.scene.target_armature
        is_ik = self.mode == 'IK'
        panel_props.ik_fk_switch = is_ik
        
        if is_ik:
            print('yay now IK')
            if panel_props.add_ik_fk_snap:
                snap_to_FK(armature)
            armature["IK_controls"] = is_ik
            print(f"IS_IK: {is_ik}")
        else:
            print('yay now FK')
            if panel_props.add_ik_fk_snap:
                snap_to_IK(armature)
            armature["IK_controls"] = is_ik
            print(f"IS_IK: {is_ik}")

        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='POSE')
        self.report({'INFO'}, f"Switched to {self.mode} mode.")
        return {'FINISHED'}

class OBJECT_OT_generate_rig(bpy.types.Operator):
    bl_idname = "object.generate_rig"
    bl_label = "Generates control rig"
    bl_options = {'REGISTER', 'UNDO'}
    

    def execute(self, context):
        armature = context.scene.target_armature     
        scene = context.scene
        panel_props = scene.ik_fk_panel_props
        generate_rig(armature, panel_props.generate_ik, panel_props.generate_fk, panel_props.add_ik_fk_snap)
        return {'FINISHED'}


# Register functions
classes = [IK_FK_Properties, OBJECT_OT_Switch_IK_FK, OBJECT_PT_control_rig_panel]

def register():
    bpy.utils.register_class(IK_FK_Properties)
    bpy.utils.register_class(OBJECT_OT_Switch_IK_FK)
    bpy.utils.register_class(OBJECT_PT_control_rig_panel)
    bpy.utils.register_class(OBJECT_OT_generate_rig)

    
    bpy.types.Scene.ik_fk_panel_props = bpy.props.PointerProperty(type=IK_FK_Properties)

def unregister():
    bpy.utils.unregister_class(IK_FK_Properties)
    bpy.utils.unregister_class(OBJECT_OT_Switch_IK_FK)
    bpy.utils.unregister_class(OBJECT_PT_control_rig_panel)
    bpy.utils.unregister_class(OBJECT_OT_generate_rig)
    
    del bpy.types.Scene.ik_fk_panel_props

if __name__ == "__main__":
    register()
