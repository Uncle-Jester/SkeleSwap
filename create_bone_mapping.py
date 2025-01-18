import bpy # type: ignore
import json
import os

from .utils.bone_mapping_utils import map_bone_lists

def update_source_armature(self, context):
    armature = bpy.context.scene.source_armature
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.source_armature = None

def update_target_armature(self, context):
    armature = bpy.context.scene.target_armature
    if armature and armature.type != 'ARMATURE':
        bpy.context.scene.target_armature = None

def create_bone_mapping_json(scene):
    bone_mapping = {}
    for pair_item in scene.bone_pair_list:
        bone_mapping[pair_item.target_bone_name] = pair_item.source_bone_name
    return bone_mapping


class OBJECT_PT_bone_mapping_panel(bpy.types.Panel):
    bl_label = "Bone Mapping Panel"
    bl_idname = "OBJECT_PT_bone_mapping_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create Bone Mapping"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.label(text="Bone Map Name")
        row.prop(scene, "input_text")

        row = layout.row()
        row.prop(scene, "source_armature", text="Source Armature")
        
        row = layout.row()
        row.prop(scene, "target_armature", text="Target Armature")


        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.operator("object.prefill_target_bones", text="Prefill Target Armature Bones")
        sub_row.operator("object.auto_map_bones", text="Auto Map Bone Names")

        row = layout.row()
        layout.operator("object.add_bone_pair", text="Add Bone Pair")
        
        layout.template_list("OBJECT_UL_bone_pair_list", "", scene, "bone_pair_list", scene, "bone_pair_list_index")
        
        row = layout.row()
        row.operator("object.export_bone_mapping", text="Export JSON")
        row.operator("object.save_bone_mapping", text="Save Bove Map")
        row.operator("object.load_bone_mapping", text="Load Bone Mapping")


class BonePairItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name") # type: ignore
    description: bpy.props.StringProperty(name="Description") # type: ignore
    target_bone_name: bpy.props.StringProperty(name="Target Bone") # type: ignore
    source_bone_name: bpy.props.StringProperty(name="Source Bone") # type: ignore


class OBJECT_OT_add_bone_pair(bpy.types.Operator):
    bl_idname = "object.add_bone_pair"
    bl_label = "Add Transform"

    def execute(self, context):
        scene = context.scene

        new_item = scene.bone_pair_list.add()
        new_item.target_bone_name = ""
        new_item.source_bone_name = ""
        return {'FINISHED'}

class OBJECT_UL_bone_pair_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = context.scene
        armature_target = scene.target_armature
        armature_source = scene.source_armature
        
        if armature_target and armature_source:
            row = layout.row(align=True)
            sub_row = row.row(align=True)
            sub_row.prop_search(item, "target_bone_name", armature_target.data, "bones", text="")
            sub_row.operator("object.set_target_bone", text="", icon='EYEDROPPER').index = index

            sub_row = row.row(align=True)
            sub_row.prop_search(item, "source_bone_name", armature_source.data, "bones", text="")
            sub_row.operator("object.set_source_bone", text="", icon='EYEDROPPER').index = index
            row.operator("object.remove_bone_pair_from_list", text="", icon='X', emboss=False).index = index


class OBJECT_OT_remove_bone_pair_from_list(bpy.types.Operator):
    bl_idname = "object.remove_bone_pair_from_list"
    bl_label = "Remove bone pair"
    index: bpy.props.IntProperty() # type: ignore

    def execute(self, context):
        scene = context.scene
        scene.bone_pair_list.remove(self.index)
        return {'FINISHED'}


class OBJECT_OT_set_target_bone(bpy.types.Operator):
    bl_idname = "object.set_target_bone"
    bl_label = "Set Target Bone"
    
    index: bpy.props.IntProperty() # type: ignore
    
    def execute(self, context):
        scene = context.scene
        selected_bone = context.active_pose_bone
        armature_target = scene.target_armature
        
        if selected_bone and selected_bone.id_data == armature_target:
            scene.bone_pair_list[self.index].target_bone_name = selected_bone.name
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Select a bone from the target armature")
            return {'CANCELLED'}

class OBJECT_OT_set_source_bone(bpy.types.Operator):
    bl_idname = "object.set_source_bone"
    bl_label = "Set Source Bone"
    
    index: bpy.props.IntProperty() # type: ignore
    
    def execute(self, context):
        scene = context.scene
        selected_bone = context.active_pose_bone
        armature_source = scene.source_armature
        
        if selected_bone and selected_bone.id_data == armature_source:
            scene.bone_pair_list[self.index].source_bone_name = selected_bone.name
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Select a bone from the source armature")
            return {'CANCELLED'}

class OBJECT_OT_prefill_target_bones(bpy.types.Operator):
    bl_idname = "object.prefill_target_bones"
    bl_label = "Prefill Target Bones"

    def execute(self, context):
        scene = context.scene
        armature_target = scene.target_armature

        if not armature_target or armature_target.type != 'ARMATURE':
            self.report({'WARNING'}, "Target Armature not selected or invalid")
            return {'CANCELLED'}

        bpy.context.view_layer.objects.active = armature_target
        if bpy.context.object.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        
        pose_bones = armature_target.pose.bones
        
        scene.bone_pair_list.clear()

        for bone in pose_bones:
            pair_item = scene.bone_pair_list.add()
            pair_item.target_bone_name = bone.name
            pair_item.source_bone_name = ""

        return {'FINISHED'}

class OBJECT_OT_auto_map_bones(bpy.types.Operator):
    bl_idname = "object.auto_map_bones"
    bl_label = "AutoMap Bones"

    def execute(self, context):
        scene = context.scene
        armature_target = scene.target_armature
        armature_source = scene.source_armature

        if not armature_target or armature_target.type != 'ARMATURE':
            self.report({'WARNING'}, "Target Armature not selected or invalid")
            return {'CANCELLED'}
        if not armature_source or armature_source.type != 'ARMATURE':
            self.report({'WARNING'}, "Source Armature not selected or invalid")
            return {'CANCELLED'}

        bpy.context.view_layer.objects.active = armature_target
        if bpy.context.object.mode != 'POSE':
            bpy.ops.object.mode_set(mode='POSE')
        
        target_pose_bones = [bone.name for bone in armature_target.pose.bones]
        source_pose_bones = [bone.name for bone in armature_source.pose.bones]
             
        target_bones_to_map = []
        
        if scene.bone_pair_list:
            for list_item in scene.bone_pair_list:
                if list_item.target_bone_name:
                    target_bones_to_map.append(list_item.target_bone_name)
        else:
            target_bones_to_map = target_pose_bones

        bone_map = map_bone_lists(target_bones_to_map, source_pose_bones)

        scene.bone_pair_list.clear()
        for target_bone, source_bone in bone_map.items():
            pair_item = scene.bone_pair_list.add()
            pair_item.target_bone_name = target_bone if target_bone is not None else ""
            pair_item.source_bone_name = source_bone if source_bone is not None else ""

        return {'FINISHED'}

class OBJECT_OT_export_bone_mapping(bpy.types.Operator):
    bl_idname = "object.export_bone_mapping"
    bl_label = "Export Bone Mapping"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="bone_mappings.json") # type: ignore

    def execute(self, context):
        scene = context.scene
        bone_mapping = create_bone_mapping_json(scene)
        
        file_path = self.filepath
        
        if not file_path.endswith(".json"):
            file_path += ".json"
        
        try:
            with open(file_path, 'w') as json_file:
                json.dump(bone_mapping, json_file, indent=4)
            self.report({'INFO'}, f"Bone mapping exported to {file_path}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to export bone mapping: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        file_name = f"{context.scene.input_text}.json" or "bone_mappings.json"
        self.filepath = bpy.path.abspath(f"//{file_name}")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class OBJECT_OT_save_bone_mapping(bpy.types.Operator):
    bl_idname = "object.save_bone_mapping"
    bl_label = "Save Bone Mapping"

    def execute(self, context):
        scene = context.scene
        bone_mapping = create_bone_mapping_json(scene)

        addon_dir = os.path.dirname(os.path.realpath(__file__))
        utils_dir = os.path.join(addon_dir, "utils")
        data_dir = os.path.join(utils_dir, "data")
        json_file_path = os.path.join(data_dir, "bone_mappings.json")
        property_name = context.scene.input_text or "default_property"

        try:
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r+') as json_file:
                    data = json.load(json_file)
                    data[property_name] = bone_mapping
                    json_file.seek(0)
                    json.dump(data, json_file, indent=4)
                    json_file.truncate()
            else:
                with open(json_file_path, 'w') as json_file:
                    data = {property_name: bone_mapping}
                    json.dump(data, json_file, indent=4)
            
            self.report({'INFO'}, f"Bone mapping saved to {json_file_path} under '{property_name}'")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save bone mapping: {e}")

        return {'FINISHED'}


class OBJECT_OT_load_bone_mapping(bpy.types.Operator):
    bl_idname = "object.load_bone_mapping"
    bl_label = "Load Bone Mapping"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH") # type: ignore

    def execute(self, context):
        scene = context.scene
        try:
            with open(self.filepath, 'r') as json_file:
                bone_mapping = json.load(json_file)

            context.scene.input_text = bpy.path.basename(self.filepath)

            scene.bone_pair_list.clear()

            for target_bone, source_bone in bone_mapping.items():
                pair_item = scene.bone_pair_list.add()
                pair_item.target_bone_name = target_bone
                pair_item.source_bone_name = source_bone

            self.report({'INFO'}, f"Bone mapping loaded from {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load bone mapping: {e}")

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



def register():
    bpy.utils.register_class(BonePairItem)
    bpy.utils.register_class(OBJECT_PT_bone_mapping_panel)
    bpy.utils.register_class(OBJECT_OT_load_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_add_bone_pair)
    bpy.utils.register_class(OBJECT_OT_remove_bone_pair_from_list)
    bpy.utils.register_class(OBJECT_UL_bone_pair_list)
    bpy.utils.register_class(OBJECT_OT_set_target_bone)
    bpy.utils.register_class(OBJECT_OT_set_source_bone)
    bpy.utils.register_class(OBJECT_OT_prefill_target_bones)
    bpy.utils.register_class(OBJECT_OT_auto_map_bones)
    bpy.utils.register_class(OBJECT_OT_export_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_save_bone_mapping)
    bpy.types.Scene.input_text = bpy.props.StringProperty(name="Bone Map Name")
    bpy.types.Scene.source_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_source_armature)
    bpy.types.Scene.target_armature = bpy.props.PointerProperty(type=bpy.types.Object, update=update_target_armature)
    bpy.types.Scene.bone_pair_list = bpy.props.CollectionProperty(type=BonePairItem)
    bpy.types.Scene.bone_pair_list_index = bpy.props.IntProperty()

def unregister():
    bpy.utils.unregister_class(BonePairItem)
    bpy.utils.unregister_class(OBJECT_PT_bone_mapping_panel)
    bpy.utils.unregister_class(OBJECT_OT_load_bone_mapping)
    bpy.utils.unregister_class(OBJECT_OT_add_bone_pair)
    bpy.utils.unregister_class(OBJECT_OT_remove_bone_pair_from_list)
    bpy.utils.unregister_class(OBJECT_UL_bone_pair_list)
    bpy.utils.register_class(OBJECT_OT_set_target_bone)
    bpy.utils.register_class(OBJECT_OT_set_source_bone)
    bpy.utils.register_class(OBJECT_OT_prefill_target_bones)
    bpy.utils.register_class(OBJECT_OT_auto_map_bones)
    bpy.utils.register_class(OBJECT_OT_export_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_save_bone_mapping)
    del bpy.types.Scene.input_text
    del bpy.types.Scene.source_armature
    del bpy.types.Scene.target_armature
    del bpy.types.Scene.bone_pair_list
    del bpy.types.Scene.bone_pair_list_index

if __name__ == "__main__":
    register()