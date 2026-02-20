import bpy # type: ignore
from .dev_utils import debug_print, validate

def get_all_meshes_of_armature(armature):
    validate([armature], ['ARMATURE'], stack_location="MeshUtils-GetAllMeshesOfArmature")
    meshes = [child for child in armature.children if child.type == 'MESH']
    if len(meshes):
        return meshes
    else:
        raise RuntimeError(f"In MeshUtils-GetAllMeshesOfArmature: The provided armature, {armature.name} has no meshes parented to it")

def delete_a_list_of_meshes(mesh_list):
    if mesh_list:
        validate(mesh_list, stack_location="MeshUtils-DeleteAListOfMeshes")
        for mesh in mesh_list:
            validate([mesh], ['MESH'], stack_location="MeshUtils-DeleteAListOfMeshes")
            delete_mesh(mesh)
    else:
        raise RuntimeError(f"In MeshUtils-DeleteAListOfMeshes: No Mesh List provided to delete")

def duplicate_a_list_of_meshes(mesh_list):
    duplicated_mesh_list = []
    if mesh_list:
        validate(mesh_list, stack_location="MeshUtils-DuplicateAListOfMeshes")
        for mesh in mesh_list:
            validate([mesh], ['MESH'], stack_location="MeshUtils-DuplicateAListOfMeshes")
            duplicated_mesh_list.append(duplicate_mesh(mesh))
        return duplicated_mesh_list
    else:
        raise RuntimeError(f"In MeshUtils-DuplicateAListOfMeshes: No Mesh List provided to delete")

def duplicate_mesh(mesh_to_duplicate):
    validate(
        [mesh_to_duplicate],
        ['MESH'],
        stack_location="MeshUtils-DuplicateMesh",
        input_identifier_strings=["mesh_to_duplicate"],
    )
    try:        
        bpy.context.view_layer.objects.active = mesh_to_duplicate
        if bpy.context.object and bpy.context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        mesh_to_duplicate.select_set(True)
        bpy.context.view_layer.objects.active = mesh_to_duplicate

        bpy.ops.object.duplicate()
        mesh_to_duplicate.select_set(False)
        duplicated_mesh = bpy.context.object
        return duplicated_mesh
    except Exception as e:
        raise RuntimeError(f"In MeshUtils-DuplicateMesh: Could not duplicate mesh. Error: {e}")

def delete_mesh(mesh_to_delete):
    validate(
        [mesh_to_delete],
        ['MESH'],
        stack_location="MeshUtils-DeleteMesh",
        input_identifier_strings=["mesh_to_delete"],
    )
    
    bpy.context.view_layer.objects.active = mesh_to_delete
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    try:
        bpy.ops.object.select_all(action='DESELECT')
        mesh_to_delete.select_set(True)
        bpy.context.view_layer.objects.active = mesh_to_delete
        bpy.ops.object.delete()
    except Exception as e:
        raise RuntimeError(f"In MeshUtils-DeleteMesh: Mesh couldn't be deleted. Error: {e}")


def delete_all_shapekeys(mesh):
    validate(
        [mesh],
        ['MESH'],
        stack_location="MeshUtils-DeleteAllShapekeys",
        input_identifier_strings=["mesh"],
    )
    
    try:
        if mesh.data.shape_keys:
            keys = mesh.data.shape_keys.key_blocks
            for key in list(keys):
                mesh.shape_key_remove(key)
            debug_print("Deleted all shapekeys.")
        else:
            debug_print("No shapekeys found.")
    except Exception as e:
        raise RuntimeError(f"In MeshUtils-DeleteAllShapekeys: Delete all Shapekey couldn't be executed. Error: {e}")

def create_basis_shape_key(mesh):
    if not mesh.data.shape_keys:
        mesh.shape_key_add(name="Basis")
        debug_print("Created 'Basis' shape key.")
    elif "Basis" not in mesh.data.shape_keys.key_blocks or "basis" not in mesh.data.shape_keys.key_blocks:
        mesh.shape_key_add(name="Basis")
        debug_print("Added 'Basis' shape key.")
    else:
        debug_print("'Basis' shape key already exists.")


def copy_shapekeys(source_mesh, target_mesh):
    validate(
        [source_mesh, target_mesh],
        ['MESH', 'MESH'],
        stack_location="MeshUtils-CopyShapekeys",
        input_identifier_strings=["source_mesh", "target_mesh"],
    )
    
    if not source_mesh.data.shape_keys or not source_mesh.data.shape_keys.key_blocks:
        debug_print("Source mesh has no shapekeys to copy.")
        return
    
    if not target_mesh.data.shape_keys:
        bpy.context.view_layer.objects.active = target_mesh
        bpy.ops.object.shape_key_add(from_mix=False)
    
    for shape_key in source_mesh.data.shape_keys.key_blocks:
        if shape_key.name == 'Basis' or shape_key.name == 'basis':
            continue
        
        target_mesh.shape_key_add(name=shape_key.name, from_mix=False)
        
        target_key = target_mesh.data.shape_keys.key_blocks[shape_key.name]
        target_key.data.foreach_set(
            "co", [co for vertex in shape_key.data for co in vertex.co]
        )
    
    debug_print(f"Copied {len(source_mesh.data.shape_keys.key_blocks) - 1} shapekeys to target mesh.")


def rename_mesh(mesh_object, new_name):
    if mesh_object:
        mesh_object.name = new_name


def add_decimate_modifier(mesh_object, decimate_type, decimate_amount):
    if mesh_object:
        modifier = mesh_object.modifiers.new(name="Decimate", type='DECIMATE')
        if decimate_type == "un-subdivide":
            modifier.decimate_type = 'UNSUBDIV'
            modifier.iterations = decimate_amount
        elif decimate_type == "collapse":
            modifier.decimate_type = 'COLLAPSE'
            modifier.ratio = decimate_amount
        elif decimate_type == "dissolve":
            modifier.decimate_type = 'DISSOLVE'
            modifier.ratio = decimate_amount

def transfer_weights(base_mesh, target_mesh): # This is used for the LOD creation logic... which is terrrible.. dont use...
    if base_mesh and target_mesh and base_mesh.data and target_mesh.data:
        for vgroup in base_mesh.vertex_groups:
            target_vgroup = target_mesh.vertex_groups.new(name=vgroup.name)
            for vert in target_mesh.data.vertices:
                for group in vert.groups:
                    if group.group == vgroup.index:
                        target_vgroup.add([vert.index], group.weight, 'REPLACE')




def transfer_weights_for_specific_bones(bone_names, target_mesh, base_mesh):
    validate(
        [bone_names, target_mesh, base_mesh],
        ['list', 'MESH', 'MESH'],
        stack_location="MeshUtils-TransferWeightsForSpecificBones",
        input_identifier_strings=["bone_names", "target_mesh", "base_mesh"],
    )
    if bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='DESELECT')
    base_mesh.select_set(True)
    target_mesh.select_set(True)
    bpy.context.view_layer.objects.active = base_mesh

    for bone_name in bone_names:
        if bone_name not in target_mesh.vertex_groups:
            target_mesh.vertex_groups.new(name=bone_name)
    
    for bone_name in bone_names:
        if bone_name in base_mesh.vertex_groups:
            target_mesh.vertex_groups.active = target_mesh.vertex_groups[bone_name]

            bpy.ops.object.data_transfer(
                data_type='VGROUP_WEIGHTS',
                vert_mapping='NEAREST',
                layers_select_src= bone_name,
                layers_select_dst= 'ACTIVE',
                mix_mode='REPLACE'
            )

    bpy.ops.object.mode_set(mode='OBJECT')
