import bpy # type: ignore
from .utils import debug_print, save_to_persistent_data_store_json_property, get_persistent_data_store_json_keys
from .utils.dev_utils import validate
_PANEL_SUPPORTS_BL_ORDER = hasattr(bpy.types.Panel, "bl_order")

def get_bone_mapping_options():
    return get_persistent_data_store_json_keys("bone_mappings")

def get_transform_map_options():
    return get_persistent_data_store_json_keys("bone_transforms")


def bone_mapping_t_update_callback(self, context):
    bpy.ops.object.select_t_bone_mapping()

def transform_map_t_update_callback(self, context):
    bpy.ops.object.select_t_transform_map()

def create_template_json(props):
    return props.get_data()

class CreateSkeleSwapTemplatePanel(bpy.types.Panel):
    bl_label = "SkeleSwap Template Creator"
    bl_idname = "OBJECT_PT_create_template_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "SkeleSwap"
    bl_options = {'DEFAULT_CLOSED'}
    if _PANEL_SUPPORTS_BL_ORDER:
        bl_order = 3

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        create_template_properties = scene.create_template_properties
        
        row = layout.row()
        row.label(text="Template Name")
        row.prop(create_template_properties, "template_name", text="")


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

class CreateSkeleSwapTemplateSelectTBoneMappingOperator(bpy.types.Operator):
    bl_idname = "object.select_t_bone_mapping"
    bl_label = "Select Bone Mapping"

    selected_bone_mapping: bpy.props.EnumProperty(
        name="Bone Mapping",
        items=lambda self, context: [(option, option, "") for option in get_bone_mapping_options()],
    ) # type: ignore

    def execute(self, context):
        try:
            create_template_properties = context.scene.create_template_properties
            selected_mapping_name = create_template_properties.selected_bone_mapping
            debug_print(f"CreateTemplate: Selected bone mapping: {selected_mapping_name}")
            self.report({'INFO'}, f"CreateTemplate: Selected bone mapping: {selected_mapping_name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTemplate-SelectTBoneMapping-Execute: Failed to select bone mapping. Error: {e}")
            return {'CANCELLED'}

class CreateSkeleSwapTemplateSelectTTransformMapOperator(bpy.types.Operator):
    bl_idname = "object.select_t_transform_map"
    bl_label = "Select Transform Map"

    selected_transform_map: bpy.props.EnumProperty(
        name="Transform Map",
        items=lambda self, context: [(option, option, "") for option in get_transform_map_options()],
    ) # type: ignore

    def execute(self, context):
        try:
            create_template_properties = context.scene.create_template_properties
            selected_transform_map_name = create_template_properties.selected_transform_map
            debug_print(f"CreateTemplate: Selected Transform Map: {selected_transform_map_name}")
            self.report({'INFO'}, f"CreateTemplate: Selected Transform Map: {selected_transform_map_name}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTemplate-SelectTTransformMap-Execute: Failed to select transform map. Error: {e}")
            return {'CANCELLED'}


class CreateSkeleSwapTemplateSaveTemplateOperator(bpy.types.Operator):
    bl_idname = "object.save_template"
    bl_label = "Save Template"
    def execute(self, context):
        try:
            scene = context.scene
            create_template_properties = scene.create_template_properties
            property_name = create_template_properties.template_name or "My Template"
            template = create_template_json(create_template_properties)
            validate(
                [property_name, template],
                ["str", "dict"],
                stack_location="CreateTemplate-SaveTemplate",
                input_identifier_strings=["property_name", "template"],
            )

            debug_print(f"CreateTemplate-SaveTemplate: Attempting to save new temolate, {template}, in the template json, under property: {property_name}")
            result = save_to_persistent_data_store_json_property("template_configs", property_name, template)
            if result == {'CANCELLED'}:
                raise RuntimeError("Failed to persist template json data")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"In CreateTemplate-SaveTemplate-Execute: Failed to save template. Error: {e}")
            return {'CANCELLED'}



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

    bpy.utils.register_class(CreateSkeleSwapTemplatePanel)
    bpy.utils.register_class(CreateSkeleSwapTemplateSelectTBoneMappingOperator)
    bpy.utils.register_class(CreateSkeleSwapTemplateSelectTTransformMapOperator)
    bpy.utils.register_class(CreateSkeleSwapTemplateSaveTemplateOperator)





def unregister():
    bpy.utils.unregister_class(CreateTemplateProperties)
    del bpy.types.Scene.create_template_properties

    bpy.utils.unregister_class(CreateSkeleSwapTemplatePanel)
    bpy.utils.unregister_class(CreateSkeleSwapTemplateSelectTBoneMappingOperator)
    bpy.utils.unregister_class(CreateSkeleSwapTemplateSelectTTransformMapOperator)
    bpy.utils.unregister_class(CreateSkeleSwapTemplateSaveTemplateOperator)


if __name__ == "__main__":
    register()
