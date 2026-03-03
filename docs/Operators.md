# SkeleSwap Operators Reference

This file documents the currently registered operators and the fields that drive them.

## 1) SkeleSwap Panel (`SkeleSwap` tab)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Enable Debug Print | `scene.enable_debug_print` | Enables `debug_print(...)` logs in many internal utility calls. |
| Template | `scene.selected_template_config` | Picks a saved template and loads its mapping/transform-map references + flags into scene state. |
| Source Armature | `scene.source_armature` | Armature that currently drives your character mesh. |
| Target Armature | `scene.target_armature` | Armature you want to keep after swap. |
| Scale Amount | `scene.skeleswap_props.scale_amount` | Uniform scale factor for source armature + child meshes when running `Adjust Scale`. |
| Transfer Unmapped Bone Weights | `scene.skeleswap_props.transfer_unmapped_weights` | If enabled, copies weights for target bones that are not present in current bone map. |
| Transfer Spine Weights | `scene.skeleswap_props.transfer_spine_weights` | Epic-target only toggle for forcing weight transfer on `spine_01..spine_05`. |

### Operators

| UI Button / Trigger | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Template dropdown change | `object.select_template_config` | Load selected template. | Reads selected template from persistent store, resolves `bone_mapping` and `transform_map` names to actual JSON data, stores resolved config in `scene.template`, sets template flags (Epic target, facial flags, MB template mode). |
| Setup Scene | `object.setup_scene_for_epic_skeleton` | UE5-friendly scene defaults. | Sets unit system to Metric + `scale_length=0.01`, sets viewport grid scale/subdivisions, updates 3D view clip range. |
| Adjust Scale | `object.adjust_scale` | Scale source armature and source meshes together. | Creates temporary empty, parents source armature + mesh children to it, scales empty by `Scale Amount`, clears parent keeping transforms, applies scale, reparents meshes back to armature, deletes temporary empty. |
| Rename VertexGroups | `object.rename_vertex_groups` | Align mesh vertex group names to target bone names. | Uses template bone map and renames mesh vertex groups from source-bone names to target-bone names for meshes bound to source armature. |
| Import T Pose Quinn | `object.import_t_quinn` | Bring in bundled Epic T-pose reference rig. | Imports bundled `Quinn_T_Pose.fbx` with preset FBX axis options. |
| Move Pelvis | `object.move_pelvis` | MB workflow helper. | Runs edit-bone position match: target `pelvis` is moved to source `pelvis` head position. |
| Match Bone Positions | `object.match_bone_positions` | Apply template transform map. | Gets target `foot_l` Z, loads selected template's transform list, executes each transform in order via `apply_transform_map(...)`. |
| Re-parent Breast Bones | `object.reparent_breast_bones` | MB workflow helper for breast bones. | Copies `breast_L/R` from source into target (parented to `spine_05`), renames to `breast_l/r`, then head-matches them to mapped source bones. |
| Replace Skeleton | `object.replace_skeleton` | Core swap step. | Applies armature modifiers, applies target pose as rest pose, reparents meshes to target armature, transfers selected vertex weights, deletes old source armature and temporary target meshes; facial path also duplicates meshes to preserve and restore shapekeys. |
| Fix Hand IK constraints | `object.fix_hand_ik_bones` | Epic rig post-fix for IK helpers. | Adds copy location/rotation constraints (`ik_hand_l/r/gun` to hand bones), then bakes frame 1 with constraints cleared. |
| Export FBX | `object.export_character_as_fbx` | Export target armature + child meshes. | Selects target armature and its mesh children, exports selected FBX with deform bones only, leaf bones off, no animation bake. |
| (not shown in panel; legacy/internal) | `object.enable_debug_print` | Toggle debug flag via operator. | Flips `scene.enable_debug_print`; panel currently uses direct property checkbox instead. |

## 2) Facial Animation Setup Panel (child of SkeleSwap)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Path to ARKIT Blend | `scene.skeleswap_props.shapekey_animation_blend_path` | External `.blend` path used for linked facial action (non-MB templates). |
| Action Name | `scene.skeleswap_props.shapekey_action_name` | Action name to link from blend library (non-MB templates). |

### Operators

| UI Button | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Browse .blend file | `object.open_blend_file_browser` | Set blend source path. | Opens file browser, validates `.blend` extension, stores path on scene property. |
| Link facial animation | `object.link_blendshapes_animation` | Load face action onto face rig armature. | Resolves face rig armature (by name contains `face_rig`, selected armature fallback, or source armature for non-separate setups), links action from library, assigns action to rig, makes linked action local. MB template uses bundled blend/action defaults. |
| Create Shapekeys from Animation | `object.create_ar_kit_shape_keys` | Convert frame-by-frame facial action into shape keys. | Reads ARKit key names from `blendshapes.json`, duplicates source meshes, applies armature, converts animation frames to shape keys, copies generated keys back to originals, deletes duplicates. |
| Remove Face Rig | `object.remove_face_rig` | Cleanup helper after shapekey conversion. | Finds face rig armature(s) by naming (`face_rig` / `phoneme_rig`) or selected fallback; MB template path removes rig collection, otherwise deletes armature object. |

## 3) Control Rig Panel (child of SkeleSwap)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Generate IK | `scene.ik_fk_panel_props.generate_ik` | Include IK control rig generation. |
| Generate FK | `scene.ik_fk_panel_props.generate_fk` | Include FK control rig generation. |
| Independent Spine IK | `scene.ik_fk_panel_props.add_spine_ctrls` | IK setup choice: one independent spine control vs direct driver-spine controls. |

### Operators

| UI Button | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Generate Rig | `object.generate_rig` | Build IK/FK control rig on target armature. | Validates target armature and blocks if generated markers already exist. Creates custom control shapes, driver bone sets (`DRV_IK`, `DRV_FK`), constraints/drivers, IK/FK switch property (`IK_controls`) when both modes are generated, assigns bone collections, hides driver/deform collections, marks armature with `skeleswap_control_rig=True`. |
| IK Mode / FK Mode | `object.switch_ik_fk` | Runtime IK/FK mode switch. | Requires generated rig marker. Sets armature custom property `IK_controls` to `1.0` (IK) or `0.0` (FK), updates depsgraph and pose view so driver-driven influences update immediately. |

## 4) Create Bone Mapping Panel (`Create Bone Mapping` tab)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Bone Map Name | `scene.input_text` | Name used by `Save Bove Map` and default export filename. |
| Source Armature | `scene.source_armature` | Source bones for mapping. |
| Target Armature | `scene.target_armature` | Target bones (keys of final mapping). |
| Bone pair rows | `scene.bone_pair_list[]` | Manual/auto mapping rows (`target_bone_name -> source_bone_name`). |

### Operators

| UI Button / Trigger | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Add Bone Pair | `object.add_bone_pair` | Add empty row to mapping list. | Appends a new `BonePairItem` with empty target/source names. |
| Row remove `X` | `object.remove_bone_pair_from_list` | Remove selected pair row. | Deletes list item by index. |
| Row target eyedropper | `object.set_target_bone` | Fill target bone from viewport selection. | Uses `context.active_pose_bone`; only accepts if selected bone belongs to current target armature. |
| Row source eyedropper | `object.set_source_bone` | Fill source bone from viewport selection. | Uses `context.active_pose_bone`; only accepts if selected bone belongs to current source armature. |
| Prefill Target Armature Bones | `object.prefill_target_bones` | Seed mapping list from target rig. | Clears list and creates one row per target pose bone, leaving source side empty. |
| Auto Map Bone Names | `object.auto_map_bones` | Generate source matches automatically. | Calls `map_bone_lists(...)`: common-prefix cleanup, side + index parsing, synonym matching, similarity fallback; rewrites list with matched pairs (or empty source on misses). |
| Export JSON | `object.export_bone_mapping` | Save mapping to external JSON file. | Writes plain dict `{target_bone: source_bone}` to selected path. |
| Save Bove Map | `object.save_bone_mapping` | Save mapping to addon persistent store. | Upserts mapping under `scene.input_text` key in `bone_mappings` store. |
| Load Bone Mapping | `object.load_bone_mapping` | Load external mapping file into list. | Reads JSON file, rebuilds list rows from loaded key/value pairs. |

## 5) Bone Transform Mapping Panel (`Bone Transform Mapping` tab)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Bone Mapping | `scene.selected_bone_mapping` | Current mapping used for selection-assist and transform setup context. |
| Transform Map Name | `scene.create_transform_props.transform_map_name_input` | Name/key for saving transform map in persistent store and default export filename prefix. |
| Source Armature | `scene.source_armature` | One side of transform operations. |
| Target Armature | `scene.target_armature` | Other side of transform operations. |
| Transform Target is Epic Skeleton | `scene.create_transform_props.transform_target_is_epic_skeleton` | Used by orientation logic (right-side Unreal flip handling). |
| Source Bone | `scene.selected_source_bone` | Selected source bone for single-bone transform types. |
| Target Bone | `scene.selected_target_bone` | Selected target bone for single-bone transform types. |
| Source Bone Chain | `scene.source_bone_chain[]` | Used by `match_edit_bone_chain_scale`. |
| Target Bone Chain | `scene.target_bone_chain[]` | Used by `match_edit_bone_chain_scale`. |
| Name for the copied bone | `scene.create_transform_props.new_bone_name` | New name used by `copy_bone_between_armatures`. |
| Axis | `scene.axis` | Transform axis for rotate/scale transform types (`X`, `Y`, `Z`, `NONE`). |
| Transform Value | `scene.value` | Numeric rotation degrees or scale factor (depends on transform type). |
| Mirror | `scene.mirror` | Enables mirrored rotation for `rotate_bone`. |
| Transform Type | `scene.transform_type` | Chooses transform function used by `Add Transform`. |
| Apply Transforms on Load | `scene.create_transform_props.apply_on_load` | When loading transform JSON, also apply each transform immediately. |

### Transform Type options

| Transform Type value | UI Label | Technical behavior |
|---|---|---|
| `match_pose_bone_head_pos` | Match POSE Bone Head Position | Moves target pose bone head to source bone head position (optionally preserves stored foot Z behavior). |
| `match_pose_bone_orientation` | Match POSE Bone Orientation | Rotates target bone orientation to source direction, with Unreal right-side flip option. |
| `chain_pose_bone_position` | Chain POSE Bone | Moves one bone head to another bone tail (same armature). |
| `scale_bone` | Scale POSE Bone | Pose-mode scale operation on chosen axis or all axes. |
| `rotate_bone` | Rotate POSE Bone | Pose-mode local-axis rotation (degrees), optional mirrored opposite-side rotation. |
| `match_edit_bone_pos` | Match EDIT Bone Head Position | Edit-mode offset move so target head aligns to source head. |
| `match_edit_bone_z_location` | Match EDIT Bone Z Position | Edit-mode Z-only offset match to source head Z. |
| `match_edit_bone_chain_scale` | Match EDIT Bone Chain Scale | Computes chain length ratio source/target and scales selected target chain. |
| `copy_bone_between_armatures` | Copy Bone Between Armatures | Copies source edit bone to target armature, renames it, and aligns its pose head. |

### Operators

| UI Button / Trigger | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Bone Mapping dropdown change | `object.select_bone_mapping` | Load selected mapping into panel context. | Pulls selected mapping from persistent store and serializes it into `scene.bone_mapping_contents` for fast local access. |
| Assign Color to armatures | `object.assign_color_to_armatures` | Visual differentiation helper. | Applies custom pose bone colors on both selected armatures (source: cyan-like, target: brown-like defaults). |
| Select Source Bone | `object.select_source_bone_from_viewport` | Capture source bone from current viewport selection. | Requires active armature in pose mode; stores selected bone name, updates source indicator (`S`/`T`), can auto-fill paired target bone via loaded mapping; for copy-bone transform type also seeds `new_bone_name`. |
| Select Target Bone | `object.select_target_bone_from_viewport` | Capture target bone from current viewport selection. | Requires active armature in pose mode; stores selected target bone name, updates target indicator, can auto-fill paired source bone via mapping. |
| Select Source Bone Chain | `object.select_source_bone_chain` | Capture selected source chain. | Reads all selected pose bones and stores names in source chain collection; sets source indicator (`S`/`T`). |
| Select Target Bone Chain | `object.select_target_bone_chain` | Capture selected target chain. | Reads all selected pose bones and stores names in target chain collection; sets target indicator (`S`/`T`). |
| Save Current Foot Z location | `object.save_foot_z_location` | Cache target foot Z for later transforms. | Stores selected target bone head Z in `create_transform_props` serialized data. |
| Add Transform | `object.add_transform` | Add a transform step (and usually apply it). | Reads current field state, calls transform dispatcher `add_transform(...)`, applies selected transform immediately (unless loading with apply disabled), stores both `transform_details` and reverse `revert_data` in list item. |
| Transform row `X` | `object.remove_transform` | Remove transform step and revert scene change. | Uses stored `revert_data` and transform type-specific inverse call, then removes row from transform list. |
| Export JSON | `object.export_bone_transform` | Save transform map to external JSON file. | Exports as `{"transforms": [ ... ]}` including armature indicators and transform params. |
| Save Bove Transforms | `object.save_bone_transform` | Save transform map for template reuse. | Writes transform list (array only) under map name into persistent `bone_transforms` store. |
| Load Bone Transforms | `object.load_bone_transform` | Import transform JSON into list. | Reads `transforms` array from file, clears current list, recreates each item by calling `add_transform(...)`; can apply while loading based on `Apply Transforms on Load`. |

## 6) Create SkeleSwap Template Panel (`Create SkeleSwap Template` tab)

### Fields

| UI Field | Backing Property | What it controls |
|---|---|---|
| Template Name | `scene.create_template_properties.template_name` | Name/key under which template is saved. |
| Bone Mapping | `scene.create_template_properties.selected_bone_mapping` | Bone mapping reference name saved into template. |
| Transform Map | `scene.create_template_properties.selected_transform_map` | Transform map reference name saved into template. |
| Target is Epic Skeleton | `scene.create_template_properties.target_is_epic_skeleton` | Runtime UI flag to show Epic-specific controls in main panel. |
| Has Facial Animations | `scene.create_template_properties.has_facial_animations` | Runtime UI flag for facial panel visibility. |
| Has Separate Face Rig | `scene.create_template_properties.has_separate_face_rig` | Runtime behavior for face rig discovery/removal path. |

### Operators

| UI Button / Trigger | Operator ID | Purpose | How it works (technical) |
|---|---|---|---|
| Bone Mapping dropdown change | `object.select_t_bone_mapping` | Template panel callback/logging. | Reads current selected value and reports it; actual value is already stored by enum property. |
| Transform Map dropdown change | `object.select_t_transform_map` | Template panel callback/logging. | Reads current selected value and reports it; actual value is already stored by enum property. |
| Save Template | `object.save_template` | Save template config object. | Builds config dict (`option_name`, map refs, flags), validates type, writes to persistent `template_configs` store under template name. |

## 7) Hidden Internal State (not direct UI controls)

These are important for debugging because operators rely on them:

- `scene.template`: resolved template JSON blob used by main workflow operators.
- `scene.target_is_epic_skeleton`: drives Epic-specific conditional buttons.
- `scene.bone_mapping_contents`: active mapping snapshot used by transform-map selection helpers.
- `scene.source_armature_indicator` / `scene.target_armature_indicator`: saved as `S` or `T` per transform so each transform can target either global armature when replayed.

## 8) Not Registered / Disabled

- `object.create_lods` exists in code as commented prototype and is not registered. It is not part of live addon behavior.
