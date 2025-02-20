import bpy # type: ignore
import os
import json

from .utils import debug_print, save_to_persistent_data_store_json_property, get_current_json_data_file_path

addon_dir = os.path.dirname(os.path.realpath(__file__))
utils_dir = os.path.join(addon_dir, "utils")
data_dir = os.path.join(utils_dir, "data")

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

def get_transform_map_options():
    json_file_path = get_current_json_data_file_path("bone_transforms")
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as json_file:
            try:
                data = json.load(json_file)
                return list(data.keys())
            except json.JSONDecodeError:
                return []
    return []


def bone_mapping_t_update_callback(self, context):
    bpy.ops.object.select_t_bone_mapping()

def transform_map_t_update_callback(self, context):
    bpy.ops.object.select_t_transform_map()

def create_template_json(props):
    return props.get_data()

class OBJECT_PT_create_template_panel(bpy.types.Panel):
    bl_label = "Create SkeleSwap Template"
    bl_idname = "OBJECT_PT_create_template_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create SkeleSwap Template"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        create_template_properties = scene.create_template_properties
        
        row = layout.row()
        row.label(text="Template Name")
        row.prop(create_template_properties, "template_name")


        row = layout.row(align=True)
        row.prop(create_template_properties, "selected_bone_mapping")  
        row = layout.row(align=True)
        row.prop(create_template_properties, "selected_transform_map")

        row = layout.row(align=True)
        sub_row = row.row(align=True)
        sub_row.prop(create_template_properties, "target_is_epic_skeleton")
        sub_row.prop(create_template_properties, "has_facial_animations")
        if create_template_properties.has_facial_animations:
            sub_row.prop(create_template_properties, "has_separate_face_rig")

        row = layout.row()
        row.label(text="Save Template")
        row.operator("object.save_template", text="Save Template")

class OBJECT_OT_select_T_bone_mapping(bpy.types.Operator):
    bl_idname = "object.select_t_bone_mapping"
    bl_label = "Select Bone Mapping"

    selected_bone_mapping: bpy.props.EnumProperty(
        name="Bone Mapping",
        items=lambda self, context: [(option, option, "") for option in get_bone_mapping_options()],
    ) # type: ignore

    def execute(self, context):
        create_template_properties = context.scene.create_template_properties
        selected_mapping_name = create_template_properties.selected_bone_mapping
        debug_print(f"CreateTemplate: Selected bone mapping: {selected_mapping_name}")
        self.report({'INFO'}, f"CreateTemplate: Selected bone mapping: {selected_mapping_name}")
        return {'FINISHED'}

class OBJECT_OT_select_T_transform_map(bpy.types.Operator):
    bl_idname = "object.select_t_transform_map"
    bl_label = "Select Transform Map"

    selected_transform_map: bpy.props.EnumProperty(
        name="Transform Map",
        items=lambda self, context: [(option, option, "") for option in get_transform_map_options()],
    ) # type: ignore

    def execute(self, context):
        create_template_properties = context.scene.create_template_properties
        selected_transform_map_name = create_template_properties.selected_transform_map
        debug_print(f"CreateTemplate: Selected Transform Map: {selected_transform_map_name}")
        self.report({'INFO'}, f"CreateTemplate: Selected Transform Map: {selected_transform_map_name}")
        return {'FINISHED'}


class OBJECT_OT_save_template(bpy.types.Operator):
    bl_idname = "object.save_template"
    bl_label = "Save Template"
    def execute(self, context):
        scene = context.scene
        create_template_properties = scene.create_template_properties
        property_name = create_template_properties.template_name or "My Template"
        template = create_template_json(create_template_properties)

        try:
            debug_print(f"CreateTemplate-SaveTemplate: Attempting to save new temolate, {template}, in the template json, under property: {property_name}")
            save_to_persistent_data_store_json_property("template_configs", property_name, template)       
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save bone mapping: {e}")
        
        return {'FINISHED'}



class CreateTemplateProperties(bpy.types.PropertyGroup):
    template_name: bpy.props.StringProperty(name="Template Name", default="My Template") # type: ignore
    target_is_epic_skeleton: bpy.props.BoolProperty(name="Target is Epic Skeleton", default=False) # type: ignore
    has_facial_animations: bpy.props.BoolProperty(name="Has Facial Animations", default=False) # type: ignore
    has_separate_face_rig: bpy.props.BoolProperty(name="Is Face Rig a Seperate Armature", default=False) # type: ignore

    selected_bone_mapping: bpy.props.EnumProperty(
        name="Bone Mapping",
        items=lambda self, context: [(option, option, "") for option in get_bone_mapping_options()],
        update=bone_mapping_t_update_callback
    ) # type: ignore
    selected_transform_map: bpy.props.EnumProperty(
        name="Transform Map",
        items=lambda self, context: [(option, option, "") for option in get_transform_map_options()],
        update=transform_map_t_update_callback
    ) # type: ignore
    
    def get_enum_value(self, prop_name):
        prop = getattr(self, prop_name)
        for item in self.bl_rna.properties[prop_name].enum_items:
            if item.value == prop:
                return item.name
        return ""

    def get_data(self):
        return {
            "option_name": self.template_name if self.template_name else None,
            "bone_mapping": self.selected_bone_mapping,
            "transform_map": self.selected_transform_map,
            "target_is_epic_skeleton": bool(self.target_is_epic_skeleton),
            "has_facial_animations": bool(self.has_facial_animations),
            "has_separate_face_rig": bool(self.has_separate_face_rig)
        }

def register():
    bpy.utils.register_class(CreateTemplateProperties)
    bpy.types.Scene.create_template_properties = bpy.props.PointerProperty(type=CreateTemplateProperties)

    bpy.utils.register_class(OBJECT_PT_create_template_panel)
    bpy.utils.register_class(OBJECT_OT_select_T_bone_mapping)
    bpy.utils.register_class(OBJECT_OT_select_T_transform_map)
    bpy.utils.register_class(OBJECT_OT_save_template)





def unregister():
    bpy.utils.unregister_class(CreateTemplateProperties)
    del bpy.types.Scene.create_template_properties

    bpy.utils.unregister_class(OBJECT_PT_create_template_panel)
    bpy.utils.unregister_class(OBJECT_OT_select_T_bone_mapping)
    bpy.utils.unregister_class(OBJECT_OT_select_T_transform_map)
    bpy.utils.unregister_class(OBJECT_OT_save_template)


if __name__ == "__main__":
    register()