import bpy


def parent_armature(mesh, armature):
    """
    Parents the mesh to the armature using standard armature deform.
    """
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature

    bpy.ops.object.parent_set(type='ARMATURE')
    print(f"Parented mesh '{mesh.name}' to armature '{armature.name}'.")


def apply_armature(mesh, armature):
    """
    Applies the armature modifier to the mesh only if it is parented to the armature.
    """
    if mesh.parent != armature:
        print(f"Mesh '{mesh.name}' is not parented to the armature '{armature.name}'.")
        return

    bpy.context.view_layer.objects.active = mesh
    for modifier in mesh.modifiers:
        if modifier.type == 'ARMATURE' and modifier.object == armature:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            print(f"Applied armature modifier on mesh: {mesh.name}")
            return
    print("No armature modifier found to apply.")

def clear_all_armatures(mesh):
    """
    WARNING: This will clear, NOT apply all armature modifiers, as well as the unparent parent armature
    """
    if mesh.type != 'MESH':
        print(f"Object {mesh.name} is not a mesh. Skipping.")
        return

    armature_modifiers = [mod for mod in mesh.modifiers if mod.type == 'ARMATURE']
    for mod in armature_modifiers:
        print(f"Removing armature modifier: {mod.name} from {mesh.name}")
        mesh.modifiers.remove(mod)

    if mesh.parent and mesh.parent.type == 'ARMATURE':
        print(f"Clearing parent armature: {mesh.parent.name} from {mesh.name}")
        mesh.parent = None

    print(f"All armatures cleared from {mesh.name}.")

def delete_armature(armature):
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    bpy.ops.object.delete()


def apply_pose_as_rest_pose(armature):
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply()
    print("Applied pose as the new rest pose.")


def scale_selected_armature_with_child_meshes(armature, scale_factor=100):
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    empty = bpy.context.object

    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)

    children = [child for child in armature.children if child.type == 'MESH']

    for obj in [armature] + children:
        obj.parent = empty

    empty.scale = (scale_factor, scale_factor, scale_factor)
    
    bpy.ops.object.select_all(action='DESELECT')
    empty.select_set(True)
    for obj in [armature] + children:
        obj.select_set(True)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)


    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True) 
    for child in children:
        child.select_set(True)
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

    bpy.data.objects.remove(empty)

def find_armature_by_name(armature_name):
    armature = bpy.data.objects.get(armature_name)
    if not armature or armature.type != 'ARMATURE':
        print(f"Armature '{armature_name}' not found. Please Import a UE5 SKM")
        return {'CANCELLED'}
    return armature