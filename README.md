# SlicerOpenAnatomy

3D Slicer extension for exporting Slicer scenes to use in the [OpenAnatomy.org](https://www.openanatomy.org/) browser and glTF and OBJ file viewers.

## OpenAnatomy Export module

This module exports a model hierarchy or segmentation node from 3D Slicer into a single glTF or OBJ file, including all the model colors and opacities; and for glTF also model hierarchy and model names.

![OpenAnatomy Exporter module screenshot](Screenshot03.png)

## Quick start

- Install `3D Slicer` and the `SlicerOpenAnatomy` extension
- Create/edit a segmentation using `Segment Editor` module
- Export the segmentation to glTF file using `OpenAnatomy Export` module
- Upload your model to Dropbox or GitHub and get a download link
- Create a view link by prepending `https://3dviewer.net/#model=` to the download link. The model can be viewed in 3D in the web browser on computers, tablets, and phones.

Example view link: https://3dviewer.net/#model=https://www.dropbox.com/s/38arwo2uhzu0ydg/SPL-Abdominal-Atlas.gltf?dl=0

## glTF viewers

- Online (in web browser):
  - [3dviewer.net](https://3dviewer.net/): simple, easy-to-use viewer
    - Free, open-source project ([GitHub page](https://github.com/kovacsv/Online3DViewer))
    - Model hierarchy can be viewed as a tree, entire branch can be shown/hidden
    - Model can be picked by clicking on an object in the 3D view
    - Orbit and free rotation
    - No editing of material or lighting
    - Can open a URL and can be embedded into an iframe
  - [gltfviewer.com](https://www.gltfviewer.com/): more complex viewer, for advanced viewing and editing
    - Allows material and light editing and saving of modified glTF file
    - Shows nodes and meshes separately
    - Model hierarchy can be viewed as a tree, entire branch can be shown/hidden
    - Model can be picked by clicking on an object in the 3D view. Limitation: the item must be visible in the tree (branch must be expanded).
    - Search by name
  - [Sketchfab](https://sketchfab.com/): commercial project, allows sharing with password, advanced lighting and other rendering settings, virtual reality.
- Android phones:
  - [OpenCascade CAD assistant](https://play.google.com/store/apps/details?id=org.opencascade.cadassistant):
    - Free application
    - Model hierarchy can be viewed as a tree, entire branch can be shown/hidden
    - Model can be picked by clicking on an object in the 3D view
    - Material and lighting editing

### Examples

Open a glTF files stored in a github repository:

https://3dviewer.net/#model=https://raw.githubusercontent.com/lassoan/Test/master/SPL-Abdominal-Atlas.gltf

![Exported glTF file viewed in 3dviewer.net](Screenshot02.png)

Embed 3dviewer.net in a website:

```
<iframe width="640" height="480" style="border:1px solid #eeeeee;" 
src="https://3dviewer.net/embed.html#model=https://raw.githubusercontent.com/lassoan/Test/master/SPL-Abdominal-Atlas.gltf">
</iframe>
```
