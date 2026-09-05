import bpy # type: ignore
import json
import os
import shutil

PERSISTENT_JSON_FILE_NAMES = ("bone_mappings", "bone_transforms", "template_configs")


class PathStateManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PathStateManager, cls).__new__(cls)
            cls._instance.persistent_paths = {}
        return cls._instance

    def _get_persistent_data_dir(self):
        return bpy.utils.user_resource('SCRIPTS', path="addon_data/SkeleSwap")

    def get_default_json_file_path(self, json_file_name):
        addon_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        return os.path.join(addon_dir, "utils", "data", f"{json_file_name}.json")

    def get_persistent_json_file_path(self, json_file_name):
        persistent_data_dir = self._get_persistent_data_dir()
        return os.path.join(persistent_data_dir, f"{json_file_name}.json")

    def get_json_file_path(self, json_file_name):
        if json_file_name in self.persistent_paths:
            return self.persistent_paths[json_file_name]

        persisted_json_file_path = self.get_persistent_json_file_path(json_file_name)
        default_path = self.get_default_json_file_path(json_file_name)

        if os.path.exists(persisted_json_file_path):
            self.persistent_paths[json_file_name] = persisted_json_file_path
            return persisted_json_file_path
        
        return default_path

    def ensure_persistent_path(self, json_file_name):
        json_file_path = self.get_persistent_json_file_path(json_file_name)
        if json_file_name in self.persistent_paths and self.persistent_paths[json_file_name] == json_file_path and os.path.exists(json_file_path):
            return json_file_path

        persistent_data_dir = self._get_persistent_data_dir()
        os.makedirs(persistent_data_dir, exist_ok=True)

        if not os.path.exists(json_file_path):
            original_json = self.get_default_json_file_path(json_file_name)
            if os.path.exists(original_json):
                shutil.copy(original_json, json_file_path)
            else:
                with open(json_file_path, "w") as json_file:
                    json.dump({}, json_file, indent=4)

        self.persistent_paths[json_file_name] = json_file_path
        return json_file_path

    def is_managed_json_file(self, file_path, json_file_name):
        normalized_input_path = os.path.abspath(file_path)
        normalized_default_path = os.path.abspath(self.get_default_json_file_path(json_file_name))
        normalized_persistent_path = os.path.abspath(self.get_persistent_json_file_path(json_file_name))
        return normalized_input_path in {normalized_default_path, normalized_persistent_path}


class JsonStoreManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JsonStoreManager, cls).__new__(cls)
            cls._instance._stores = {}
        return cls._instance

    def initialize(self, json_file_names=None):
        json_file_names = json_file_names or PERSISTENT_JSON_FILE_NAMES
        for json_file_name in json_file_names:
            self.reload_store(json_file_name, ensure_persistent=True)

    def clear_cache(self):
        self._stores = {}

    def reload_store(self, json_file_name, ensure_persistent=False):
        json_file_path = (
            path_state_manager.ensure_persistent_path(json_file_name)
            if ensure_persistent
            else path_state_manager.get_json_file_path(json_file_name)
        )
        data = open_json(json_file_path)
        if not isinstance(data, dict):
            data = {}
        self._stores[json_file_name] = data
        return data

    def get_store(self, json_file_name):
        if json_file_name not in self._stores:
            self.reload_store(json_file_name, ensure_persistent=True)
        return self._stores.get(json_file_name, {})

    def list_keys(self, json_file_name):
        return list(self.get_store(json_file_name).keys())

    def get_property(self, json_file_name, property_name):
        return self.get_store(json_file_name).get(property_name)

    def get_contents_copy(self, json_file_name):
        return dict(self.get_store(json_file_name))

    def _atomic_save_store(self, json_file_name):
        json_file_path = path_state_manager.ensure_persistent_path(json_file_name)
        json_data = self.get_store(json_file_name)
        temp_file_path = f"{json_file_path}.tmp"

        try:
            with open(temp_file_path, "w") as json_file:
                json.dump(json_data, json_file, indent=4)
            os.replace(temp_file_path, json_file_path)
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass

    def upsert_property(self, json_file_name, property_name, json_data):
        store = self.get_store(json_file_name)
        store[property_name] = json_data
        self._atomic_save_store(json_file_name)

    def remove_property(self, json_file_name, property_name):
        store = self.get_store(json_file_name)
        if property_name in store:
            del store[property_name]
            self._atomic_save_store(json_file_name)


path_state_manager = PathStateManager()
json_store_manager = JsonStoreManager()

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

def _get_managed_store_name_for_file_path(file_path):
    base_name = os.path.basename(file_path)
    if not base_name.endswith(".json"):
        return None
    json_file_name = os.path.splitext(base_name)[0]
    if json_file_name not in PERSISTENT_JSON_FILE_NAMES:
        return None
    if path_state_manager.is_managed_json_file(file_path, json_file_name):
        return json_file_name
    return None


def get_json_property(file_path, property):
    try:
        managed_store_name = _get_managed_store_name_for_file_path(file_path)
        if managed_store_name:
            return json_store_manager.get_property(managed_store_name, property)
        json_data = open_json(file_path)
        if isinstance(json_data, dict):
            return json_data.get(property)
        return None
    except Exception as e:
        print(f"An error occurred while reading the json file. Error: {e}")
        return {'CANCELLED'}


def get_current_json_data_file_path(json_file_name):
    if json_file_name in PERSISTENT_JSON_FILE_NAMES:
        path = path_state_manager.ensure_persistent_path(json_file_name)
    else:
        path = path_state_manager.get_json_file_path(json_file_name)
    debug_print(f"DevUtils-GetCurrentJSONDataFilePath: Returning path: {path}")
    return path



def save_to_persistent_data_store_json_property(json_file_name, property_name, jsonData):
    try:
        json_store_manager.upsert_property(json_file_name, property_name, jsonData)
    except Exception as e:
        print(f"An error occurred while saving the JSON file. Error: {e}")
        return {'CANCELLED'}


def get_persistent_data_store_json_property(json_file_name, property_name):
    try:
        return json_store_manager.get_property(json_file_name, property_name)
    except Exception as e:
        print(f"An error occurred while getting the json property from the persistent data store. Error: {e}")
        return None


def get_persistent_data_store_json_keys(json_file_name):
    try:
        return json_store_manager.list_keys(json_file_name)
    except Exception as e:
        print(f"An error occurred while getting keys from the persistent data store. Error: {e}")
        return []


def get_persistent_data_store_json_contents(json_file_name):
    try:
        return json_store_manager.get_contents_copy(json_file_name)
    except Exception as e:
        print(f"An error occurred while getting contents from the persistent data store. Error: {e}")
        return {}


def initialize_persistent_data_store(json_file_names=None):
    try:
        json_store_manager.initialize(json_file_names)
    except Exception as e:
        print(f"An error occurred while initializing the persistent data store. Error: {e}")
        return {'CANCELLED'}


def reset_persistent_data_store_cache():
    json_store_manager.clear_cache()


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

    major, minor, _ = bpy.app.version

    if major < 4:  # Blender 2.8x - 3.x: Use Bone Groups
        bone_group = armature_object.pose.bone_groups.get("CustomColorGroup")
        if not bone_group:
            bone_group = armature_object.pose.bone_groups.new(name="CustomColorGroup")

        bone_group.colors.normal = base_color
        bone_group.colors.select = selected_color
        bone_group.colors.active = active_color
        bone_group.color_set = 'CUSTOM'

        for bone in armature_object.pose.bones:
            bone.bone_group = bone_group


    else:  # Blender 4.x
        for bone in armature_object.pose.bones:
            bone.color.palette = "CUSTOM"
            bone.color.custom.normal = base_color
            bone.color.custom.select = selected_color
            bone.color.custom.active = active_color
    
    print(f"Assigned color {rgb_color} using Bone Groups (Blender {major}.{minor})")


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
