import bpy # type: ignore
from mathutils import Matrix, Vector # type: ignore
import json
import os

from .utils import rotate_bone, match_pose_bone_head_pos, match_edit_bone_pos, chain_pose_bone_position, scale_pose_bone, match_pose_bone_orientation, get_foot_z_location, move_pose_bone, orient_bone, move_edit_bone, assign_bone_color_to_armature, match_edit_bone_z_location, match_edit_bone_chain_scale, scale_edit_bone_chain, copy_bone_between_armatures, delete_edit_bone
from .utils import is_flipped_unreal_bone
from .utils import debug_print, get_current_json_data_file_path, save_to_persistent_data_store_json_property
from .utils.dev_utils import validate

class CreateTransformProperties(bpy.types.PropertyGroup):
    create_transform_foot_z_location: bpy.props.StringProperty(name="Foot Z Location", default="")  # type: ignore
    apply_on_load: bpy.props.BoolProperty(name="Load Transform Map Without Applying", default=False)  # type: ignore
    new_bone_name: bpy.props.StringProperty(name="Name of the new Bone", default="") # type: ignore
    transform_map_name_input: bpy.props.StringProperty(name="Transform Map Name", default="") # type: ignore
    transform_target_is_epic_skeleton: bpy.props.BoolProperty(name="Load Transform Map Without Applying", default=True) # type: ignore

    def set_data(self, value):
        if isinstance(value, Matrix):
            value = [list(row) for row in value]
        elif isinstance(value, Vector):
            value = list(value)
        self["create_transform_foot_z_location"] = json.dumps(value)

    def get_data(self):
        if self.get("create_transform_foot_z_location"):
            data = json.loads(self["create_transform_foot_z_location"])
            if isinstance(data, list):
                if len(data) == 4 and all(isinstance(row, list) and len(row) == 4 for row in data):
                    return Matrix(data)
                elif len(data) == 3 and all(isinstance(x, (int, float)) for x in data):
                    return Vector(data)
        else:
            return None
        return data
    
class BoneTransformPanel(bpy.types.Panel):
    bl_label = "Armature and Bone Selector"
    bl_idname = "OBJECT_PT_armature_bone_selector"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Bone Transform Mapping"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        create_transform_props = scene.create_transform_props
        
        
        row = layout.row()
        row.prop(scene, "selected_bone_mapping")
        row.prop(create_transform_props, "transform_map_name_input")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(scene, "source_armature", text="Source Armature")
        sub_row.prop(scene, "target_armature", text="Target Armature")
        
        row = layout.row()
        row.prop(create_transform_props, "transform_target_is_epic_skeleton", text="Transform Target is Epic Skeleton")

        row = layout.row()
        row.operator("object.assign_color_to_armatures", text="Assign Color to armatures")
        
        row = layout.row()
        row.prop(scene, "selected_source_bone", text="Source Bone")
        row.operator("object.select_source_bone_from_viewport", text="Select Source Bone")
        
        row = layout.row()
        row.prop(scene, "selected_target_bone", text="Target Bone")
        row.operator("object.select_target_bone_from_viewport", text="Select Target Bone")
        
        if scene.transform_type == "copy_bone_between_armatures":
            row = layout.row()
            row.prop(create_transform_props, "new_bone_name", text="Name for the copied bone")

        if scene.transform_type == "match_edit_bone_chain_scale":
            row = layout.row()
            row.prop(scene, "source_bone_chain", text="Source Bone Chain")
            row.operator("object.select_source_bone_chain", text="Select Source Bone Chain")        
            row = layout.row()
            row.prop(scene, "target_bone_chain", text="Target Bone Chain")
            row.operator("object.select_target_bone_chain", text="Select Target Bone Chain")
        
        row = layout.row()
        row.operator("object.save_foot_z_location", text="Save Current Foot Z location")

        if scene.transform_type == "rotate_bone" or scene.transform_type == "scale_bone":
            row = layout.row()
            row.prop(scene, "axis", text="Axis")
            row.prop(scene, "value", text="Transform Value")
        
        if scene.transform_type == "rotate_bone":
            layout.prop(scene, "mirror", text="Mirror")

        layout.prop(scene, "transform_type", text='Transform Type')

        layout.operator("object.add_transform", text="Add Transform")
        
        layout.template_list("OBJECT_UL_transform_list", "", scene, "transform_list", scene, "transform_list_index")
        
        row = layout.row()
        row.operator("object.export_bone_transform", text="Export JSON")
        row.operator("object.save_bone_transform", text="Save Bove Transforms")
        row = layout.row()
        row.prop(create_transform_props,"apply_on_load", text="Apply Transforms on Load")
        row.operator("object.load_bone_transform", text="Load Bone Transforms")

class Transform_item(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name") # type: ignore
    description: bpy.props.StringProperty(name="Description") # type: ignore
    transform_type: bpy.props.StringProperty(name="Transform Type", default='rotate_bone') # type: ignore
    revert_data: bpy.props.StringProperty(name="Revert Data", default="{}") # type: ignore
    transform_details: bpy.props.StringProperty(name="Transform Details", default="{}") # type: ignore


    def set_data(self, data, data_type="revert_data"):
        debug_print(f"CreateTransformMap-TransformItem-SetData: data to set: {data_type} -- data: {data}")
        if not data:
            self[data_type] = {}
            return
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
        if not self.get(data_type):
            return {}
        data = json.loads(self[data_type])
        if not data or not data.items():
            return self.revert_data
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


def add_transform(context, target_bone_name, source_bone_name, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator, target_chain=[], source_chain=[], new_bone_name="" ,apply_transform=True):
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

    foot_z_no_template = scene.create_transform_props.get_data()
    transform_target_is_epic_skeleton = scene.create_transform_props.transform_target_is_epic_skeleton
    new_transform = None
    debug_print(f"In CreateTransformMap -> AddTransform(Func): Apply Transform: {apply_transform}")
    if transform_type == 'rotate_bone':
        revert_data = None
        if(apply_transform):
            revert_data = rotate_bone(target_armature, target_bone_name, axis, transform_value, mirror) # calls the function and saves the return value, which can be used to revert the changes
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "axis":axis, "transform_value": transform_value, "mirror": mirror}, 'transform_details')
        new_transform.name = f"Rotate Bone: {target_bone_name} -> LOCAL '{axis}' - {transform_value} | {'MIRRORED' if mirror else ''}"
    elif transform_type == 'scale_bone':
        revert_data = None
        if(apply_transform):
            revert_data = scale_pose_bone(target_armature, target_bone_name, transform_value, axis)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "transform_value":transform_value, "axis": axis}, 'transform_details')            
        new_transform.name = f"Scale Bone: {target_bone_name} -> LOCAL '{axis}' - {transform_value}"
    elif transform_type == 'match_pose_bone_head_pos':
        foot_z_location = None if "foot" not in target_bone_name.lower() else (get_foot_z_location(target_armature, target_bone_name) if not foot_z_no_template else foot_z_no_template)
        revert_data = None
        if(apply_transform):
            revert_data = match_pose_bone_head_pos(target_armature, source_armature, target_bone_name, source_bone_name, foot_z_location)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name, "foot_z_location": foot_z_location}, 'transform_details')
        new_transform.name = f"Match POSE Bone Head Position: {target_bone_name} -> {source_bone_name}"
    elif transform_type == 'match_pose_bone_orientation':
        unreal_right = False if target_armature_indicator == "S" else is_flipped_unreal_bone(target_bone_name, transform_target_is_epic_skeleton)
        revert_data = None
        if(apply_transform):
            revert_data = match_pose_bone_orientation(target_armature, source_armature, target_bone_name, source_bone_name, unreal_right)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name, "unreal_right": unreal_right}, 'transform_details')
        new_transform.name = f"Match POSE Bone Orientation: {target_bone_name} -> {source_bone_name}"
    elif transform_type == 'chain_pose_bone_position':
        revert_data = None
        if(apply_transform):
            revert_data = chain_pose_bone_position(target_armature, target_bone_name, source_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name}, 'transform_details')
        new_transform.name = f"Chain POSE Bone: {target_bone_name} -> {source_bone_name}"
    elif transform_type == 'match_edit_bone_pos':
        revert_data = None
        if(apply_transform):
            revert_data = match_edit_bone_pos(target_armature, source_armature, target_bone_name, source_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name}, 'transform_details')
        new_transform.name = f"Match EDIT Bone Position {target_bone_name} -> {source_bone_name}"
    elif transform_type == 'match_edit_bone_z_location':
        revert_data = None
        if(apply_transform):
            revert_data = match_edit_bone_z_location(target_armature, source_armature, target_bone_name, source_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name":source_bone_name}, 'transform_details')
        new_transform.name = f"Match EDIT Bone Z: {target_bone_name} -> {source_bone_name}"
    elif transform_type == 'match_edit_bone_chain_scale':
        revert_data = None
        if(apply_transform):
            revert_data = match_edit_bone_chain_scale(target_armature, source_armature, target_chain, source_chain)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_chain": target_chain, "source_chain": source_chain}, 'transform_details')
        new_transform.name = f"Match EDIT Bone Chain Scale: {target_chain[0]} - {target_chain[-1]}"
    elif transform_type == 'copy_bone_between_armatures':
        revert_data = None
        if(apply_transform):
            revert_data = copy_bone_between_armatures(target_armature, source_armature, source_bone_name, target_bone_name, new_bone_name)
        new_transform = scene.transform_list.add()
        new_transform.transform_type = transform_type
        new_transform.set_data(revert_data, 'revert_data')
        new_transform.set_data({"target_armature_indicator": target_armature_indicator, "source_armature_indicator": source_armature_indicator, "transform_type":transform_type, "target_bone_name": target_bone_name, "source_bone_name": source_bone_name, "new_bone_name": new_bone_name}, 'transform_details')
        new_transform.name = f"Copy Bone: {source_bone_name} -> {new_bone_name} -> Parent: {target_bone_name}"
    else:
        raise ValueError(f"In CreateTransformMap-AddTransform: Invalid transform type: {transform_type}")
    return new_transform if new_transform else None

class OBJECT_OT_save_foot_z_location(bpy.types.Operator):
    bl_idname = "object.save_foot_z_location"
    bl_label = "Save Current Foot Z Location"

    def execute(self, context):
        scene = context.scene
        create_transform_props = scene.create_transform_props
        target_armature = scene.target_armature
        foot_bone_name = scene.selected_target_bone

        try:
            validate(
                [target_armature, foot_bone_name],
                ["ARMATURE", "str"],
                stack_location="CreateTransformMap-SaveFootZLocation",
                input_identifier_strings=["target_armature", "foot_bone_name"],
            )
            create_transform_props.set_data(get_foot_z_location(target_armature, foot_bone_name))
            return {'FINISHED'}
        except ValueError:
            self.report({'WARNING'}, "No selected target armature, or foot bone found. Make sure to select them before trying to save the foot z location")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SaveFootZLocation-Execute: Failed to save foot z location. Error: {e}")
            return {'CANCELLED'}

class OBJECT_OT_add_transform(bpy.types.Operator):
    bl_idname = "object.add_transform"
    bl_label = "Add Transform"

    def execute(self, context):
        scene = context.scene
        create_transform_props = scene.create_transform_props

        target_bone_name = scene.selected_target_bone
        source_bone_name = scene.selected_source_bone
        target_chain = [item.name for item in scene.target_bone_chain]
        source_chain = [item.name for item in scene.source_bone_chain]
        target_armature_indicator = scene.target_armature_indicator
        source_armature_indicator = scene.source_armature_indicator
        new_bone_name = create_transform_props.new_bone_name
        axis = scene.axis
        transform_value = scene.value
        mirror = scene.mirror

        transform_type = scene.transform_type
        try:
            new_transform = add_transform(context, target_bone_name, source_bone_name, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator, target_chain, source_chain, new_bone_name=new_bone_name)
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-AddTransform-Execute: Failed to add transform. Error: {e}")
            return {'CANCELLED'}
        if not new_transform:
            self.report({'ERROR'}, "In CreateTransformMap-AddTransform-Execute: Failed to add transform. No transform item was created.")
            return {'CANCELLED'}
        self.report({'INFO'}, f"{new_transform.name} added to the list")
        return {'FINISHED'}

class OBJECT_UL_transform_list(bpy.types.UIList):
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

    index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        scene = context.scene
        revert_data = scene.transform_list[self.index].get_data("revert_data")
        if not revert_data:
            scene.transform_list.remove(self.index)
            debug_print(f"In CreateTransformMap -> RemoveTransform: No Revert Data, removing list item without transforms.")
            return {'FINISHED'}
        try:
            if scene.transform_list[self.index].transform_type == "rotate_bone":
                rotate_bone(
                    revert_data['armature'], 
                    revert_data['bone_name'], 
                    revert_data['axis'], 
                    revert_data['degrees'], 
                    revert_data['mirror']
                )
                debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted rotation for bone: {revert_data['bone_name']}")
            elif scene.transform_list[self.index].transform_type == "scale_bone":
                scale_pose_bone(
                    revert_data['armature'], 
                    revert_data['bone_name'], 
                    revert_data['scale_value'], 
                    revert_data['axis'], 
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
            elif scene.transform_list[self.index].transform_type == "match_edit_bone_z_location":
                move_edit_bone(
                    revert_data['target_armature'], 
                    revert_data['target_bone_name'], 
                    revert_data['offset']
                )
                debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted edit bone position for bone: {revert_data['target_bone_name']}")
            elif scene.transform_list[self.index].transform_type == "match_edit_bone_chain_scale":
                scale_edit_bone_chain(
                    revert_data['target_armature'], 
                    revert_data['target_chain'], 
                    revert_data['scale_factor']
                )
                debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted edit bone chain scale for the bone chain: {revert_data['target_chain']}")
            elif scene.transform_list[self.index].transform_type == "copy_bone_between_armatures":
                delete_edit_bone(
                    revert_data['target_armature'], 
                    revert_data['new_bone_name'], 
                )
                debug_print(f"CreateBoneTransformMap-RemoveTransform: Reverted Copy Bone, by deleting the copied bone: {revert_data['new_bone_name']}")
            else:
                print('TBD')
            scene.transform_list.remove(self.index)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-RemoveTransform-Execute: Failed to revert transform. Error: {e}")
            return {'CANCELLED'}


class OBJECT_OT_select_source_bone(bpy.types.Operator):
    bl_idname = "object.select_source_bone_from_viewport"
    bl_label = "Select Source Bone From Viewport"
    
    def execute(self, context):
        try:
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
                        if context.scene.transform_type == "copy_bone_between_armatures":
                            context.scene.create_transform_props.new_bone_name = context.scene.selected_source_bone
                            debug_print(f"CreateTransformMap-SelectingSourceBone: Set source bone name as default value for Copied Bone Name: {context.scene.create_transform_props.new_bone_name}")
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
                    return {'FINISHED'}
            self.report({'WARNING'}, f"Something went wrong when trying to select source bone. Make sure you are in pose mode and selecting a bone")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectSourceBone-Execute: Failed to select source bone. Error: {e}")
            return {'CANCELLED'}

class OBJECT_OT_select_target_bone(bpy.types.Operator):
    bl_idname = "object.select_target_bone_from_viewport"
    bl_label = "Select Target Bone From Viewport"
    
    def execute(self, context):
        try:
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
                        return {'FINISHED'}
                    return {'FINISHED'}
            self.report({'WARNING'}, f"Something went wrong when trying to select target bone. Make sure you are in pose mode and selecting a bone")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectTargetBone-Execute: Failed to select target bone. Error: {e}")
            return {'CANCELLED'}

class OBJECT_OT_select_source_bone_chain(bpy.types.Operator):
    bl_idname = "object.select_source_bone_chain"
    bl_label = "Select Source Bone Chain"
    bl_description = "Select a chain of bones in the viewport and set them as the Source Bone Chain"

    def execute(self, context):
        try:
            selected_object = context.view_layer.objects.active
            if selected_object and selected_object.type == 'ARMATURE':
                if context.active_object.mode == 'POSE':
                    selected_bones = context.selected_pose_bones

                    if selected_bones:
                        context.scene.source_bone_chain.clear()
                        
                        for bone in selected_bones:
                            item = context.scene.source_bone_chain.add()
                            item.name = bone.name
                        context.scene.source_armature_indicator = 'S' if selected_object.name == context.scene.source_armature.name else 'T'
                        self.report({'INFO'}, f"Selected source bone chain: {[bone.name for bone in context.scene.source_bone_chain]}")
                        return {'FINISHED'}
                    else:
                        self.report({'WARNING'}, "No bones selected.")
                        return {'CANCELLED'}
                else:
                    self.report({'WARNING'}, "Must be in Pose mode to select bones.")
                    return {'CANCELLED'}
            else:
                self.report({'WARNING'}, "Active object must be an armature.")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectSourceBoneChain-Execute: Failed to select source bone chain. Error: {e}")
            return {'CANCELLED'}

class OBJECT_OT_select_target_bone_chain(bpy.types.Operator):
    bl_idname = "object.select_target_bone_chain"
    bl_label = "Select Target Bone Chain"
    bl_description = "Select a chain of bones in the viewport and set them as the Target Bone Chain"

    def execute(self, context):
        try:
            selected_object = context.view_layer.objects.active
            if selected_object and selected_object.type == 'ARMATURE':
                if context.active_object.mode == 'POSE':
                    selected_bones = context.selected_pose_bones

                    if selected_bones:
                        context.scene.target_bone_chain.clear()
                        
                        for bone in selected_bones:
                            item = context.scene.target_bone_chain.add()
                            item.name = bone.name
                        context.scene.target_armature_indicator = 'T' if selected_object.name == context.scene.target_armature.name else 'S'
                        self.report({'INFO'}, f"Selected target bone chain: {[bone.name for bone in context.scene.target_bone_chain]}")
                        return {'FINISHED'}
                    else:
                        self.report({'WARNING'}, "No bones selected.")
                        return {'CANCELLED'}
                else:
                    self.report({'WARNING'}, "Must be in Pose mode to select bones.")
                    return {'CANCELLED'}
            else:
                self.report({'WARNING'}, "Active object must be an armature.")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectTargetBoneChain-Execute: Failed to select target bone chain. Error: {e}")
            return {'CANCELLED'}

def update_source_armature(self, context):
    armature = bpy.context.scene.source_armature
    debug_print('CreateTransformMap-UpdateSourceArmature: updated source armature')
    if armature:
        try:
            validate(
                [armature],
                ['ARMATURE'],
                stack_location="CreateTransformMap-UpdateSourceArmature",
                input_identifier_strings=["source_armature"],
            )
        except ValueError:
            bpy.context.scene.source_armature = None

def update_target_armature(self, context):
    debug_print("CreateTransformMap-UpdateSourceArmature:updated source armature")
    armature = bpy.context.scene.target_armature
    if armature:
        try:
            validate(
                [armature],
                ['ARMATURE'],
                stack_location="CreateTransformMap-UpdateTargetArmature",
                input_identifier_strings=["target_armature"],
            )
        except ValueError:
            bpy.context.scene.target_armature = None

def get_bone_mapping_options():
    json_file_path = get_current_json_data_file_path("bone_mappings")
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
        ) # type: ignore

    def execute(self, context):
        try:
            debug_print('CreateTransformMap-SelectBoneMapping-Execute: Executing select_bone_mapping')
            selected_mapping_name = context.scene.selected_bone_mapping
            debug_print(f"CreateTransformMap-SelectBoneMapping-Execute: Selected bone mapping name: {selected_mapping_name}")

            json_file_path = get_current_json_data_file_path("bone_mappings")
            if not os.path.exists(json_file_path):
                self.report({'WARNING'}, "Bone mapping data file was not found")
                return {'CANCELLED'}

            with open(json_file_path, 'r') as json_file:
                data = json.load(json_file)
                mapping_contents = data.get(selected_mapping_name) if data else None
                if not mapping_contents:
                    self.report({'WARNING'}, "Selected bone mapping is invalid or empty")
                    return {'CANCELLED'}

                debug_print(f"CreateTransformMap-SelectBoneMapping-Execute: selected_bone_mapping_contents: {mapping_contents}")
                set_bone_mapping_contents(context.scene, mapping_contents)

            self.report({'INFO'}, f"Selected bone mapping: {selected_mapping_name}")
            return {'FINISHED'}
        except json.JSONDecodeError as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectBoneMapping-Execute: Failed to load bone mapping data. Error: {e}")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SelectBoneMapping-Execute: Failed to select bone mapping. Error: {e}")
            return {'CANCELLED'}


class OBJECT_OT_assign_color_to_armatures(bpy.types.Operator):
    bl_idname = "object.assign_color_to_armatures"
    bl_label = "Refresh Bone Mapping"

    def execute(self, context):
        armature1 = context.scene.source_armature
        armature2 = context.scene.target_armature
        try:
            validate(
                [armature1, armature2],
                ["ARMATURE", "ARMATURE"],
                stack_location="CreateTransformMap-AssignColorToArmatures",
                input_identifier_strings=["source_armature", "target_armature"],
            )
            debug_print('CreateTransformMap-AssignColorToArmatures: Assigning colors')
            assign_bone_color_to_armature(armature1, (1,95,100))
            assign_bone_color_to_armature(armature2, (115,30,0))
            return {'FINISHED'}
        except ValueError:
            self.report({'WARNING'}, f"Make sure you have both target and source armature selected before assigning color to armatures.")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-AssignColorToArmatures-Execute: Couldn't assign color to armatures. Error: {e}")
            return {'CANCELLED'}


def create_bone_transform_json(scene, mode = "export"):
    bone_transform_list = []
    bone_transform_json = {}

    for transform in scene.transform_list:
        bone_transform_list.append(transform.get_data('transform_details'))
    bone_transform_json["transforms"] = bone_transform_list
    
    if mode == "save":
        return bone_transform_list
    else:
        return bone_transform_json


class OBJECT_OT_export_bone_transform(bpy.types.Operator):
    bl_idname = "object.export_bone_transform"
    bl_label = "Export Bone Transforms"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="bone_transforms.json") # type: ignore

    def execute(self, context):
        scene = context.scene
        bone_transform_list = create_bone_transform_json(scene, mode = "export")
        
        file_path = self.filepath
        
        if not file_path.endswith(".json"):
            file_path += ".json"
        
        try:
            with open(file_path, 'w') as json_file:
                json.dump(bone_transform_list, json_file, indent=4)
            self.report({'INFO'}, f"Bone transform list exported to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-ExportBoneTransform-Execute: Failed to export bone transform list. Error: {e}")
            return {"CANCELLED"}
        return {'FINISHED'}

    def invoke(self, context, event):
        file_name = f"{context.scene.create_transform_props.transform_map_name_input}_transforms.json" or "bone_transforms.json"
        self.filepath = bpy.path.abspath(f"//{file_name}")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OBJECT_OT_save_bone_transform(bpy.types.Operator):
    bl_idname = "object.save_bone_transform"
    bl_label = "Save Bone Mapping"

    def execute(self, context):
        try:
            scene = context.scene
            bone_transforms_json = create_bone_transform_json(scene, mode = "save")
            property_name = context.scene.create_transform_props.transform_map_name_input or "default_property"

            validate(
                [property_name, bone_transforms_json],
                ["str", "list"],
                stack_location="CreateTransformMap-SaveBoneTransform",
                input_identifier_strings=["property_name", "bone_transforms_json"],
            )

            result = save_to_persistent_data_store_json_property("bone_transforms", property_name, bone_transforms_json)
            if result == {'CANCELLED'}:
                raise RuntimeError("Failed to persist bone transforms json data")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-SaveBoneTransform-Execute: Failed to save bone transforms. Error: {e}")
            return {'CANCELLED'}


class OBJECT_OT_load_bone_transform(bpy.types.Operator):
    bl_idname = "object.load_bone_transform"
    bl_label = "Load Bone Transforms"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH") # type: ignore

    def execute(self, context):
        scene = context.scene
        create_transform_props = scene.create_transform_props
        apply_transform =  create_transform_props.apply_on_load
        try:
            with open(self.filepath, 'r') as json_file:
                json_object = json.load(json_file)
                bone_transforms = json_object["transforms"]

            scene.transform_list.clear()

            create_transform_props.tranform_map_name_input = bpy.path.basename(self.filepath) if not create_transform_props.tranform_map_name_input else create_transform_props.tranform_map_name_input

            debug_print(f"CreateTransformMap-LoadBoneTransformMap: Loading all Transforms. Apply on Load: {apply_transform}")
            for transform_data in bone_transforms:
                target_bone_name = transform_data.get("target_bone_name")
                source_bone_name = transform_data.get("source_bone_name")
                target_chain = transform_data.get("target_chain")
                source_chain = transform_data.get("source_chain")
                axis = transform_data.get("axis")
                transform_value = transform_data.get("transform_value")
                mirror = transform_data.get("mirror")
                transform_type = transform_data.get("transform_type")
                target_armature_indicator = transform_data.get("target_armature_indicator")
                source_armature_indicator = transform_data.get("source_armature_indicator")
                new_bone_name = transform_data.get("new_bone_name")
                add_transform(context, target_bone_name, source_bone_name, axis, transform_value, mirror, transform_type, target_armature_indicator, source_armature_indicator, target_chain, source_chain, new_bone_name=new_bone_name, apply_transform=apply_transform)
            self.report({'INFO'}, f"Bone transform loaded from {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTransformMap-LoadBoneTransform-Execute: Failed to load bone transforms. Error: {e}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(CreateTransformProperties)
    bpy.types.Scene.create_transform_props = bpy.props.PointerProperty(type=CreateTransformProperties)

    bpy.utils.register_class(BoneTransformPanel)
    bpy.utils.register_class(OBJECT_OT_assign_color_to_armatures)
    bpy.utils.register_class(OBJECT_OT_select_source_bone)
    bpy.utils.register_class(OBJECT_OT_select_target_bone)
    bpy.utils.register_class(OBJECT_OT_select_source_bone_chain)
    bpy.utils.register_class(OBJECT_OT_select_target_bone_chain)
    bpy.utils.register_class(Transform_item)
    bpy.utils.register_class(OBJECT_OT_add_transform)
    bpy.utils.register_class(OBJECT_OT_remove_transform)
    bpy.utils.register_class(OBJECT_UL_transform_list)
    bpy.utils.register_class(OBJECT_OT_select_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_export_bone_transform)
    bpy.utils.register_class(OBJECT_OT_save_bone_transform)
    bpy.utils.register_class(OBJECT_OT_load_bone_transform)
    bpy.utils.register_class(OBJECT_OT_save_foot_z_location)


    bpy.types.Scene.selected_source_bone = bpy.props.StringProperty(name="Selected Source Bone")
    bpy.types.Scene.selected_target_bone = bpy.props.StringProperty(name="Selected Target Bone")
    bpy.types.Scene.source_bone_chain = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.target_bone_chain = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    
    bpy.types.Scene.source_armature_indicator = bpy.props.StringProperty(name="Source Armature Indicator for Transform")
    bpy.types.Scene.target_armature_indicator = bpy.props.StringProperty(name="Target Armature Indicator for Transform")

    bpy.types.Scene.mirror = bpy.props.BoolProperty(name="Mirror", default=False)
    bpy.types.Scene.value = bpy.props.FloatProperty(name="Transform Value", default=0.0)
    


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

    bpy.types.Scene.axis = bpy.props.EnumProperty(
        name="Axis",
        items=[
            ('X', "X", ""),
            ('Y', "Y", ""),
            ('Z', "Z", ""),
            ('NONE', "None", ""), # this is for scaling. not selecting an axis means it will scale on all of them the same amount
        ],
        default='X',
    )


    bpy.types.Scene.transform_type = bpy.props.EnumProperty(
        name='Transform Type',
        items=[
            ('match_pose_bone_head_pos', "Match POSE Bone Head Position", "Match Pose Bone Head Position"),
            ('match_pose_bone_orientation', "Match POSE Bone Orientation", "Match Pose Bone Orientation"),
            ('chain_pose_bone_position', "Chain POSE Bone", "Chain Pose Bone"),
            ('scale_bone', "Scale POSE Bone", "Scale Bone"),
            ('rotate_bone', "Rotate POSE Bone", "Rotate Bone"),
            ('match_edit_bone_pos', "Match EDIT Bone Head Position", "Match Edit Bone Head Position"),
            ('match_edit_bone_z_location', "Match EDIT Bone Z Position", "Match Edit Bone Z Position"),
            ('match_edit_bone_chain_scale', "Match EDIT Bone Chain Scale", "Match Edit Bone Chain Scale"),
            ('copy_bone_between_armatures', "Copy Bone Between Armatures", "Copy Bone Between Armatures")
        ],
        default='rotate_bone'
    )


    

    bpy.types.Scene.transform_list = bpy.props.CollectionProperty(type=Transform_item)
    bpy.types.Scene.transform_list_index = bpy.props.IntProperty()

def unregister():
    bpy.utils.unregister_class(CreateTransformProperties)
    bpy.utils.unregister_class(BoneTransformPanel)
    bpy.utils.unregister_class(OBJECT_OT_assign_color_to_armatures)
    bpy.utils.unregister_class(OBJECT_OT_select_source_bone)
    bpy.utils.unregister_class(OBJECT_OT_select_target_bone)
    bpy.utils.unregister_class(OBJECT_OT_select_source_bone_chain)
    bpy.utils.unregister_class(OBJECT_OT_select_target_bone_chain)
    bpy.utils.unregister_class(Transform_item)
    bpy.utils.unregister_class(OBJECT_OT_add_transform)
    bpy.utils.unregister_class(OBJECT_OT_remove_transform)
    bpy.utils.unregister_class(OBJECT_UL_transform_list)
    bpy.utils.unregister_class(OBJECT_OT_select_bone_mapping)
    bpy.utils.unregister_class(OBJECT_OT_export_bone_transform)
    bpy.utils.unregister_class(OBJECT_OT_save_bone_transform)
    bpy.utils.unregister_class(OBJECT_OT_load_bone_transform)
    bpy.utils.unregister_class(OBJECT_OT_save_foot_z_location)
    
    del bpy.types.Scene.create_transform_props
    del bpy.types.Scene.selected_source_bone
    del bpy.types.Scene.selected_target_bone
    del bpy.types.Scene.target_bone_chain
    del bpy.types.Scene.source_bone_chain
    del bpy.types.Scene.source_armature_indicator
    del bpy.types.Scene.target_armature_indicator
    del bpy.types.Scene.mirror
    del bpy.types.Scene.value
    del bpy.types.Scene.selected_bone_mapping
    bpy.types.Scene.bone_mapping_contents

    del bpy.types.Scene.axis
    del bpy.types.Scene.transform_type
    del bpy.types.Scene.transform_list
    del bpy.types.Scene.transform_list_index

if __name__ == "__main__":
    register()
