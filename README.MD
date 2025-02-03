# SkeleSwap

**SkeleSwap** is a Blender addon designed to streamline and automate the process of swapping skeletons in rigged armatures. Initially it was created to help me transfer the Epic skeleton to the MB Lab created meshes...But then I went on a "side quest", and this is the result.

- **Flexibility**: Supports various skeleton types and allows custom configurations.
- **Efficiency**: Once you create the configuration for a pair of skeletons. You can resuse the template, and change skeletons with just a few clicks.
- **Extensibility**: Users can add new skeletons and create automated workflows for their specific needs.

## Key Features

### **In-Built Skeleton Swap Support**

- **MB Lab to Epic Skeleton**: Change the skeleton of an MB Lab skeletal mesh to the UE5 Epic skeleton.
- **Mixamo to Epic Skeleton**: Change Mixamo skeletons to the UE5 Epic skeleton.

### **Automated Skeleton Swapping**

Easily swap the skeleton of a rigged armature to another skeleton with minimal manual intervention once you have created a template for them. SkeleSwap dynamically adjusts the target skeleton to fit the mesh it is being swapped into, by going through a list of transforms based on the Armature of your desired mesh. Provided the rest pose is similar and the armature is standardized, you can reuse your custom template after creating it once.

### **Adding Custom Skeleton Support**

Add support for any skeleton by creating bone mapping and transformation lists directly within the addon. SkeleSwap allows you to save these configurations as templates, making them reusable across multiple meshes with the same skeleton.

### **Bone Matching Tool, to snap bones to match the location of another bone**

The built-in tool lets you easily match bone positions and orientations, ensuring a perfect fit and alignment between the original and target skeletons, these transforms then can be saved and reused, so you only have to do it once.

### **Exporting The Bone Map and Transform List**

Once you have created your template for your custom needs, you can export the bone mapping, and transform list. Allowing others to set up their template in a few clicks, letting multiple people reuse it, saving time and helping consistency

### **Facial ARKit52 Shapekey Creation (Currently only works for Separate Face rigs, that drive shapekeys. WIP)**

If your face rigs are the same accross multiple characters, and you want facial motion track using ARKIT52, but you dont want to create the animations over and over again. You can create it once, save it in a blend file, the addon can get the animation from the blend file, and create the shapekeys based on that animation. (works best if the face rig is a separate armature. If it is part of the main armature, that is still a work in progress)

## Planned Features (In order of Priority)

- **Generating Dynamic Control Rig (IK, FK) -> _Already done for UE5 Skeleton_**
- **Supporting Multi-Mesh/Modular Skeletal Meshes (_WIP_)**
- **Tool to copy a bone from one armature to the other (_Logic is already done, just not included in the bone transforms list yet_)**
- **Option to mirror, added transform items not just the rotation, to significantly speed up the process of creating custom transform maps**
- **The ability to edit saved templates, bone mappings, and transform maps**
- **Facial Shapekey Creation from deformbone based face rigs (_Logic implemented, but I am heavily procastinating on rigging faces, and testing with them, so no guarantee it works_)**
- **Dynamic LOD Creation for the Skeleton Swapped SKMs (_We will see if this ever get implemented... topology play a huge role in this, and I am not sure I want to add any retopology algortythms or logic to this addon, since it is primary about bones_)**
