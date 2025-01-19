import bpy # type: ignore
import os
import json

from .utils import match_pose_bone_head_pos, match_edit_bone_pos, get_foot_z_location, add_copy_location_constraint, add_copy_rotation_constraint, apply_bone_constraints, copy_bone_between_skeletons, rename_bone # bone transform utils imports
from .utils import link_animation, set_frame_to, convert_animation_to_shapekeys # facial animation utils imports
from .utils import get_json_property, debug_print
from .utils import duplicate_mesh, delete_mesh, copy_shapekeys, delete_all_shapekeys, create_basis_shape_key, rename_mesh, add_decimate_modifier, transfer_weights, transfer_weights_for_specific_bones # mesh utils imports
from .utils import delete_armature, parent_armature, scale_selected_armature_with_child_meshes, apply_armature, apply_pose_as_rest_pose
from .utils import delete_collection

from .utils.bone_transform_map_utils import apply_transform_map

addon_dir = os.path.dirname(os.path.realpath(__file__))
utils_dir = os.path.join(addon_dir, "utils")
imports_dir = os.path.join(utils_dir, "blends_and_fbx")
data_dir = os.path.join(utils_dir, "data")

bpy.types.Scene.enable_debug_print = bpy.props.BoolProperty(
    name="Enable Debug Print",
    description="Enable or disable the debug print feature",
    default=False
)

class SkeleSwapProperties(bpy.types.PropertyGroup):
    show_facial_operators: bpy.props.BoolProperty(name="Show Facial Operators", default=False) # type: ignore
    shapekey_animation_blend_path: bpy.props.StringProperty(name="Path to ARKIT Blend", default="") # type: ignore
    shapekey_action_name: bpy.props.StringProperty(name="Shape Key Action Name", default="52_Shapekeys") # type: ignore
    target_is_epic_skeleton: bpy.props.BoolProperty(name="Target is Epic Skeleton", default=False) # type: ignore
    has_facial_animations: bpy.props.BoolProperty(name="Has Facial Animations", default=False) # type: ignore
    has_separate_face_rig: bpy.props.BoolProperty(name="Has Separate Face Rig", default=False) # type: ignore
    is_mb_to_epic: bpy.props.BoolProperty(name="Has Facial Animations", default=True) # type: ignore
    scale_amount: bpy.props.IntProperty(name="Scale Amount",default=100) # type: ignore
    lod_count: bpy.props.IntProperty(
    name="LOD Count",
    description="Number of LODs to create",
    default=3,
    min=1,
    max=5
    ) # type: ignore

class OBJECT_PT_skeleswap_main_panel(bpy.types.Panel):
    bl_label = "Align Skeleton"
    bl_idname = "OBJECT_PT_skeleswap_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'SkeleSwap'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        skeleswap_props = scene.skeleswap_props

        row = layout.row()
        layout.prop(scene, "enable_debug_print", text="Enable Debug Print")

        row = layout.row(align=True)
        row.prop(scene, "selected_template_config")

        row = layout.row()
        layout.operator("object.setup_scene_for_epic_skeleton", text="Setup Scene")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(scene, "source_armature", text="Source Armature")
        sub_row.prop(scene, "target_armature", text="Target Armature")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.operator("object.adjust_scale", text="Adjust Scale")
        layout.separator()
        sub_row.prop(skeleswap_props, "scale_amount", text="Scale Amount")

        row = layout.row()
        row.operator("object.rename_vertex_groups", text="Rename VertexGroups")
        row = layout.row()
        row.operator("object.import_t_quinn", text="Import T Pose Quinn")

        if skeleswap_props.is_mb_to_epic:
            row = layout.row()
            row.operator("object.move_pelvis", text="Move Pelvis")

        row = layout.row()
        row.operator("object.match_bone_positions", text="Match Bone Positions")

        if skeleswap_props.is_mb_to_epic:
            row = layout.row()
            row.operator("object.reparent_breast_bones", text="Re-parent Breast Bones")

        row = layout.row()
        row.operator("object.replace_skeleton", text="Replace Skeleton")

        if scene.target_is_epic_skeleton:
            row = layout.row()
            row.operator("object.fix_hand_ik_bones", text="Fix Hand IK constraints")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(skeleswap_props, "lod_count", text="Number of LODs")
        layout.separator()
        sub_row.operator("object.create_lods", text="Create LODS")
        layout.separator()
        layout.separator()
        if scene.target_is_epic_skeleton:
            row = layout.row()
            row.operator("object.export_character_as_fbx", text="Export FBX")
            



class OBJECT_PT_facial_operators_panel(bpy.types.Panel):
    bl_label = "Facial Animation Setup"
    bl_idname = "OBJECT_PT_facial_operators_panel"
    bl_parent_id = "OBJECT_PT_skeleswap_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        skeleswap_props = scene.skeleswap_props
        if skeleswap_props.has_facial_animations:
            box = layout.box()
            if not skeleswap_props.is_mb_to_epic:
                row = box.row(align=True)
                row.prop(skeleswap_props, "shapekey_animation_blend_path", text="")
                row.operator("object.open_blend_file_browser", text="Browse .blend file", icon='FILEBROWSER')
            
            
            box.operator("object.link_blendshapes_animation", text="Link facial animation")
            box.operator("object.create_ar_kit_shape_keys", text="Create Shapekeys from Animation")
            if skeleswap_props.has_separate_face_rig or skeleswap_props.is_mb_to_epic:
                box.operator("object.remove_face_rig", text="Remove Face Rig")

def rename_vertex_groups(armature, bone_mapping):
    bpy.context.view_layer.objects.active = armature
    for obj in bpy.data.objects:
        debug_print(f"MainPanel-RenameVertexGroups: obj.name: {obj.name} - obj.find_armature: {obj.find_armature()}")
        if obj.type == 'MESH' and obj.find_armature() == armature:
            for target_bone, source_bone in bone_mapping.items():
                if source_bone in obj.vertex_groups:
                    obj.vertex_groups[source_bone].name = target_bone

def get_template_config_options():
    json_file_path = os.path.join(data_dir, "template_configs.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
                return list(data.keys())
            except json.JSONDecodeError:
                print(f"Could not load json file from filepath: {json_file_path}")
                return []
    else:
        print("JSON path is not valid")
    return []

def get_template_config_contents(scene):
    if scene.template:
        template_data = json.loads(scene.template)
        debug_print(f"MainPanel-GetTemplateConfigContents: {template_data}")
        bone_mapping_property_name = template_data.get("bone_mapping")
        bone_transform_property_name = template_data.get("transform_map")
        if bone_mapping_property_name and bone_transform_property_name:
            debug_print(f"MainPanel-GetTemplateConfigContents: bone_mapping: {bone_mapping_property_name}, transform_map: {bone_transform_property_name}")
            template_data["bone_mapping"] = get_json_property(os.path.join(data_dir, "bone_mappings.json"), bone_mapping_property_name)
            template_data["transform_map"] = get_json_property(os.path.join(data_dir, "bone_transforms.json"), bone_transform_property_name)
            return template_data
    else:
        return {}

def set_template_config_contents(scene, config):
    debug_print(f"MainPanel-SetTemplateConfigContents: {config}")
    scene.template = json.dumps(config)
    skelewap_props = scene.skeleswap_props
    scene.target_is_epic_skeleton = config.get("target_is_epic_skeleton", False)
    skelewap_props.has_facial_animations = config.get("has_facial_animations", False)
    skelewap_props.is_mb_to_epic = config.get("option_name") == "MB to Epic Skeleton"

def template_config_update_callback(self, context):
    debug_print("MainPanel-TemplateConfigUpdateCallback: Callback is being called upon selecting a new template")
    bpy.ops.object.select_template_config()

def update_source_armature(self, context):
    armature = bpy.context.scene.source_armature
    debug_print(f"MainPanel-SelectSourceArmature: Updated Source Armature: {armature}")
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.source_armature = None
        debug_print("MainPanel-SelectSourceArmature: Source Armature is not an armature, resetting to None")


def update_target_armature(self, context):
    armature = bpy.context.scene.target_armature
    debug_print(f"MainPanel-SelectTargetArmature: Updated Target Armature: {armature}")
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.target_armature = None
        debug_print("MainPanel-SelectTargetArmature: Target Armature is not an armature, resetting to None")

class OBJECT_OT_select_template_config(bpy.types.Operator):
    bl_idname = "object.select_template_config"
    bl_label = "Select Template"

    selected_template_config: bpy.props.EnumProperty(
        name="Template",
        items=lambda self, context: [(option, option, "") for option in get_template_config_options()],
    ) # type: ignore

    def execute(self, context):
        selected_template_name = context.scene.selected_template_config
        json_file_path = os.path.join(data_dir, "template_configs.json")
        debug_print(f"MainPanel-SelectTemplateConfig-Execute: Template Selected: {selected_template_name}")
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                try:
                    data = json.load(json_file)
                    if data and data.get(selected_template_name):
                        template_contents = data[selected_template_name]
                        debug_print(f"MainPanel-SelectTemplateConfig-Execute: Contents of selected template: {template_contents}")
                        set_template_config_contents(context.scene, template_contents)
                except json.JSONDecodeError:
                    return {}

        self.report({'INFO'}, f"Selected Template: {selected_template_name}")
        return {'FINISHED'}

class OBJECT_OT_setup_scene_for_epic_skeleton(bpy.types.Operator):
    bl_idname = "object.setup_scene_for_epic_skeleton"
    bl_label = "Setup Scene for UE5"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 0.01        
        bpy.context.space_data.overlay.grid_scale = 1.0
        bpy.context.space_data.overlay.grid_subdivisions = 10
        
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_start = 0.1
                        space.clip_end = 10000

        self.report({'INFO'}, "Scene configured for Epic Skeleton")
        return {'FINISHED'}

class OBJECT_OT_adjust_scale(bpy.types.Operator):
    bl_idname = "object.adjust_scale"
    bl_label = "Rescales Source Armature and its child meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        armature = context.scene.source_armature
        skeleswap_props = context.scene.skeleswap_props
        if armature and armature.type == 'ARMATURE':
            scale_selected_armature_with_child_meshes(armature, skeleswap_props.scale_amount)
            self.report({'INFO'}, f"Scaled by {skeleswap_props.scale_amount}")
        else:
            debug_print(f"MainPanel-AdjustScale: Invalid Armature: {armature}")
            self.report({'WARNING'}, "Source Armature is not valid, please select a valid source armature")
            return {"CANCELLED"}
        return {'FINISHED'}


    
class OBJECT_OT_rename_vertex_groups(bpy.types.Operator):
    bl_idname = "object.rename_vertex_groups"
    bl_label = "Rename Vertex Groups"
    bl_description = "Rename vertex groups, to match the epic mannequin"


    def execute(self, context):
        armature = context.scene.source_armature      
        template_config = get_template_config_contents(context.scene)


        if not armature:
            debug_print(f"MainPanel-RenameVertexGroups-Execute: Invalid Armature: {armature}")
            self.report({'WARNING'}, "Source Armature is not valid, please select a valid source armature")
            return {'CANCELLED'}
        
        if not template_config:
            self.report({'WARNING'}, "Template is invalid, please select a template")
            return {'CANCELLED'}

        BONE_MAPPING = template_config.get("bone_mapping")
        if not BONE_MAPPING:
            debug_print(f"MainPanel-RenameVertexGroups-Execute: Template Config: {template_config}")
            self.report({'WARNING'}, "Bone mapping in the template is invalid. Make sure the template is set up properly")
            return {'CANCELLED'}
        
        if armature and armature.type == 'ARMATURE':
            rename_vertex_groups(armature, BONE_MAPPING)
            self.report({'INFO'}, "Renamed vertex groups according to the set bone mapping")
        else:
            self.report({'WARNING'}, "Source Armature is invalid. Please select a valid armature")
        return {'FINISHED'}

class OBJECT_OT_import_t_quinn(bpy.types.Operator):
    bl_idname = "object.import_t_quinn"
    bl_label = "Import Quinn in T Pose"
    bl_description = "Import T pose Quinn"
    
    def execute(self, context):
        try:
            bpy.ops.import_scene.fbx(
                filepath=os.path.join(imports_dir, "Quinn_T_Pose.fbx"),
                primary_bone_axis='X',
                secondary_bone_axis='-Y',
                automatic_bone_orientation=False,
                ignore_leaf_bones=False
            )
        except Exception as e:
            self.report({'WARNING'}, f"Couldn't import Quinn: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class OBJECT_OT_move_pelvis(bpy.types.Operator):
    bl_idname = "object.move_pelvis"
    bl_label = "Move Pelvis"
    bl_description = "Move Pelvis"
    
    def execute(self, context):
        source_armature = context.scene.source_armature
        target_armature = context.scene.target_armature
        
        if not target_armature:
            self.report({'WARNING'}, f"No Target Armature, please select a target armature")
            return {'CANCELLED'}
        if not source_armature:
            self.report({'WARNING'}, f"No Source Armature, please select a source armature")
            return {'CANCELLED'}

        match_edit_bone_pos(target_armature, source_armature, 'pelvis', 'pelvis')
        bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

class OBJECT_OT_match_bone_positions(bpy.types.Operator):
    bl_idname = "object.match_bone_positions"
    bl_label = "Match Bone positions"
    bl_description = "Match the positions of the Epic SKM to the MB lab SKM"
    
    def execute(self, context):
        source_armature = context.scene.source_armature
        target_armature = context.scene.target_armature
        
        if not target_armature:
            self.report({'WARNING'}, f"Target armature not found. Please Import and set your target armature")
            return {'CANCELLED'}
        if not source_armature:
            self.report({'WARNING'}, f"No Source Armature, please select a source armature")
            return {'CANCELLED'}
        
        foot_z_location = get_foot_z_location(target_armature, 'foot_l')        
        template_config = get_template_config_contents(context.scene)
        
        if not template_config:
            debug_print("MainPanel-MatchBonePos-Execute: Template not found")
            self.report({'WARNING'}, f"No Template found, please select the appropriate Template from the dropdown")
            return {'CANCELLED'}

        TRANSFORM_MAP = template_config.get("transform_map")
        if not TRANSFORM_MAP:
            debug_print(f"MainPanel-MatchBonePos-Execute: transform_map not found in template. Template: {template_config}")
            self.report({'WARNING'}, f"No valid transform map found in the selected template.")
            return {'CANCELLED'}        
        try:
            apply_transform_map(TRANSFORM_MAP, foot_z_location, target_armature, source_armature)
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'ERROR'}, f"Could not apply transform map. Error: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}

class OBJECT_OT_enable_debug_print(bpy.types.Operator):
    bl_idname = "object.enable_debug_print"
    bl_label = "Enable Debug Print"
    bl_description = "Checkbox, which enables debug print"

    def execute(self, context):
           context.scene.enable_debug_print = not context.scene.enable_debug_print
           self.report({'INFO'}, f"Debug Print Enabled: {context.scene.enable_debug_print}")
           return {'FINISHED'}

class OBJECT_OT_open_blend_file_browser(bpy.types.Operator):
    bl_idname = "object.open_blend_file_browser"
    bl_label = "Browse For Blend File"
    bl_description = "Select a .blend file for shapekey animation"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH") # type: ignore

    def invoke(self, context, event):
        self.filepath = ''
        context.window_manager.fileselect_add(self)
        self.file_filter_glob = "*.blend"
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if self.filepath.lower().endswith(".blend"):
            context.scene.skeleswap_props.shapekey_animation_blend_path = self.filepath
            self.report({'INFO'}, f"Selected file: {self.filepath}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Please select a .blend file")
            return {'CANCELLED'}

class OBJECT_OT_link_blendshapes_animation(bpy.types.Operator):
    bl_idname = "object.link_blendshapes_animation"
    bl_label = "Link Blendshapes Animation"
    bl_description = "Link the MB lab face rig animation of the blendshapes, needed to convert them to facekeys"

    def execute(self, context):
        face_rig_armature = None
        skeleswap_props = context.scene.skeleswap_props
        shapekey_animation_blend_path = skeleswap_props.shapekey_animation_blend_path
        has_separate_face_rig = skeleswap_props.has_separate_face_rig
        shapekey_action_name = skeleswap_props.shapekey_action_name
        is_mb_to_epic = skeleswap_props.is_mb_to_epic
        potential_face_rig = context.object if (context.object and context.object.type == 'ARMATURE') and (context.object != context.scene.target_armature) and (context.object != context.scene.source_armature) else None
        
        if has_separate_face_rig or is_mb_to_epic:
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and 'face_rig' in obj.name.lower():
                    debug_print(f"MainPanel-LinkBlendShapesAnimations-Execute: Found face rig match: {obj.name}")
                    face_rig_armature = obj
                    break
            if not face_rig_armature:
                debug_print(f"MainPanel-LinkBlendShapesAnimations-Execute: No facerig found in scene, trying to see if selected object is a separate armature")
                debug_print(f"MainPanel-LinkBlendShapesAnimations-Execute: ptential_face_rig: {potential_face_rig}")
                if potential_face_rig:
                    debug_print(f"MainPanel-LinkBlendShapesAnimations-Execute: Separate selected armature found, treating it as the face rig. Selected armature : {potential_face_rig.name}")
                    face_rig_armature = potential_face_rig
                else:
                    self.report({'WARNING'}, f"No face rig found. Try selecting it in the viewport and try again")
                    debug_print('No separate face rig found')
                    return {"CANCELLED"}
        
        if is_mb_to_epic:
            filepath = os.path.join(imports_dir, "ARKIT_Blendshape_Animations_For_MB_Lab_FaceRig.blend")
            action_name = "52_Shapekeys"
        else:
            filepath = shapekey_animation_blend_path
            action_name = shapekey_action_name
        
        if not filepath:
            self.report({'WARNING'}, f"Please select your blend file")
            return {'CANCELLED'}
        if not action_name:
            self.report({'WARNING'}, f"Please fill in the Action Name input")
            return {'CANCELLED'}
        if not face_rig_armature:
            debug_print("MainPanel-LinkBlendShapesAnimations-Execute: No Face Rig Armature Found")
            self.report({'WARNING'}, f"No face rig found. Try selecting it in the viewport and try again")
            return {'CANCELLED'}
        try:
            link_animation(face_rig_armature, filepath, action_name)
            return {'FINISHED'}
        except Exception as e:
            debug_print(f"MainPanel-LinkBlendShapesAnimations-Execute: Failed to link animation. Error:{e}")
            self.report({'ERROR'}, f"Failed to link animation. Error:{e}")
            return {'CANCELLED'}

class OBJECT_OT_create_ar_kit_shape_keys(bpy.types.Operator):
    bl_idname = "object.create_ar_kit_shape_keys"
    bl_label = "Create ARKIT 52 Shape Keys"
    bl_description = "Creates the shapekeys needed for ARKIT based on the blendshapes animation"

    def execute(self, context):
        try:
            set_frame_to(1)
            file_path = os.path.join(data_dir, "blendshapes.json")
            shapekey_names = get_json_property(file_path, "blendshape_names")
            base_mesh = context.object

            duplicated_mesh = duplicate_mesh(base_mesh)
            armature = duplicated_mesh.parent
            delete_all_shapekeys(duplicated_mesh)
            apply_armature(duplicated_mesh, armature)
            create_basis_shape_key(duplicated_mesh)

            bpy.ops.object.select_all(action='DESELECT')
            base_mesh.select_set(True)
            duplicated_mesh.select_set(True)
            bpy.context.view_layer.objects.active = duplicated_mesh

            convert_animation_to_shapekeys(duplicated_mesh, shapekey_names)
            copy_shapekeys(duplicated_mesh, base_mesh)
            delete_mesh(duplicated_mesh)
            set_frame_to(1)
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create shapekeys. Error:{e}")
            return {'CANCELLED'}

        return {'FINISHED'}

class OBJECT_OT_remove_face_rig(bpy.types.Operator):
    bl_idname = "object.remove_face_rig"
    bl_label = "Remove Face Rig"
    bl_description = "Removes the face rig"

    def execute(self, context):
        skeleswap_props = context.scene.skeleswap_props
        has_separate_face_rig = skeleswap_props.has_separate_face_rig
        if skeleswap_props.is_mb_to_epic or has_separate_face_rig:
            potential_face_rig = context.object if (context.object and context.object.type == 'ARMATURE') and (context.object != context.scene.target_armature) and (context.object != context.scene.source_armature) else None
            for obj in bpy.data.objects:
                if obj.type == 'ARMATURE' and ('face_rig' in obj.name.lower() or 'phoneme_rig' in obj.name.lower()):
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    face_rig = obj
                    context.view_layer.objects.active = obj
                    debug_print(f"Selected armature: {obj.name}")
                    if(skeleswap_props.is_mb_to_epic):
                        delete_collection(face_rig)
                        self.report({'INFO'}, f"Deleted face rig and its collection")
                        return {'FINISHED'}
                    else:
                        delete_armature(face_rig)
                        self.report({'INFO'}, f"Deleted face rig armature")
                        return {'FINISHED'}
            if potential_face_rig:
                debug_print(f"MainPanel-RemoveFaceRig-Execute: Potential Face rig selected in view port. deleting: {potential_face_rig}")
                delete_armature(potential_face_rig)
                self.report({'INFO'}, f"Deleted face rig armature")
                return {'FINISHED'}
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class OBJECT_OT_reparent_breast_bones(bpy.types.Operator):
    bl_idname = "object.reparent_breast_bones"
    bl_label = "Re-Parent Breast Bones"
    bl_description = "Places The MB Lab breast bones onto the epic skeleton"

    def execute(self, context):
        source_armature = context.scene.source_armature
        target_armature = context.scene.target_armature

        template_config = get_template_config_contents(context.scene)
        if not template_config:
            self.report({'WARNING'}, "No template config found. Make sure to select a template from the dropdown")
            return {'CANCELLED'}

        BONE_MAPPING = template_config.get("bone_mapping")
        if not BONE_MAPPING:
            debug_print(f"MainPanel-ReparentBreastBones-Execute: No bone_mapping -> Template Config: {template_config}")
            self.report({'WARNING'}, "Bone mapping in the template is invalid. Make sure the template is set up properly")
            return {'CANCELLED'}
        try:
            copy_bone_between_skeletons(source_armature, target_armature, 'breast_L', 'spine_05') # TBD: Create Operator, that allows for copying bones over to the armature. Select new parent bone on target armature, select the bone to copy, rename the bone according to the vertex group
            rename_bone(target_armature, 'breast_L', 'breast_l')
            copy_bone_between_skeletons(source_armature, target_armature, 'breast_R', 'spine_05')
            rename_bone(target_armature, 'breast_R', 'breast_r')
            match_pose_bone_head_pos(target_armature, source_armature, "breast_l", BONE_MAPPING["breast_l"])
            match_pose_bone_head_pos(target_armature, source_armature, "breast_r", BONE_MAPPING["breast_r"])
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            self.report({'ERROR'}, f"Couldn't reparent breast bones. Error: {e}")
            debug_print(f"Couldn't reparent breast bones. Error: {e}")
            return {"CANCELLED"}
        return {'FINISHED'}
# ________________________________________________________
class OBJECT_OT_replace_skeleton(bpy.types.Operator):
    bl_idname = "object.replace_skeleton"
    bl_label = "Replace Skeleton"
    bl_description = "Replaces existing skeleton to the eipc skeleton"

    def execute(self, context):
        source_armature = context.scene.source_armature
        target_armature = context.scene.target_armature
        skeleswap_props = context.scene.skeleswap_props
        template_config = get_template_config_contents(context.scene)

        bpy.ops.object.mode_set(mode='OBJECT')
        
        if not target_armature:
            self.report({'WARNING'}, f"No Target Armature, please select a target armature")
            return {'CANCELLED'}
        if not source_armature:
            self.report({'WARNING'}, f"No Source Armature, please select a source armature")
            return {'CANCELLED'}

        
        if not template_config:
            self.report({'WARNING'}, "Template is invalid, please select a template")
            return {'CANCELLED'}

        BONE_MAPPING = template_config.get("bone_mapping")
        if not BONE_MAPPING:
            debug_print(f"MainPanel-ReplaceSkeleton-Execute: Template Config: {template_config}")
            self.report({'WARNING'}, "Bone mapping in the template is invalid. Make sure the template is set up properly")
            return {'CANCELLED'}


        source_mesh = [child for child in source_armature.children if child.type == 'MESH'][0] # TBD error handling
        target_mesh = [child for child in target_armature.children if child.type == 'MESH'][0]

        if not target_mesh:
            self.report({'WARNING'}, f"No Target Mesh")
            return {'CANCELLED'}
        if not source_mesh:
            self.report({'WARNING'}, f"No Source Mesh")
            return {'CANCELLED'}

        unmapped_bones = []
        for bone in target_armature.pose.bones:
            target_bone = BONE_MAPPING.get(bone.name)
            if not target_bone:
                unmapped_bones.append(bone.name)

        if context.scene.target_is_epic_skeleton:
            unmapped_bones.extend(["spine_01", "spine_02", "spine_03", "spine_04", "spine_05"])
        if source_mesh and target_mesh:
            try:
                if skeleswap_props.has_facial_animations:
                    duplicated_mesh = duplicate_mesh(source_mesh)
                    apply_armature(target_mesh, target_armature)
                    apply_pose_as_rest_pose(target_armature)
                    delete_all_shapekeys(source_mesh)
                    transfer_weights_for_specific_bones(unmapped_bones, source_mesh, target_mesh)
                    delete_armature(source_armature)
                    parent_armature(target_mesh, target_armature)
                    parent_armature(source_mesh, target_armature)
                    apply_armature(source_mesh, source_armature)
                    copy_shapekeys(duplicated_mesh, source_mesh)
                    delete_mesh(duplicated_mesh)
                    delete_mesh(target_mesh)
                else:
                    apply_armature(target_mesh, target_armature)
                    apply_pose_as_rest_pose(target_armature)
                    delete_all_shapekeys(source_mesh)
                    apply_armature(source_mesh, source_armature)
                    delete_armature(source_armature)
                    parent_armature(target_mesh, target_armature)
                    parent_armature(source_mesh, target_armature)
                    transfer_weights_for_specific_bones(unmapped_bones, source_mesh, target_mesh)
                    delete_mesh(target_mesh)
            except Exception as e:
                self.report({'ERROR'}, f"Couldn't replace skeleton. Error: {e}")
                debug_print(f"Couldn't replace skeleton. Error: {e}")
                return {"CANCELLED"}
        else:
           debug_print(f"MainPanel-ReplaceSkeleton-Execute: No mesh found: source_mesh: {source_mesh}, target_mesh: {target_mesh}, source_armature: {source_armature.name}, target_armature: {target_armature.name}")
           self.report({'WARNING'}, f"No source or target mesh found. Makes sure they are not hidden from the scene")
           return {"CANCELLED"} 
        return {'FINISHED'}

class OBJECT_OT_fix_hand_ik_bones(bpy.types.Operator):
    bl_idname = "object.fix_hand_ik_bones"
    bl_label = "Add&Apply Constraint to IK bones"
    bl_description = "Adds and applies copy location&rotation constraints to the hand&gun IK bones"


    def execute(self, context):
        target_armature = context.scene.target_armature
        if not target_armature:
            self.report({'WARNING'}, f"No Target Armature, please select a target armature")
            return {'CANCELLED'}
        try:
            add_copy_location_constraint(target_armature, 'ik_hand_l', 'hand_l')
            add_copy_rotation_constraint(target_armature, 'ik_hand_l', 'hand_l')
            add_copy_location_constraint(target_armature, 'ik_hand_r', 'hand_r')
            add_copy_rotation_constraint(target_armature, 'ik_hand_r', 'hand_r')
            add_copy_location_constraint(target_armature, 'ik_hand_gun', 'hand_r')
            add_copy_rotation_constraint(target_armature, 'ik_hand_gun', 'hand_r')

            apply_bone_constraints(target_armature)
        except Exception as e:
                self.report({'ERROR'}, f"Couldn't constrain IK bones. Error: {e}")
                debug_print(f"Couldn't constrain IK bones. Error: {e}")
                return {"CANCELLED"}
        return {'FINISHED'}

class OBJECT_OT_create_lods(bpy.types.Operator):
    bl_idname = "object.create_lods"
    bl_label = "Create LODs"
    bl_description = "Creates between 1 and 5 LODs, based on the number input"

    # TBD: Make it actually useful

    def execute(self, context):
        skelswap_props = context.scene.skeleswap_props
        user_input = skelswap_props.lod_count
        mesh = context.object
        armature = mesh.parent
        current_lod = None

        if not mesh or not armature:
            self.report({'ERROR'}, "Select a mesh with an armature parent!")
            return {'CANCELLED'}

        for index in range(user_input):
            current_lod = duplicate_mesh(mesh)
            rename_mesh(current_lod, f"LOD_{index+1}")
            
            if not index >= 3: 
                add_decimate_modifier(current_lod, "un-subdivide", index+1)
            else:
                add_decimate_modifier(current_lod, "un-subdivide", index-1)
                add_decimate_modifier(current_lod, "collapse", 0.1)
            parent_armature(current_lod, armature)
            transfer_weights(mesh, current_lod)

        self.report({'INFO'}, f"{user_input} LOD(s) created successfully.")
        return {'FINISHED'}
    

# ________________________________________________________

class OBJECT_OT_export_character_as_FBX(bpy.types.Operator):
    bl_idname = "object.export_character_as_fbx"
    bl_label = "Export Character as FBX"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH") # type: ignore

    def execute(self, context):
        armature = context.scene.target_armature
        if not armature or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Invalid target armature")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')

        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        
        for obj in armature.children:
            if obj.type == 'MESH':
                obj.select_set(True)

        bpy.ops.export_scene.fbx(
            filepath=self.filepath,
            use_selection=True,
            use_armature_deform_only=True,
            add_leaf_bones=False,
            primary_bone_axis='X',
            secondary_bone_axis='-Y',
            mesh_smooth_type='FACE',
            bake_anim=False
        )
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(SkeleSwapProperties)
    bpy.types.Scene.skeleswap_props = bpy.props.PointerProperty(type=SkeleSwapProperties)

    bpy.types.Scene.source_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_source_armature)
    bpy.types.Scene.target_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_target_armature)

    bpy.utils.register_class(OBJECT_PT_skeleswap_main_panel)
    bpy.utils.register_class(OBJECT_OT_enable_debug_print)
    bpy.utils.register_class(OBJECT_OT_setup_scene_for_epic_skeleton)
    bpy.utils.register_class(OBJECT_OT_adjust_scale)
    bpy.utils.register_class(OBJECT_OT_rename_vertex_groups)
    bpy.utils.register_class(OBJECT_OT_import_t_quinn)
    bpy.utils.register_class(OBJECT_OT_move_pelvis)
    bpy.utils.register_class(OBJECT_OT_match_bone_positions)
    bpy.utils.register_class(OBJECT_OT_reparent_breast_bones)
    bpy.utils.register_class(OBJECT_OT_open_blend_file_browser)
    bpy.utils.register_class(OBJECT_OT_link_blendshapes_animation)
    bpy.utils.register_class(OBJECT_OT_create_ar_kit_shape_keys)
    bpy.utils.register_class(OBJECT_OT_remove_face_rig)
    bpy.utils.register_class(OBJECT_OT_replace_skeleton)
    bpy.utils.register_class(OBJECT_OT_fix_hand_ik_bones)
    bpy.utils.register_class(OBJECT_OT_create_lods)
    bpy.utils.register_class(OBJECT_OT_select_template_config)
    bpy.utils.register_class(OBJECT_OT_export_character_as_FBX)
    bpy.utils.register_class(OBJECT_PT_facial_operators_panel)

    bpy.types.Scene.selected_template_config = bpy.props.EnumProperty(
        name="Template",
        items=lambda self, context: [(option, option, "") for option in get_template_config_options()],
        update=template_config_update_callback
    )
    bpy.types.Scene.template = bpy.props.StringProperty(name="Template")
    bpy.types.Scene.target_is_epic_skeleton = bpy.props.BoolProperty(name="Is Target Epic Skeleton", default=True)
    
    def force_select_template_config():
        debug_print(f"MainPanel-ForceSelectTemplateConfig: Force selected default Template")
        bpy.ops.object.select_template_config()
        return None 
    bpy.app.timers.register( force_select_template_config, first_interval=0.1 ) # force the inital selected template to run the execute function to load necessary data
def unregister():
    bpy.utils.unregister_class(OBJECT_PT_skeleswap_main_panel)
    bpy.utils.unregister_class(OBJECT_OT_enable_debug_print)
    bpy.utils.unregister_class(OBJECT_OT_setup_scene_for_epic_skeleton)
    bpy.utils.unregister_class(OBJECT_OT_adjust_scale)
    bpy.utils.unregister_class(OBJECT_OT_rename_vertex_groups)
    bpy.utils.unregister_class(OBJECT_OT_import_t_quinn)
    bpy.utils.unregister_class(OBJECT_OT_move_pelvis)
    bpy.utils.unregister_class(OBJECT_OT_match_bone_positions)
    bpy.utils.unregister_class(OBJECT_OT_reparent_breast_bones)
    bpy.utils.unregister_class(OBJECT_OT_open_blend_file_browser)
    bpy.utils.unregister_class(OBJECT_OT_link_blendshapes_animation)
    bpy.utils.unregister_class(OBJECT_OT_create_ar_kit_shape_keys)
    bpy.utils.unregister_class(OBJECT_OT_remove_face_rig)
    bpy.utils.unregister_class(OBJECT_OT_replace_skeleton)
    bpy.utils.unregister_class(OBJECT_OT_fix_hand_ik_bones)
    bpy.utils.unregister_class(OBJECT_OT_create_lods)
    bpy.utils.unregister_class(OBJECT_OT_select_template_config)
    bpy.utils.unregister_class(SkeleSwapProperties)
    bpy.utils.unregister_class(OBJECT_OT_export_character_as_FBX)
    bpy.utils.unregister_class(OBJECT_PT_facial_operators_panel)
    del bpy.types.Scene.skeleswap_props
    del bpy.types.Scene.enable_debug_print
    del bpy.types.Scene.selected_template_config
    del bpy.types.Scene.template
    del bpy.types.Scene.target_is_epic_skeleton

if __name__ == "__main__":
    register()