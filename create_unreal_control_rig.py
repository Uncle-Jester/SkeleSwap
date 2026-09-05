import bpy  # type: ignore

from .utils.create_control_rig_utils.control_rig_utils import (
    add_IK_constraint,
    add_copy_location_constraint,
    add_copy_rotation_constraint,
    add_copy_rotation_constraint_with_driver,
    add_custom_shape_for_bone,
    add_damped_track_constraint,
    add_ik_fk_switch_property,
    add_track_to_constraint,
    add_copy_transforms_constraints_to_deform_bones_for_drivers,
    assign_bones_to_new_collection,
    clear_parent,
    connect_bone_tail_to_head,
    create_bone_at_intersection,
    create_custom_shape_mesh,
    create_deform_bones_collection,
    create_driver_bones,
    duplicate_bone,
    extrude_bone,
    move_constraint_to_top,
    move_edit_bone_by_vector,
    parent_bone_keep_offset,
    remove_constraint_by_name,
    remove_constraint_by_type,
    scale_edit_bone,
    set_bone_collection_visibility,
)
from .utils.dev_utils import validate

IK_FK_SWITCH_PROPERTY = "IK_controls"
IK_FK_RIG_MARKER_PROPERTY = "skeleswap_control_rig"
IK_DRIVER_PREFIX = "DRV_IK_"


def _ensure_pose_mode(armature):
    bpy.context.view_layer.objects.active = armature
    if bpy.context.mode != "POSE":
        bpy.ops.object.mode_set(mode="POSE")


def _refresh_pose_view(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.context.view_layer.update()
    try:
        bpy.context.evaluated_depsgraph_get().update()
    except Exception:
        pass
    try:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="POSE")
    except Exception:
        _ensure_pose_mode(armature)

    window_manager = bpy.context.window_manager
    if not window_manager:
        return

    for window in window_manager.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            area.tag_redraw()


def _add_constraint_influence_driver(armature, constraint, invert=False):
    try:
        constraint.driver_remove("influence")
    except Exception:
        pass

    driver = constraint.driver_add("influence").driver
    driver.type = "SCRIPTED"
    variable = driver.variables.new()
    variable.name = "ik_fk_switch"
    variable.targets[0].id = armature
    variable.targets[0].data_path = f'["{IK_FK_SWITCH_PROPERTY}"]'
    driver.expression = "1 - ik_fk_switch" if invert else "ik_fk_switch"


def add_mode_drivers_to_ik_runtime_constraints(armature):
    _ensure_pose_mode(armature)
    for pose_bone in armature.pose.bones:
        if not pose_bone.name.startswith(IK_DRIVER_PREFIX):
            continue
        for constraint in pose_bone.constraints:
            if constraint.type in {"IK", "COPY_LOCATION", "COPY_ROTATION"}:
                _add_constraint_influence_driver(armature, constraint, invert=False)


def has_existing_generated_control_rig(armature):
    marker_bones = {
        "DRV_IK_pelvis",
        "DRV_FK_pelvis",
        "CTRL_base",
        "CTRL_hand_l",
        "foot_l_CTRL",
    }
    return any(bone_name in armature.data.bones for bone_name in marker_bones)


def is_generated_control_rig(armature):
    if not armature:
        return False
    return bool(armature.get(IK_FK_RIG_MARKER_PROPERTY, False))


def get_ik_fk_mode_from_armature(armature, default=True):
    if not armature:
        return default
    value = armature.get(IK_FK_SWITCH_PROPERTY)
    if value is None:
        return default
    return float(value) >= 0.5


def _ordered_unique(items):
    ordered = []
    seen = set()
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _add_shape(
    armature,
    mode,
    bone_name,
    shape,
    theme,
    wireframe=True,
    scale=(1, 1, 1),
    translation=(0, 0, 0),
    rotation=(0, 0, 0),
):
    add_custom_shape_for_bone(
        armature,
        bone_name,
        shape,
        theme,
        wireframe=wireframe,
        scale=list(scale),
        translation=list(translation),
        rotation=list(rotation),
        mode=mode,
    )


def _apply_shape_specs(armature, mode, shape_specs):
    for spec in shape_specs:
        _add_shape(armature, mode, **spec)


def _build_fk_shape_specs():
    specs = []

    for side in ("r", "l"):
        for finger in ("thumb_02", "index_01", "middle_01", "ring_01", "pinky_01"):
            specs.append({"bone_name": f"DRV_FK_{finger}_{side}", "shape": "sphere", "theme": "07"})

    for side in ("r", "l"):
        for finger in ("thumb_03", "index_02", "middle_02", "ring_02", "pinky_02"):
            specs.append(
                {
                    "bone_name": f"DRV_FK_{finger}_{side}",
                    "shape": "sphere",
                    "theme": "03",
                    "scale": (0.7, 0.7, 0.7),
                }
            )

    for side in ("r", "l"):
        for finger in ("index_03", "middle_03", "ring_03", "pinky_03"):
            specs.append(
                {
                    "bone_name": f"DRV_FK_{finger}_{side}",
                    "shape": "sphere",
                    "theme": "12",
                    "scale": (0.5, 0.5, 0.5),
                }
            )

    for side in ("r", "l"):
        for finger in ("index_metacarpal", "middle_metacarpal", "ring_metacarpal", "pinky_metacarpal"):
            specs.append(
                {
                    "bone_name": f"DRV_FK_{finger}_{side}",
                    "shape": "sphere",
                    "theme": "03",
                    "scale": (0.5, 0.5, 0.5),
                }
            )

    specs.extend(
        [
            {"bone_name": "DRV_FK_clavicle_l", "shape": "sphere", "theme": "03", "scale": (1, 1, 1)},
            {"bone_name": "DRV_FK_upperarm_l", "shape": "sphere", "theme": "12", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_lowerarm_l", "shape": "sphere", "theme": "03", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_hand_l", "shape": "sphere", "theme": "12", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_clavicle_r", "shape": "sphere", "theme": "03", "scale": (1, 1, 1)},
            {"bone_name": "DRV_FK_upperarm_r", "shape": "sphere", "theme": "12", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_lowerarm_r", "shape": "sphere", "theme": "03", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_hand_r", "shape": "sphere", "theme": "12", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_thigh_l", "shape": "sphere", "theme": "03", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_calf_l", "shape": "sphere", "theme": "03", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_foot_l", "shape": "sphere", "theme": "07", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_ball_l", "shape": "sphere", "theme": "07", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_thigh_r", "shape": "sphere", "theme": "03", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_calf_r", "shape": "sphere", "theme": "03", "scale": (5, 5, 5)},
            {"bone_name": "DRV_FK_foot_r", "shape": "sphere", "theme": "07", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_ball_r", "shape": "sphere", "theme": "07", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_pelvis", "shape": "sphere", "theme": "04", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_spine_01", "shape": "sphere", "theme": "03", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_spine_02", "shape": "sphere", "theme": "03", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_spine_03", "shape": "sphere", "theme": "03", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_spine_04", "shape": "sphere", "theme": "03", "scale": (2, 2, 2)},
            {"bone_name": "DRV_FK_spine_05", "shape": "sphere", "theme": "03", "scale": (3, 3, 3)},
            {"bone_name": "DRV_FK_neck_01", "shape": "sphere", "theme": "12", "scale": (1, 1, 1)},
            {"bone_name": "DRV_FK_neck_02", "shape": "sphere", "theme": "12", "scale": (1, 1, 1)},
            {"bone_name": "DRV_FK_head", "shape": "sphere", "theme": "07", "scale": (5, 5, 5)},
        ]
    )
    return specs


def generate_fk_rig(armature, shape_mode=None):
    fk_mode_driver = {"property_name": IK_FK_SWITCH_PROPERTY, "invert": True} if shape_mode is not None else None
    add_copy_transforms_constraints_to_deform_bones_for_drivers(
        armature,
        "FK_DRIVER_BONES",
        "DRV_FK",
        True,
        add_driver_to_copy_transform_influence=shape_mode is not None,
    )

    for side in ("l", "r"):
        ball_name = f"ball_{side}"
        driver_ball_name = f"DRV_FK_ball_{side}"
        remove_constraint_by_name(armature, ball_name, f"FK_Copy Transforms -> {driver_ball_name}")
        add_copy_rotation_constraint_with_driver(
            armature,
            ball_name,
            driver_ball_name,
            f"Copy FK Rotation -> {driver_ball_name}",
            driver=fk_mode_driver,
        )
        move_constraint_to_top(armature, ball_name, f"Copy FK Rotation -> {driver_ball_name}")

    fk_shape_specs = _build_fk_shape_specs()
    _apply_shape_specs(armature, shape_mode, fk_shape_specs)
    fk_control_bones = _ordered_unique([spec["bone_name"] for spec in fk_shape_specs])
    assign_bones_to_new_collection(armature, fk_control_bones, "CONTROL_RIG", False)


def _setup_ik_arm_side(armature, side, pole_angle):
    hand_driver = f"DRV_IK_hand_{side}"
    lowerarm_driver = f"DRV_IK_lowerarm_{side}"
    hand_ctrl = f"CTRL_hand_{side}"
    elbow_pole = f"PT_elbow_{side}"

    extrude_bone(armature, hand_driver, hand_ctrl, (0, 20, 0))
    parent_bone_keep_offset(armature, hand_driver, hand_ctrl)
    extrude_bone(armature, lowerarm_driver, elbow_pole, (0, 20, 0))
    move_edit_bone_by_vector(armature, elbow_pole, (0, 30, 0))
    add_IK_constraint(armature, lowerarm_driver, hand_ctrl, elbow_pole, 2, pole_angle)
    add_copy_location_constraint(armature, hand_driver, lowerarm_driver, 1)


def _setup_clavicle_side(armature, side):
    clavicle_driver = f"DRV_IK_clavicle_{side}"
    hand_ctrl = f"CTRL_hand_{side}"
    target_name = f"MCH_clavicle_target_{side}"
    clavicle_mch = f"MCH_clavicle_{side}"

    create_bone_at_intersection(armature, clavicle_driver, hand_ctrl, (0, 20, 0), target_name)
    add_damped_track_constraint(armature, clavicle_driver, target_name)
    add_copy_location_constraint(armature, target_name, hand_ctrl, 0, "LOCAL", "LOCAL", 0.3)

    duplicate_bone(armature, clavicle_driver, clavicle_mch)
    scale_edit_bone(armature, clavicle_mch, (1.1, 1.1, 1.1))
    parent_bone_keep_offset(armature, clavicle_driver, clavicle_mch)
    remove_constraint_by_type(armature, clavicle_driver, "DAMPED_TRACK")


def _setup_ik_leg_side(armature, side, pole_angle, ik_mode_driver):
    calf_driver = f"DRV_IK_calf_{side}"
    foot_driver = f"DRV_IK_foot_{side}"
    knee_pole = f"PT_knee_{side}"
    foot_ctrl = f"foot_{side}_CTRL"
    ball_name = f"ball_{side}"
    ball_driver = f"DRV_IK_ball_{side}"
    ball_pivot_ctrl = f"CTRL_PV_ball_{side}"

    connect_bone_tail_to_head(armature, calf_driver, foot_driver)
    extrude_bone(armature, calf_driver, knee_pole, (0, -20, 0))
    clear_parent(armature, knee_pole)
    move_edit_bone_by_vector(armature, knee_pole, (0, -40, 0))

    duplicate_bone(armature, foot_driver, foot_ctrl)
    clear_parent(armature, foot_ctrl)
    remove_constraint_by_type(armature, foot_ctrl, "COPY_TRANSFORMS")
    add_IK_constraint(armature, calf_driver, foot_ctrl, knee_pole, 2, pole_angle)
    add_copy_rotation_constraint(armature, foot_driver, foot_ctrl, (1, 1, 1), "WORLD", "WORLD")

    remove_constraint_by_name(armature, ball_name, f"IK_Copy Transforms -> {ball_driver}")
    add_copy_rotation_constraint_with_driver(
        armature,
        ball_name,
        ball_driver,
        f"Copy IK Rotation -> {ball_driver}",
        driver=ik_mode_driver,
    )
    move_constraint_to_top(armature, ball_name, f"Copy IK Rotation -> {ball_driver}")

    extrude_bone(armature, ball_driver, ball_pivot_ctrl, (0, 0, 10))
    parent_bone_keep_offset(armature, ball_pivot_ctrl, ball_driver)
    parent_bone_keep_offset(armature, foot_ctrl, ball_pivot_ctrl)
    clear_parent(armature, ball_driver)


def _add_ik_finger_rotation_follow_constraints(armature):
    follow_pairs = [
        ("thumb_03", "thumb_02"),
        ("index_02", "index_01"),
        ("index_03", "index_02"),
        ("middle_02", "middle_01"),
        ("middle_03", "middle_02"),
        ("ring_02", "ring_01"),
        ("ring_03", "ring_02"),
        ("pinky_02", "pinky_01"),
        ("pinky_03", "pinky_02"),
    ]
    for side in ("l", "r"):
        for target_suffix, source_suffix in follow_pairs:
            add_copy_rotation_constraint(
                armature,
                f"DRV_IK_{target_suffix}_{side}",
                f"DRV_IK_{source_suffix}_{side}",
                (0, 0, 1),
                "LOCAL",
                "LOCAL",
            )


def _build_ik_shape_specs(independent_spine):
    specs = [
        {"bone_name": "CTRL_base", "shape": "circle", "theme": "14", "wireframe": False, "scale": (50, 50, 50)},
        {"bone_name": "CTRL_head", "shape": "sphere", "theme": "01", "wireframe": False, "scale": (5, 5, 5)},
        {"bone_name": "PT_elbow_l", "shape": "sphere", "theme": "05", "scale": (5, 5, 5)},
        {"bone_name": "PT_elbow_r", "shape": "sphere", "theme": "05", "scale": (5, 5, 5)},
        {"bone_name": "PT_knee_l", "shape": "sphere", "theme": "11", "scale": (5, 5, 5)},
        {"bone_name": "PT_knee_r", "shape": "sphere", "theme": "11", "scale": (5, 5, 5)},
        {"bone_name": "CTRL_center_of_gravity", "shape": "cube", "theme": "09", "scale": (20, 30, 40)},
        {"bone_name": "DRV_IK_neck_01", "shape": "sphere", "theme": "04", "scale": (2, 2, 2)},
        {"bone_name": "DRV_IK_neck_02", "shape": "sphere", "theme": "04", "scale": (2, 2, 2)},
        {"bone_name": "CTRL_hip", "shape": "sphere", "theme": "09", "scale": (3, 3, 3)},
    ]

    if independent_spine:
        specs.append({"bone_name": "CTRL_spine", "shape": "sphere", "theme": "06", "scale": (3, 3, 3)})
    else:
        for bone_name in ("DRV_IK_spine_01", "DRV_IK_spine_02", "DRV_IK_spine_03", "DRV_IK_spine_04"):
            specs.append({"bone_name": bone_name, "shape": "sphere", "theme": "03", "scale": (2, 2, 2)})
        specs.append({"bone_name": "DRV_IK_spine_05", "shape": "sphere", "theme": "03", "scale": (3, 3, 3)})

    specs.extend(
        [
            {
                "bone_name": "DRV_IK_ball_r",
                "shape": "circle",
                "theme": "02",
                "scale": (5, 5, 0),
                "translation": (0, 3, 1),
                "rotation": (-2, 93, 0),
            },
            {
                "bone_name": "DRV_IK_ball_l",
                "shape": "circle",
                "theme": "02",
                "scale": (5, 5, 0),
                "translation": (0, 3, 1),
                "rotation": (-2, 93, 0),
            },
            {
                "bone_name": "CTRL_PV_ball_r",
                "shape": "circle",
                "theme": "02",
                "scale": (10, 5, 0),
                "translation": (6, 0, 10),
                "rotation": (90, -60, 0),
            },
            {
                "bone_name": "CTRL_PV_ball_l",
                "shape": "circle",
                "theme": "02",
                "scale": (10, 5, 0),
                "translation": (-12, 0, 0),
                "rotation": (90, 0, 0),
            },
        ]
    )

    for side in ("l", "r"):
        for bone_suffix in ("thumb_02", "index_01", "middle_01", "ring_01", "pinky_01"):
            specs.append({"bone_name": f"DRV_IK_{bone_suffix}_{side}", "shape": "sphere", "theme": "04"})

        if side == "l":
            specs.append(
                {
                    "bone_name": "CTRL_hand_l",
                    "shape": "cube",
                    "theme": "02",
                    "scale": (15, 8, 1),
                    "translation": (10, -3, 5),
                    "rotation": (0, 10, -10),
                }
            )
        else:
            specs.append(
                {
                    "bone_name": "CTRL_hand_r",
                    "shape": "cube",
                    "theme": "02",
                    "scale": (15, 8, 1),
                    "translation": (-10, 3, 5),
                    "rotation": (0, -10, 10),
                }
            )

    specs.extend(
        [
            {
                "bone_name": "DRV_IK_clavicle_l",
                "shape": "curled_plane",
                "theme": "02",
                "scale": (5, 10, 10),
                "translation": (0, 10, 8.5),
                "rotation": (0, 15, 90),
            },
            {
                "bone_name": "DRV_IK_clavicle_r",
                "shape": "curled_plane",
                "theme": "02",
                "scale": (5, 10, 10),
                "translation": (0, 10, 8.5),
                "rotation": (0, 15, 90),
            },
        ]
    )
    return specs


def _assign_ik_collections(armature, independent_spine):
    selected_spine_option = (
        ["CTRL_spine"]
        if independent_spine
        else ["DRV_IK_spine_01", "DRV_IK_spine_02", "DRV_IK_spine_03", "DRV_IK_spine_04", "DRV_IK_spine_05"]
    )

    assign_bones_to_new_collection(
        armature,
        ["MCH_head", "MCH_clavicle_l", "MCH_clavicle_target_l", "MCH_clavicle_r", "MCH_clavicle_target_r"],
        "MCH_BONES",
        True,
    )

    assign_bones_to_new_collection(
        armature,
        [
            "CTRL_base",
            "CTRL_hip",
            "CTRL_head",
            "DRV_IK_neck_01",
            "DRV_IK_neck_02",
            *selected_spine_option,
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
            "PT_knee_l",
            "PT_knee_r",
            "foot_l_CTRL",
            "foot_r_CTRL",
            "CTRL_PV_ball_l",
            "CTRL_PV_ball_r",
            "DRV_IK_ball_r",
            "DRV_IK_ball_l",
            "DRV_IK_clavicle_l",
            "DRV_IK_clavicle_r",
        ],
        "CONTROL_RIG",
        True,
    )

    assign_bones_to_new_collection(
        armature,
        [
            "PT_knee_l",
            "PT_knee_r",
            "PT_elbow_l",
            "PT_elbow_r",
            "CTRL_head",
            "CTRL_PV_ball_l",
            "CTRL_PV_ball_r",
            "CTRL_hip",
            "CTRL_spine",
            "CTRL_center_of_gravity",
            "CTRL_hand_l",
            "CTRL_hand_r",
            "foot_l_CTRL",
            "foot_r_CTRL",
            "CTRL_base",
            "MCH_clavicle_target_l",
            "MCH_clavicle_target_r",
        ],
        "IK_CTRL_BONES",
        False,
    )

    set_bone_collection_visibility(armature, "MCH_BONES", False)


def generate_ik_rig(armature, shape_mode, independent_spine):
    ik_mode_driver = {"property_name": IK_FK_SWITCH_PROPERTY, "invert": False} if shape_mode is not None else None

    add_copy_transforms_constraints_to_deform_bones_for_drivers(
        armature,
        "IK_DRIVER_BONES",
        "DRV_IK",
        True,
        add_driver_to_copy_transform_influence=shape_mode is not None,
    )

    duplicate_bone(armature, "center_of_mass", "CTRL_base")
    clear_parent(armature, "CTRL_base")

    for side in ("l", "r"):
        connect_bone_tail_to_head(armature, f"DRV_IK_lowerarm_{side}", f"DRV_IK_hand_{side}")

    for side, pole_angle in (("l", 135), ("r", 0)):
        _setup_ik_arm_side(armature, side, pole_angle)

    extrude_bone(armature, "DRV_IK_spine_01", "CTRL_hip", (0, 20, 0))
    parent_bone_keep_offset(armature, "DRV_IK_pelvis", "CTRL_hip")

    extrude_bone(armature, "DRV_IK_spine_01", "CTRL_center_of_gravity", (0, 20, 0))
    parent_bone_keep_offset(armature, "CTRL_hip", "CTRL_center_of_gravity")

    if independent_spine:
        extrude_bone(armature, "DRV_IK_spine_04", "CTRL_spine", (0, 20, 0))
        clear_parent(armature, "CTRL_spine")
        parent_bone_keep_offset(armature, "DRV_IK_spine_04", "CTRL_spine")
        add_IK_constraint(armature, "DRV_IK_spine_03", "CTRL_spine", chain_length=1)
        add_copy_location_constraint(armature, "DRV_IK_spine_04", "DRV_IK_spine_03", 1)
        parent_bone_keep_offset(armature, "CTRL_spine", "CTRL_center_of_gravity")

    duplicate_bone(armature, "DRV_IK_head", "CTRL_head")
    move_edit_bone_by_vector(armature, "CTRL_head", (0, -30, 0))
    clear_parent(armature, "CTRL_head")

    duplicate_bone(armature, "DRV_IK_head", "MCH_head")
    scale_edit_bone(armature, "MCH_head", (1.1, 1.1, 1.1))
    parent_bone_keep_offset(armature, "DRV_IK_head", "MCH_head")
    parent_bone_keep_offset(armature, "MCH_head", "DRV_IK_neck_02")
    add_track_to_constraint(armature, "MCH_head", "CTRL_head", "X", "Y")
    add_copy_rotation_constraint(armature, "DRV_IK_head", "CTRL_head", (1, 0, 0), "LOCAL", "LOCAL")

    for side in ("l", "r"):
        _setup_clavicle_side(armature, side)

    for side, pole_angle in (("r", -172), ("l", 0)):
        _setup_ik_leg_side(armature, side, pole_angle, ik_mode_driver)

    _add_ik_finger_rotation_follow_constraints(armature)

    if shape_mode is not None:
        add_mode_drivers_to_ik_runtime_constraints(armature)

    for child_bone in [
        "MCH_clavicle_target_l",
        "MCH_clavicle_target_r",
        "CTRL_center_of_gravity",
        "CTRL_head",
        "CTRL_hand_l",
        "CTRL_hand_r",
        "PT_elbow_r",
        "PT_knee_r",
        "PT_elbow_l",
        "PT_knee_l",
        "DRV_IK_ball_l",
        "DRV_IK_ball_r",
    ]:
        parent_bone_keep_offset(armature, child_bone, "CTRL_base")

    _apply_shape_specs(armature, shape_mode, _build_ik_shape_specs(independent_spine))
    _assign_ik_collections(armature, independent_spine)


def generate_rig(armature, ik=True, fk=False, independent_spine=True):
    validate(
        [armature],
        ["ARMATURE"],
        stack_location="CreateUnrealControlRig-GenerateRig",
        input_identifier_strings=["armature"],
    )
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")

    create_custom_shape_mesh("cube")
    create_custom_shape_mesh("circle")
    create_custom_shape_mesh("sphere")
    create_custom_shape_mesh("plane", curled=True)
    create_deform_bones_collection(armature)

    add_copy_location_constraint(armature, "ik_hand_l", "hand_l")
    add_copy_rotation_constraint(armature, "ik_hand_l", "hand_l")
    add_copy_location_constraint(armature, "ik_hand_r", "hand_r")
    add_copy_rotation_constraint(armature, "ik_hand_r", "hand_r")
    add_copy_location_constraint(armature, "ik_hand_gun", "hand_r")
    add_copy_rotation_constraint(armature, "ik_hand_gun", "hand_r")

    if ik and fk:
        create_driver_bones(armature, "IK_DRIVER_BONES", "DRV_IK")
        create_driver_bones(armature, "FK_DRIVER_BONES", "DRV_FK")
        add_ik_fk_switch_property(armature, IK_FK_SWITCH_PROPERTY)
        armature[IK_FK_SWITCH_PROPERTY] = 1.0
    elif ik:
        create_driver_bones(armature, "IK_DRIVER_BONES", "DRV_IK")
    elif fk:
        create_driver_bones(armature, "FK_DRIVER_BONES", "DRV_FK")

    if fk:
        shape_mode = "FK" if ik else None
        generate_fk_rig(armature, shape_mode)

    if ik:
        shape_mode = "IK" if fk else None
        generate_ik_rig(armature, shape_mode, independent_spine)

    if ik:
        set_bone_collection_visibility(armature, "IK_DRIVER_BONES", False)
    if fk:
        set_bone_collection_visibility(armature, "FK_DRIVER_BONES", False)
    set_bone_collection_visibility(armature, "DEFORM_BONES", False)

    bpy.ops.object.mode_set(mode="POSE")
    armature[IK_FK_RIG_MARKER_PROPERTY] = True
    _refresh_pose_view(armature)


class IK_FK_Properties(bpy.types.PropertyGroup):
    generate_fk: bpy.props.BoolProperty(  # type: ignore
        name="generate_FK",
        description="Generate FK controls",
        default=False,
    )

    generate_ik: bpy.props.BoolProperty(  # type: ignore
        name="generate_IK",
        description="Generate IK controls",
        default=True,
    )

    add_spine_ctrls: bpy.props.BoolProperty(  # type: ignore
        name="add_spine_ctrls",
        description="Adds independent spine controls to the IK control rig",
        default=True,
    )


class UnrealControlRigPanel(bpy.types.Panel):
    bl_label = "Control Rig"
    bl_idname = "OBJECT_PT_control_rig_panel"
    bl_parent_id = "OBJECT_PT_skeleswap_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        panel_props = scene.ik_fk_panel_props
        armature = scene.target_armature
        is_ik_mode = get_ik_fk_mode_from_armature(armature)
        is_generated_rig = is_generated_control_rig(armature)

        row = layout.row()
        row.prop(panel_props, "generate_ik", text="Generate IK")
        row.prop(panel_props, "generate_fk", text="Generate FK")

        if panel_props.generate_ik:
            row = layout.row()
            row.prop(panel_props, "add_spine_ctrls", text="Independent Spine IK")

        row = layout.row()
        row.operator("object.generate_rig", text="Generate Rig")

        if panel_props.generate_ik and panel_props.generate_fk:
            row = layout.row()
            row.label(text="Switch IK/FK Mode:")
            if not is_generated_rig:
                row = layout.row()
                row.label(text="Generate rig first on a clean armature.")
            row = layout.row()
            row.enabled = is_generated_rig
            row.operator("object.switch_ik_fk", text="IK Mode", depress=is_ik_mode).mode = "IK"
            row.operator("object.switch_ik_fk", text="FK Mode", depress=not is_ik_mode).mode = "FK"


class UnrealControlRigSwitchIkFkOperator(bpy.types.Operator):
    bl_idname = "object.switch_ik_fk"
    bl_label = "Switch IK/FK"
    bl_options = {"REGISTER", "UNDO"}

    mode: bpy.props.EnumProperty(  # type: ignore
        items=[("IK", "IK Mode", "Switch to IK Mode"), ("FK", "FK Mode", "Switch to FK Mode")],
        name="IK/FK Mode",
    )

    def execute(self, context):
        armature = context.scene.target_armature
        target_ik_mode = self.mode == "IK"
        try:
            validate(
                [armature],
                ["ARMATURE"],
                stack_location="CreateUnrealControlRig-SwitchIKFK",
                input_identifier_strings=["armature"],
            )
            _ensure_pose_mode(armature)
            if not is_generated_control_rig(armature):
                self.report({"ERROR"}, "Target armature is not marked as a generated control rig.")
                return {"CANCELLED"}

            if IK_FK_SWITCH_PROPERTY not in armature.keys():
                add_ik_fk_switch_property(armature, IK_FK_SWITCH_PROPERTY)

            armature[IK_FK_SWITCH_PROPERTY] = 1.0 if target_ik_mode else 0.0
            armature.update_tag()
            armature.data.update_tag()

            try:
                context.evaluated_depsgraph_get().update()
            except Exception:
                pass
            context.scene.frame_set(context.scene.frame_current)
            _refresh_pose_view(armature)
            self.report({"INFO"}, f"Switched rig to {self.mode} mode.")
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, f"Failed to switch IK/FK mode. Error: {error}")
            return {"CANCELLED"}


class UnrealControlRigGenerateRigOperator(bpy.types.Operator):
    bl_idname = "object.generate_rig"
    bl_label = "Generate control rig"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armature = context.scene.target_armature
        panel_props = context.scene.ik_fk_panel_props
        try:
            validate(
                [armature],
                ["ARMATURE"],
                stack_location="CreateUnrealControlRig-GenerateOperator",
                input_identifier_strings=["armature"],
            )
            if has_existing_generated_control_rig(armature):
                self.report({"ERROR"}, "Detected existing control rig bones. Use a clean armature/scene for this rig.")
                return {"CANCELLED"}

            generate_rig(
                armature,
                panel_props.generate_ik,
                panel_props.generate_fk,
                panel_props.add_spine_ctrls,
            )
            _refresh_pose_view(armature)
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, f"Failed to generate control rig. Error: {error}")
            return {"CANCELLED"}


classes = [
    IK_FK_Properties,
    UnrealControlRigSwitchIkFkOperator,
    UnrealControlRigGenerateRigOperator,
    UnrealControlRigPanel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ik_fk_panel_props = bpy.props.PointerProperty(type=IK_FK_Properties)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.ik_fk_panel_props


if __name__ == "__main__":
    register()
