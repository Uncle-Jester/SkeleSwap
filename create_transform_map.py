import bpy
from bpy.props import PointerProperty, StringProperty, EnumProperty, FloatProperty, BoolProperty, CollectionProperty
from bpy.types import Operator, Panel, PropertyGroup, UIList
from mathutils import Matrix, Vector
import json
import os

from .utils import rotate_bone, match_pose_bone_head_pos, match_edit_bone_pos, chain_pose_bone_position, scale_pose_bone, match_pose_bone_orientation, get_foot_z_location, move_pose_bone, orient_bone, move_edit_bone, assign_bone_color_to_armature
from .utils import is_flipped_unreal_bone
from .utils import debug_print

class BoneTransformPanel(bpy.types.Panel):
    bl_label = "Armature and Bone Selector"
    bl_idname = "OBJECT_PT_armature_bone_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bone Transform Mapping"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        
        row = layout.row()
        row.prop(scene, "selected_bone_mapping")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(scene, "source_armature", text="Source Armature")
        sub_row.prop(scene, "target_armature", text="Target Armature")
        
        row = layout.row()
        row.operator("object.assign_color_to_armatures", text="Assign Color to armatures")
        
        row = layout.row()
        row.prop(scene, "selected_source_bone", text="Source Bone")
        row.operator("object.select_source_bone_from_viewport", text="Select Source Bone")
        
        row = layout.row()
        row.prop(scene, "selected_target_bone", text="Target Bone")
        row.operator("object.select_target_bone_from_viewport", text="Select Target Bone")

        layout.prop(scene, "axis", text="Axis")
        layout.prop(scene, "value", text="Transform Value")
        layout.prop(scene, "global_axis", text="Global Axis")
        layout.prop(scene, "mirror", text="Mirror")

        layout.prop(scene, "transform_type", text='Transform Type')

        layout.operator("object.add_transform", text="Add Transform")
        
        layout.template_list("OBJECT_UL_transform_list", "", scene, "transform_list", scene, "transform_list_index")
        
        row = layout.row()
        row.operator("object.export_bone_transform", text="Export JSON")
        row.operator("object.save_bone_transform", text="Save Bove Transforms")
        row.operator("object.load_bone_transform", text="Load Bone Transforms")


class Transform_item(PropertyGroup):
    name: StringProperty(name="Name")
    description: StringProperty(name="Description")
    transform_type: StringProperty(name="Transform Type", default='rotate_bone')
    revert_data: bpy.props.StringProperty(name="Revert Data", default="{}")
    transform_details: bpy.props.StringProperty(name="Transform Details", default="{}")


    def set_data(self, data, data_type="revert_data"):
        if not data or data.items():
            self.revert_data
        for key, value in data.items():
            if isinstance(value, bpy.types.Object):
                data[key] = {"name": value.name, "type": value.type}
            elif isinstance(value, bool):
                data[key] = value
            elif isinstance(value, (Matrix, Vector)):
                if isinstance(value, Matrix):
                    data[key] = [list(row) for row in value]
                elif isinstance(value, Vector):
                    data[key] = list(value)
        self[data_type] = json.dumps(data)

    def get_data(self, data_type="revert_data"):
        data = json.loads(self[data_type])
        for key, value in data.items():
            if isinstance(value, dict) and "name" in value and "type" in value:
                obj_name = value["name"]
                obj_type = value["type"]
                if obj_type == "ARMATURE" and obj_name in bpy.data.objects:
                    data[key] = bpy.data.objects[obj_name]
                elif obj_type == "MESH" and obj_name in bpy.data.objects:
                    data[key] = bpy.data.objects[obj_name]
            elif isinstance(value, list):
                if len(value) == 4 and all(isinstance(x, (int, float)) for x in value):
                    data[key] = Matrix(value).to_4x4()
                elif len(value) == 3 and all(isinstance(x, (int, float)) for x in value):
                    data[key] = Vector(value)
                else:
                    data[key] = value
        return data


def add_transform(context, target_bone_name, source_bone_name, global_axis, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator):
    scene = context.scene

    target_armature = (
        scene.target_armature if target_armature_indicator == "T"
        else scene.source_armature if target_armature_indicator == "S"
        else None
    )
    source_armature = (
        scene.source_armature if source_armature_indicator == "S"
        else scene.target_armature if source_armature_indicator == "T"
        else None
    )
    new_transform = None
    if transform_type == 'rotate_bone':
        revert_data = rotate_bone(target_armature, target_bone_name, axis, transform_value, global_axis, mirror) # calls the function and saves the return value, which can be used to revert the changes
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "axis":axis, "transform_value": transform_value, "global_axis": global_axis, "mirror": mirror}, 'transform_details')
        new_transform.name = f"Rotate Bone {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    elif transform_type == 'scale_bone':
        revert_data = scale_pose_bone(target_armature, target_bone_name, transform_value, axis, global_axis)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "transform_value":transform_value, "axis": axis, "global_axis": global_axis}, 'transform_details')            
        new_transform.name = f"Scale Bone {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    elif transform_type == 'match_pose_bone_head_pos':
        foot_z_location = None if "foot" not in target_bone_name else get_foot_z_location(target_armature, target_bone_name)
        revert_data = match_pose_bone_head_pos(target_armature, source_armature, target_bone_name, source_bone_name, foot_z_location)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name, "foot_z_location": foot_z_location}, 'transform_details')
        new_transform.name = f"Match Pose Bone Head Position {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    elif transform_type == 'match_pose_bone_orientation':
        unreal_right = False if target_armature_indicator == "S" else is_flipped_unreal_bone(target_bone_name, scene.target_is_epic_skeleton)
        effect_roll = False
        revert_data = match_pose_bone_orientation(target_armature, source_armature, target_bone_name, source_bone_name, effect_roll, unreal_right)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name, "unreal_right": unreal_right}, 'transform_details')
        new_transform.name = f"Match Pose Bone Orientation {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    elif transform_type == 'chain_pose_bone_position':
        revert_data = chain_pose_bone_position(target_armature, target_bone_name, source_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name}, 'transform_details')
        new_transform.name = f"Chain Bone {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    elif transform_type == 'match_edit_bone_pos':
        revert_data = match_edit_bone_pos(target_armature, source_armature, target_bone_name, source_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name}, 'transform_details')
        new_transform.name = f"Match Edit Bone Head Position {target_armature.name}-{target_bone_name} {global_axis} {axis}-{transform_value} - mirrored = {mirror}"
    else:
        raise ValueError(f"In CreateTransformMap-AddTransform: Invalid transform type: {transform_type}")
    return new_transform if new_transform else None


class OBJECT_OT_add_transform(bpy.types.Operator):
    bl_idname = "object.add_transform"
    bl_label = "Add Transform"

    def execute(self, context):
        scene = context.scene

        target_bone_name = scene.selected_target_bone
        source_bone_name = scene.selected_source_bone
        target_armature_indicator = scene.target_armature_indicator
        source_armature_indicator = scene.source_armature_indicator
        global_axis = scene.global_axis
        axis = scene.axis
        transform_value = scene.value
        mirror = scene.mirror

        transform_type = scene.transform_type
        new_transform = add_transform(context, target_bone_name, source_bone_name, global_axis, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator)
        
        self.report({'INFO'}, f"{new_transform.name} added to the list")
        return {'FINISHED'}

class OBJECT_UL_transform_list(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        transform = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=transform.name)
            layout.operator("object.remove_transform", text="", icon='X', emboss=False).index = index
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=transform.name)

class OBJECT_OT_remove_transform(bpy.types.Operator):
    bl_idname = "object.remove_transform"
    bl_label = "Remove Transform"

    index: bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        revert_data = scene.transform_list[self.index].get_data("revert_data")
        if not revert_data:
           scene.transform_list.remove(self.index)
 
        if scene.transform_list[self.index].transform_type == "rotate_bone":
            rotate_bone(
                revert_data['armature'], 
                revert_data['bone_name'], 
                revert_data['axis'], 
                revert_data['degrees'], 
                revert_data['global_axis'], 
                revert_data['mirror']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted rotation for bone: {revert_data['bone_name']}")
        elif scene.transform_list[self.index].transform_type == "scale_bone":
            scale_pose_bone(
                revert_data['armature'], 
                revert_data['bone_name'], 
                revert_data['scale_value'], 
                revert_data['axis'], 
                revert_data['global_axis']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted scale for bone: {revert_data['bone_name']}")
        elif scene.transform_list[self.index].transform_type == "match_pose_bone_head_pos":
            move_pose_bone(
                revert_data['armature'], 
                revert_data['bone_name'], 
                revert_data['previous_head_position'], 
                revert_data['foot_z_location']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted head position for bone: {revert_data['bone_name']}")
        elif scene.transform_list[self.index].transform_type == "match_pose_bone_orientation":
            orient_bone(
                revert_data['armature'], 
                revert_data['bone_name'], 
                revert_data['orientation'], 
                revert_data['effect_roll']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted orientation for bone: {revert_data['bone_name']}")
        elif scene.transform_list[self.index].transform_type == "chain_pose_bone_position":
            move_pose_bone(
                revert_data['armature'], 
                revert_data['bone_name'], 
                revert_data['previous_head_position']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted orientation for bone: {revert_data['bone_name']}")
        elif scene.transform_list[self.index].transform_type == "match_edit_bone_pos":
            move_edit_bone(
                revert_data['target_armature'], 
                revert_data['target_bone_name'], 
                revert_data['offset']
            )
            debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted edit bone position for bone: {revert_data['target_bone_name']}")

        else:
            print('TBD')
        scene.transform_list.remove(self.index)
        return {'FINISHED'}


class OBJECT_OT_select_source_bone(bpy.types.Operator):
    bl_idname = "object.select_source_bone_from_viewport"
    bl_label = "Select Source Bone From Viewport"
    
    def execute(self, context):
        selected_object = context.view_layer.objects.active
        if selected_object and selected_object.type == 'ARMATURE':
            if context.active_object.mode == 'POSE':
                selected_source_bone = context.selected_pose_bones
                selected_target_bone = context.scene.selected_target_bone if context.scene.selected_target_bone else ""
                if selected_source_bone:
                    context.scene.selected_source_bone = selected_source_bone[0].name
                    context.scene.source_armature_indicator = 'S' if selected_object.name == context.scene.source_armature.name else 'T'
                    mapping_content = get_bone_mapping_contents(context.scene)
                    debug_print(f"CreateTransformMap-SelectingSourceBone: mapping_content: {mapping_content}")
                    if mapping_content:
                        paired_target_bone = None
                        for target_bone, source_bone in mapping_content.items():
                            if source_bone == context.scene.selected_source_bone:
                                paired_target_bone = target_bone
                                break
                        context.scene.selected_target_bone = paired_target_bone if paired_target_bone else selected_target_bone
                        if context.scene.selected_target_bone:
                            context.scene.target_armature_indicator = 'T' if selected_object.name != context.scene.target_armature.name else 'S' # this is a terrible way to do it i hate it but i am tired...alas
                    
                    return {'FINISHED'}
        return {'CANCELLED'}

class OBJECT_OT_select_target_bone(bpy.types.Operator):
    bl_idname = "object.select_target_bone_from_viewport"
    bl_label = "Select Target Bone From Viewport"
    
    def execute(self, context):
        selected_object = context.view_layer.objects.active
        if selected_object and selected_object.type == 'ARMATURE':
            if context.active_object.mode == 'POSE':
                selected_target_bone = context.selected_pose_bones
                selected_source_bone = context.scene.selected_source_bone
                if selected_target_bone:
                    context.scene.selected_target_bone = selected_target_bone[0].name
                    context.scene.target_armature_indicator = 'T' if selected_object.name == context.scene.target_armature.name else 'S'
                    mapping_content = get_bone_mapping_contents(context.scene)
                    debug_print(f"CreateTransformMap-SelectingTargetBone: mapping_content: {mapping_content}")
                    if not selected_source_bone and mapping_content:
                        paired_source_bone = mapping_content.get(context.scene.selected_target_bone)
                        context.scene.selected_source_bone = paired_source_bone if paired_source_bone else ""
                        if context.scene.selected_source_bone:
                            context.scene.source_armature_indicator = 'S' if selected_object.name != context.scene.source_armature.name else 'T'
                    return {'CANCELLED'}
        return {'CANCELLED'}

def update_source_armature(self, context):
    armature = bpy.context.scene.source_armature
    debug_print('CreateTransformMap-UpdateSourceArmature: updated source armature')
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.source_armature = None

def update_target_armature(self, context):
    debug_print("CreateTransformMap-UpdateSourceArmature:updated source armature")
    armature = bpy.context.scene.target_armature
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.target_armature = None

def get_bone_mapping_options():
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    utils_dir = os.path.join(addon_dir, "utils")
    data_dir = os.path.join(utils_dir, "data")
    json_file_path = os.path.join(data_dir, "bone_mappings.json")

    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
                return list(data.keys())
            except json.JSONDecodeError:
                return []
    return []

def get_bone_mapping_contents(scene):
    if scene.bone_mapping_contents:
        return json.loads(scene.bone_mapping_contents)
    else:
        return {}

def set_bone_mapping_contents(scene, mapping):
    scene.bone_mapping_contents = json.dumps(mapping)

def bone_mapping_update_callback(self, context):
    debug_print('CreateTransformMape-BoneMappingUpdateCallback: Updating selected bone map')
    bpy.ops.object.select_bone_mapping()

class OBJECT_OT_select_bone_mapping(bpy.types.Operator):
    bl_idname = "object.select_bone_mapping"
    bl_label = "Select Bone Mapping"

    selected_bone_mapping: bpy.props.EnumProperty(
        name="Bone Mapping",
        items=lambda self, context: [(option, option, "") for option in get_bone_mapping_options()],
        )

    def execute(self, context):
        debug_print('CreateTransformMap-SelectBoneMapping-Execute: Executing select_bone_mapping')
        selected_mapping_name = context.scene.selected_bone_mapping
        debug_print(f"CreateTransformMap-SelectBoneMapping-Execute: Selected bone mapping name: {selected_mapping_name}")

        addon_dir = os.path.dirname(os.path.realpath(__file__))
        utils_dir = os.path.join(addon_dir, "utils")
        data_dir = os.path.join(utils_dir, "data")
        json_file_path = os.path.join(data_dir, "bone_mappings.json")
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                try:
                    data = json.load(json_file)
                    if data and data.get(selected_mapping_name):
                        mapping_contents = data[selected_mapping_name]
                        debug_print(f"CreateTransformMap-SelectBoneMapping-Execute: selected_bone_mapping_contents: {mapping_contents}")
                        set_bone_mapping_contents(context.scene, mapping_contents)
                except json.JSONDecodeError:
                    print("Failed to load bone mapping data")
                    return {}
        else:
            return {'ERROR'}
        self.report({'INFO'}, f"Selected bone mapping: {selected_mapping_name}")
        return {'FINISHED'}


class OBJECT_OT_assign_color_to_armatures(bpy.types.Operator):
    bl_idname = "object.assign_color_to_armatures"
    bl_label = "Refresh Bone Mapping"

    def execute(self, context):
        armature1 = context.scene.source_armature
        armature2 = context.scene.target_armature
        if armature1 and armature2:
            debug_print('CreateTransformMap-AssignColorToArmatures: Assigning colors')
            assign_bone_color_to_armature(armature1, (1,95,100))
            assign_bone_color_to_armature(armature2, (115,30,0))
        return {'FINISHED'}


def create_bone_transform_json(scene):
    bone_transform_list = []
    bone_transform_json = {}

    for transform in scene.transform_list:
        bone_transform_list.append(transform.get_data('transform_details'))
    bone_transform_json["transforms"] = bone_transform_list
    return bone_transform_json


class OBJECT_OT_export_bone_transform(bpy.types.Operator):
    bl_idname = "object.export_bone_transform"
    bl_label = "Export Bone Mapping"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="bone_transforms.json")

    def execute(self, context):
        scene = context.scene
        bone_transform_list = create_bone_transform_json(scene)
        
        file_path = self.filepath
        
        if not file_path.endswith(".json"):
            file_path += ".json"
        
        try:
            with open(file_path, 'w') as json_file:
                json.dump(bone_transform_list, json_file, indent=4)
            self.report({'INFO'}, f"Bone transform list exported to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export bone transform list {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        file_name = f"{context.scene.input_text}_transforms.json" or "bone_transforms.json"
        self.filepath = bpy.path.abspath(f"//{file_name}")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OBJECT_OT_save_bone_transform(bpy.types.Operator):
    bl_idname = "object.save_bone_transform"
    bl_label = "Save Bone Mapping"

    def execute(self, context):
        scene = context.scene
        bone_transform = create_bone_transform_json(scene)

        addon_dir = os.path.dirname(os.path.realpath(__file__))
        utils_dir = os.path.join(addon_dir, "utils")
        data_dir = os.path.join(utils_dir, "data")
        json_file_path = os.path.join(data_dir, "bone_transforms.json")
        property_name = context.scene.input_text or "default_property"

        try:
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r+') as json_file:
                    data = json.load(json_file)
                    data[property_name] = bone_transform
                    json_file.seek(0)
                    json.dump(data, json_file, indent=4)
                    json_file.truncate()
            else:
                with open(json_file_path, 'w') as json_file:
                    data = {property_name: bone_transform}
                    json.dump(data, json_file, indent=4)
            
            self.report({'INFO'}, f"Bone transform saved under '{property_name}'")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save bone transform: {e}")

        return {'FINISHED'}


class OBJECT_OT_load_bone_transform(bpy.types.Operator):
    bl_idname = "object.load_bone_transform"
    bl_label = "Load Bone Transforms"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        scene = context.scene
        try:
            with open(self.filepath, 'r') as json_file:
                json_object = json.load(json_file)
                bone_transforms = json_object["transforms"]

            scene.transform_list.clear()
            for transform_data in bone_transforms:
                target_bone_name = transform_data.get("target_bone_name")
                source_bone_name = transform_data.get("source_bone_name")
                global_axis = transform_data.get("global_axis")
                axis = transform_data.get("axis")
                transform_value = transform_data.get("transform_value")
                mirror = transform_data.get("mirror")
                transform_type = transform_data.get("transform_type")
                target_armature_indicator = transform_data.get("target_armature_indicator")
                source_armature_indicator = transform_data.get("source_armature_indicator")
                add_transform(context, target_bone_name, source_bone_name, global_axis, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator)

            self.report({'INFO'}, f"Bone transform loaded from {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load bone transform: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(BoneTransformPanel)
    bpy.utils.register_class(OBJECT_OT_assign_color_to_armatures)
    bpy.utils.register_class(OBJECT_OT_select_source_bone)
    bpy.utils.register_class(OBJECT_OT_select_target_bone)
    bpy.utils.register_class(Transform_item)
    bpy.utils.register_class(OBJECT_OT_add_transform)
    bpy.utils.register_class(OBJECT_OT_remove_transform)
    bpy.utils.register_class(OBJECT_UL_transform_list)
    bpy.utils.register_class(OBJECT_OT_select_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_export_bone_transform)
    bpy.utils.register_class(OBJECT_OT_save_bone_transform)
    bpy.utils.register_class(OBJECT_OT_load_bone_transform)


    bpy.types.Scene.source_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_source_armature)
    bpy.types.Scene.target_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_target_armature)
    bpy.types.Scene.selected_source_bone = bpy.props.StringProperty(name="Selected Source Bone")
    bpy.types.Scene.selected_target_bone = bpy.props.StringProperty(name="Selected Target Bone")
    
    bpy.types.Scene.source_armature_indicator = bpy.props.StringProperty(name="Source Armature Indicator for Transform")
    bpy.types.Scene.target_armature_indicator = bpy.props.StringProperty(name="Target Armature Indicator for Transform")

    bpy.types.Scene.mirror = BoolProperty(name="Mirror", default=False)
    bpy.types.Scene.value = FloatProperty(name="Transform Value", default=0.0)
    bpy.types.Scene.global_axis = BoolProperty(name="Global Axis", default=False)
    


    bpy.types.Scene.selected_bone_mapping = bpy.props.EnumProperty(
        name="Bone Mapping",
        items=lambda self, context: [(option, option, "") for option in get_bone_mapping_options()],
        update=bone_mapping_update_callback
    )
    bpy.types.Scene.bone_mapping_contents = bpy.props.StringProperty(name="Bone Mapping Contents")

    def force_select_bone_mapping():
        bpy.ops.object.select_bone_mapping()
        return None 
    bpy.app.timers.register( force_select_bone_mapping, first_interval=0.1 ) # force the inital selected bone mapping to run the execute function to load necessary data

    bpy.types.Scene.axis = EnumProperty(
        name="Axis",
        items=[
            ('X', "X", ""),
            ('Y', "Y", ""),
            ('Z', "Z", ""),
            ('NONE', "None", ""), # this is for scaling. not selecting an axis means it will scale on all of them the same amount
        ],
        default='X',
    )


    bpy.types.Scene.transform_type = EnumProperty(
        name='Transform Type',
        items=[
            ('rotate_bone', "Rotate Bone", "Rotate Bone"),
            ('scale_bone', "Scale Bone", "Scale Bone"),
            ('match_pose_bone_head_pos', "Match Pose Bone Head Position", "Match Pose Bone Head Position"),
            ('match_pose_bone_orientation', "Match Pose Bone Orientation", "Match Pose Bone Orientation"),
            ('chain_pose_bone_position', "Chain Bone", "Chain Bone"),
            ('match_edit_bone_pos', "Match Edit Bone Head Position", "Match Edit Bone Head Position")
        ],
        default='rotate_bone'
    )


    

    bpy.types.Scene.transform_list = CollectionProperty(type=Transform_item)
    bpy.types.Scene.transform_list_index = bpy.props.IntProperty()

def unregister():
    bpy.utils.unregister_class(BoneTransformPanel)
    bpy.utils.unregister_class(OBJECT_OT_assign_color_to_armatures)
    bpy.utils.unregister_class(OBJECT_OT_select_source_bone)
    bpy.utils.unregister_class(OBJECT_OT_select_target_bone)
    bpy.utils.unregister_class(Transform_item)
    bpy.utils.unregister_class(OBJECT_OT_add_transform)
    bpy.utils.unregister_class(OBJECT_OT_remove_transform)
    bpy.utils.unregister_class(OBJECT_UL_transform_list)
    bpy.utils.unregister_class(OBJECT_OT_select_bone_mapping)
    bpy.utils.unregister_class(OBJECT_OT_export_bone_transform)
    bpy.utils.unregister_class(OBJECT_OT_save_bone_transform)
    bpy.utils.unregister_class(OBJECT_OT_load_bone_transform)

    del bpy.types.Scene.source_armature
    del bpy.types.Scene.target_armature
    del bpy.types.Scene.selected_source_bone
    del bpy.types.Scene.selected_target_bone
    del bpy.types.Scene.source_armature_indicator
    del bpy.types.Scene.target_armature_indicator
    del bpy.types.Scene.mirror
    del bpy.types.Scene.global_axis
    del bpy.types.Scene.value
    del bpy.types.Scene.selected_bone_mapping
    bpy.types.Scene.bone_mapping_contents

    del bpy.types.Scene.axis
    del bpy.types.Scene.transform_type
    del bpy.types.Scene.transform_list
    del bpy.types.Scene.transform_list_index

if __name__ == "__main__":
    register()