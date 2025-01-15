import bpy # type: ignore

def duplicate_mesh(mesh_to_duplicate):
    if not mesh_to_duplicate or mesh_to_duplicate.type != 'MESH':
        raise ValueError("Provided object is not a valid mesh.")
    
    bpy.ops.object.select_all(action='DESELECT')
    mesh_to_duplicate.select_set(True)
    bpy.context.view_layer.objects.active = mesh_to_duplicate
    
    bpy.ops.object.duplicate()
    duplicated_mesh = bpy.context.object
    return duplicated_mesh

def delete_mesh(mesh_to_delete):
    if not mesh_to_delete or mesh_to_delete.type != 'MESH':
        raise ValueError("Provided object is not a valid mesh.")
    
    bpy.ops.object.select_all(action='DESELECT')
    mesh_to_delete.select_set(True)
    bpy.context.view_layer.objects.active = mesh_to_delete
    
    bpy.ops.object.delete()


def delete_all_shapekeys(mesh):
    if mesh.data.shape_keys:  # Check if the mesh has shapekeys
        keys = mesh.data.shape_keys.key_blocks
        for key in list(keys):
            mesh.shape_key_remove(key)
        print("Deleted all shapekeys.")
    else:
        print("No shapekeys found.")

def create_basis_shape_key(mesh):
    if not mesh.data.shape_keys:
        mesh.shape_key_add(name="Basis")
        print("Created 'Basis' shape key.")
    elif "Basis" not in mesh.data.shape_keys.key_blocks or "basis" not in mesh.data.shape_keys.key_blocks:
        mesh.shape_key_add(name="Basis")
        print("Added 'Basis' shape key.")
    else:
        print("'Basis' shape key already exists.")


def copy_shapekeys(source_mesh, target_mesh):
    if not source_mesh or source_mesh.type != 'MESH':
        raise ValueError("Source object is not a valid mesh.")
    if not target_mesh or target_mesh.type != 'MESH':
        raise ValueError("Target object is not a valid mesh.")
    
    if not source_mesh.data.shape_keys or not source_mesh.data.shape_keys.key_blocks:
        raise ValueError("Source mesh has no shapekeys to copy.")
    
    if not target_mesh.data.shape_keys:
        bpy.context.view_layer.objects.active = target_mesh
        bpy.ops.object.shape_key_add(from_mix=False)
    
    for shape_key in source_mesh.data.shape_keys.key_blocks:
        if shape_key.name == 'Basis':
            continue
        
        target_mesh.shape_key_add(name=shape_key.name, from_mix=False)
        
        target_key = target_mesh.data.shape_keys.key_blocks[shape_key.name]
        target_key.data.foreach_set(
            "co", [co for vertex in shape_key.data for co in vertex.co]
        )
    
    print(f"Copied {len(source_mesh.data.shape_keys.key_blocks) - 1} shapekeys to target mesh.")


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

def transfer_weights(base_mesh, target_mesh):
    if base_mesh and target_mesh and base_mesh.data and target_mesh.data:
        for vgroup in base_mesh.vertex_groups:
            target_vgroup = target_mesh.vertex_groups.new(name=vgroup.name)
            for vert in target_mesh.data.vertices:
                for group in vert.groups:
                    if group.group == vgroup.index:
                        target_vgroup.add([vert.index], group.weight, 'REPLACE')