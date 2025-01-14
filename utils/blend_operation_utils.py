import bpy

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
        print("Invalid parameter type. Must be a string (collection name) or an object.")
        return

    # Fetch the collection
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Unlink the collection from all scenes
    for scene in bpy.data.scenes:
        # Check by collection name
        if collection_name in [child.name for child in scene.collection.children]:
            scene.collection.children.unlink(collection)
    
    # Delete all objects in the collection
    for obj in collection.objects:
        print(f"Deleting object: {obj.name}")
        bpy.data.objects.remove(obj, do_unlink=True)
    
    # Delete the collection itself
    print(f"Deleting collection: {collection_name}")
    bpy.data.collections.remove(collection)
