# SkeleSwap Usage Guide

This guide is based on how the addon currently behaves in code. It is written as a practical workflow doc, not marketing copy.

## Table of Contents

- [Before You Start](#before-you-start)
- [Use with Built-in Template](#use-with-built-in-template)
- [Use with Custom Template](#use-with-custom-template)
- [Facial ShapeKey Creation](#facial-shapekey-creation)
- [Generating a Control Rig](#generating-a-control-rig)
- [Create a Custom Template](#create-a-custom-template)
- [Create Custom Bone Mapping](#create-custom-bone-mapping)
- [Create Custom Transform Map](#create-custom-transform-map)
- [Where Saved Data Lives](#where-saved-data-lives)
- [Troubleshooting](#troubleshooting)

## Before You Start

- `Source Armature` = the armature currently driving your character mesh.
- `Target Armature` = the armature you want to end up with (for built-ins, this is usually Epic).
- The addon expects meshes to be direct children of the armature objects.
- If the source or target armature has no child meshes, swap steps will fail.
- The main workflow is designed around similar rest poses (not wildly different rigs).
- Always keep a backup scene or file before running `Replace Skeleton`.

Open the UI in:

`3D View -> N Panel -> SkeleSwap`

## Use with Built-in Template

Built-in templates currently include:

- `MB to Epic Skeleton`
- `Mixamo to Epic Skeleton`

### Standard flow (recommended order)

1. Select your template from the `Template` dropdown.
2. Click `Setup Scene` (sets UE-friendly units and viewport clipping).
3. Set `Source Armature` and `Target Armature`.
4. If source scale is off, set `Scale Amount` and click `Adjust Scale`.
5. Click `Rename VertexGroups`.
6. If you need a quick Epic target in scene, click `Import T Pose Quinn`.
7. If template is `MB to Epic Skeleton`, run `Move Pelvis`.
8. Click `Match Bone Positions`.
9. If template is `MB to Epic Skeleton`, run `Re-parent Breast Bones`.
10. Choose weight transfer options:
   - `Transfer Unmapped Bone Weights`
   - `Transfer Spine Weights` (Epic target templates)
11. Click `Replace Skeleton`.
12. If using Epic target, click `Fix Hand IK constraints`.
13. Optional: click `Export FBX`.

### What those critical steps are doing

- `Rename VertexGroups`: renames source mesh vertex groups to target-bone names based on the selected template's bone map.
- `Match Bone Positions`: runs the template transform map in order and reshapes the target armature to source proportions.
- `Replace Skeleton`: applies armature modifiers, applies target pose as rest pose, reparents meshes to target, transfers selected weights, removes old rig and helper meshes.

## Use with Custom Template

Once you have custom data saved, the runtime usage is the same as built-ins:

1. Pick your custom template in `Template`.
2. Set source/target armatures.
3. Run the same main buttons (`Rename VertexGroups` -> `Match Bone Positions` -> `Replace Skeleton`).

The custom template must point to:

- a saved bone mapping entry
- a saved transform map entry

If either one is missing/invalid, the main operators will cancel with warnings.

## Facial ShapeKey Creation

This section appears when the template has `has_facial_animations = true`.

### MB to Epic template

For MB template, the addon uses bundled data by default:

- Blend file: `ARKIT_Blendshape_Animations_For_MB_Lab_FaceRig.blend`
- Action: `52_Shapekeys`

Expected flow:

1. `Link facial animation`
2. `Create Shapekeys from Animation`
3. Optional cleanup: `Remove Face Rig`

### Non-MB custom template (facial enabled)

If template is not MB-specific:

1. Set blend file path (`Browse .blend file`).
2. Set action name.
3. `Link facial animation`.
4. `Create Shapekeys from Animation`.

### Technical notes

- The addon links an action from a `.blend` library, assigns it to the face rig armature, then makes it local.
- Shapekey creation duplicates source meshes, bakes one frame per ARKit name, copies keys back to original meshes, then deletes duplicates. Bone-parented rigid meshes are baked from their animated object transforms.
- If no separate face rig is found, select the face rig armature in viewport and run link/remove again.

## Generating a Control Rig

The `Control Rig` panel is under the main SkeleSwap panel.

### Quick flow

1. Set `Target Armature`.
2. Choose:
   - `Generate IK`
   - `Generate FK`
   - `Independent Spine IK` (only when IK is enabled)
3. Click `Generate Rig`.
4. If both IK and FK were generated, switch mode with:
   - `IK Mode`
   - `FK Mode`

### What gets generated

- Driver-bone layers (`DRV_IK_*`, `DRV_FK_*`)
- Control bones and pole controls (`CTRL_*`, `PT_*`)
- Constraints and constraint drivers
- IK/FK switch property on armature: `IK_controls`
- Collection setup and visibility rules for control/driver/deform sets

Important: generation expects a clean target armature (no previously generated control-rig marker bones).

## Create a Custom Template

Open:

`3D View -> N Panel -> Create SkeleSwap Template`

Steps:

1. Set `Template Name`.
2. Select existing saved `Bone Mapping`.
3. Select existing saved `Transform Map`.
4. Set flags:
   - `Target is Epic Skeleton`
   - `Has Facial Animations`
   - `Has Separate Face Rig` (if applicable)
5. Click `Save Template`.

Template saves only references to mapping/transform-map names plus flags.

## Create Custom Bone Mapping

Open:

`3D View -> N Panel -> Create Bone Mapping`

Steps:

1. Set `Bone Map Name`.
2. Set `Source Armature` and `Target Armature`.
3. Click `Prefill Target Armature Bones`.
4. Click `Auto Map Bone Names`.
5. Manually fix any wrong/missing pairs.
6. Click `Save Bove Map` for internal reuse.
7. Optional: `Export JSON` to share/version.

How auto-map works:

- strips common prefixes
- parses side indicators (`L/R`, `Left/Right`, etc.)
- parses bone numbers
- checks direct name matches, synonym matches, then similarity fallback

## Create Custom Transform Map

Open:

`3D View -> N Panel -> Bone Transform Mapping`

Steps:

1. Select a saved `Bone Mapping`.
2. Set `Transform Map Name`.
3. Set source and target armatures.
4. Optionally click `Assign Color to armatures` for readability.
5. Select source/target bones from fields or viewport selectors.
6. Pick `Transform Type`, set required inputs, click `Add Transform`.
7. Repeat until chain is complete.
8. Save with `Save Bove Transforms`.
9. Optional: `Export JSON`.

### Transform map tips

- Transform order matters. The map is executed top-to-bottom.
- `Remove Transform` reverts that transform using cached reverse data and removes it from the list.
- For foot alignment-heavy setups, use `Save Current Foot Z location` before adding foot transforms.
- Use `Apply Transforms on Load` if you want imported transforms applied immediately when loading from JSON.

## Where Saved Data Lives

Persistent addon data is stored in Blender's user scripts area:

`.../addon_data/SkeleSwap/`

Managed JSON stores:

- `bone_mappings.json`
- `bone_transforms.json`
- `template_configs.json`

So `Save` operations are persistent across Blender sessions.

## Troubleshooting

- `No Source Mesh` / `No Target Mesh`: make sure meshes are parented to the selected armatures.
- Bone selection operators failing: be in `POSE` mode, with an armature active.
- Facial link fails: confirm `.blend` path and exact action name.
- `Replace Skeleton` gives unexpected deforms: verify bone map first, then rebuild transform map order.
- Control rig generation blocked: use a clean target armature without old `DRV_*` / `CTRL_*` rig artifacts.
