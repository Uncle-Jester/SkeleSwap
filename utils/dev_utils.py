import bpy # type: ignore
import json
import os
import shutil

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


def get_current_json_data_file_path(json_file_name):
    persistent_data_dir = bpy.utils.user_resource('SCRIPTS', path="addon_data/SkeleSwap")
    persisted_json_file_path = os.path.join(persistent_data_dir, f"{json_file_name}.json")
    if not os.path.exists(persisted_json_file_path):
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(addon_dir, "utils", "data", f"{json_file_name}.json")
    else:
        return persisted_json_file_path



def save_to_persistent_data_store_json_property(json_file_name, property_name, jsonData):
    persistent_data_dir = bpy.utils.user_resource('SCRIPTS', path="addon_data/SkeleSwap")
    try:    
        debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: Checking persistent file directory, creating if doesnt exist")
        os.makedirs(persistent_data_dir, exist_ok=True)
    except:
        debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: Failed to create file directory")

    json_file_path = os.path.join(persistent_data_dir, f"{json_file_name}.json")
    debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: File path: {json_file_path}")
    if not os.path.exists(json_file_path):
        debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: File path doesnt exist. Creating.")
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        original_json = os.path.join(addon_dir, "utils", "data", f"{json_file_name}.json")
        if os.path.exists(original_json):
            debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: Copying original json to the new path.")
            shutil.copy(original_json, json_file_path)
        debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: Created Filepath for persistent storage of json files")
    try:
        if os.path.exists(json_file_path):
            debug_print(f"DevUtils-SaveToPersistentStoreJsonProp: File path exists. Attempting to save and create")
            with open(json_file_path, 'r+') as json_file:
                data = json.load(json_file)
                data[property_name] = jsonData
                json_file.seek(0)
                json.dump(data, json_file, indent=4)
                json_file.truncate()
        else:
            with open(json_file_path, 'w') as json_file:
                json.dump({property_name: jsonData}, json_file, indent=4)
        
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
