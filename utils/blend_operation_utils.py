import bpy # type: ignore

def find_collection_by_object(obj):
    for collection in bpy.data.collections:
        if obj.name in collection.objects:
            return collection
    return None

def delete_collection(collection_or_child):
    if isinstance(collection_or_child, str):
        collection_name = collection_or_child
    elif isinstance(collection_or_child, bpy.types.Object):
        collection = find_collection_by_object(collection_or_child)
        if collection:
            collection_name = collection.name
        else:
            print(f"No collection found for object '{collection_or_child.name}'.")
            return
    else:
        raise ValueError(f"In BlendOperationUtils-DeleteCollection: Invalid parameter type. Must be a string (collection name) or an object.")

    collection = bpy.data.collections.get(collection_name)
    if not collection:
        raise ValueError(f"In BlendOperationUtils-DeleteCollection: Collection '{collection_name}' not found.")

    try:
        for scene in bpy.data.scenes:
            if collection_name in [child.name for child in scene.collection.children]:
                scene.collection.children.unlink(collection)

        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

        bpy.data.collections.remove(collection)
    except Exception as e:
       raise RuntimeError(f"In BlendOperationUtils-DeleteCollection: Couldn't delete collection. Error: {e}")
