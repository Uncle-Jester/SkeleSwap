import bpy # type: ignore
import json

def get_debug_print_status():
    if hasattr(bpy.context.scene, "enable_debug_print"):
        return bpy.context.scene.enable_debug_print
    else:
        return False

def debug_print(string_to_print):
    if get_debug_print_status():
        print(string_to_print)

def open_json(file_path):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}


def get_json_property(file_path, property):
    try:
        json_data = open_json(file_path)
        return json_data.get(property)
    except Exception as e:
        print(f"An error occurred while reading the json file. Error: {e}")
        return {'CANCELLED'}
    
def assign_bone_color_to_armature(armature_object, rgb_color):
    if armature_object.type != 'ARMATURE':
        print("The provided object is not an armature!")
        return

    # blender uses normalized rgb values, but as a user, i think it's easier for us to just use the 0-255 values you would see in most color pickers, so the input is based on that, then the below code just makes it compatible (normalizes) the values
    base_color = tuple(c / 255 for c in rgb_color)

    def brighten(color, factor=1.5):
        return tuple(min(1.0, c * factor) for c in color)

    selected_color = brighten(base_color, factor=2)
    active_color = brighten(base_color, factor=3)

    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='POSE')

    bone_group = armature_object.pose.bone_groups.get("CustomColorGroup")
    if not bone_group:
        bone_group = armature_object.pose.bone_groups.new(name="CustomColorGroup")

    bone_group.colors.normal = base_color
    bone_group.colors.select = selected_color
    bone_group.colors.active = active_color

    bone_group.color_set = 'CUSTOM'

    for bone in armature_object.pose.bones:
        bone.bone_group = bone_group

    print(f"Assigned color {rgb_color} to all bones in {armature_object.name} with tweaks for selected and active.")

def validate(inputs, validate_types=None, stack_location=None, custom_message=None, input_identifier_strings=None):
    stack_location = stack_location if stack_location else 'unknown'
    
    if len(inputs) == 0:
        raise ValueError(f"Please provide inputs to validate. Input validation failed at: {stack_location}")
    
    for index, input in enumerate(inputs):
        input_id_string = ''
        validate_type = None

        if input_identifier_strings:
            input_id_string = input_identifier_strings[index] if index < len(input_identifier_strings) else ''
        
        if validate_types:
            validate_type = validate_types[index] if index < len(validate_types) else None


        if input:
            if validate_types is not None:
                if index < len(validate_types) and (validate_type is not None):
                    actual_type = input.type if hasattr(input, "type") else type(input).__name__
                    if actual_type != validate_type:
                        if custom_message:
                            raise ValueError(f"In {stack_location}: TypeError: {custom_message}")
                        else:
                            raise ValueError(f"In {stack_location}: Expected input for {input_id_string} {validate_type} to be of type: {validate_type}, instead got: {actual_type}")
                    else:
                        debug_print(f"Validate -> Type validation is Succesful. Proceeding")
                        continue
                else:
                    debug_print(f"Validate -> Type validation is not needed. Proceeding")
                    continue
            else:
                debug_print(f"Validate -> Type validation is not needed. Proceeding")
                continue
        else:
            if custom_message:
                raise ValueError(f"In {stack_location}: ValueError: {custom_message}")
            else:
                raise ValueError(f"In {stack_location}: No value provided for valudation. Expected value of {validate_type}, {input_id_string}.")
