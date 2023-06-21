import vtk
import qt
import json

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# AtlasEditor
#

class AtlasEditor(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "OpenAnatomy AtlasEditor"  
        self.parent.categories = ["OpenAnatomy"]  
        self.parent.dependencies = []  
        self.parent.contributors = ["Andy Huynh (ISML, University of Western Australia)"] 
        self.parent.helpText = """"""
        self.parent.acknowledgementText = """"""

#
# AtlasEditorWidget
#

class AtlasEditorWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/AtlasEditor.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = AtlasEditorLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
        # (in the selected parameter node).

        self.ui.atlasLabelMapInputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI) #vtkMRMLLabelMapVolumeNode
        self.ui.atlasLabelMapOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI) #vtkMRMLLabelMapVolumeNode
        self.ui.atlasStructureInputPath.connect("currentPathChanged(QString)", self.updateParameterNodeFromGUI)

        # Buttons
        self.ui.downloadButton.connect('clicked(bool)', self.onDownloadButton)
        self.ui.mergeButton.connect('clicked(bool)', self.onMergeButton)
        self.ui.removeButton.connect('clicked(bool)', self.onRemoveButton)
        self.ui.updateButton.connect('clicked(bool)', self.onUpdateButton)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user


    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """
        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    
        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.atlasLabelMapInputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputLabelMap"))
        self.ui.atlasLabelMapOutputSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputLabelMap"))
        self.ui.atlasStructureInputPath.setCurrentPath(self._parameterNode.GetParameter("InputStructurePath"))

        # Update buttons states and tooltips
        # Update button
        if self._parameterNode.GetNodeReference("InputLabelMap") and len(self.ui.atlasStructureInputPath.currentPath) > 1:
            self.ui.updateButton.toolTip = "Update atlas structure tree widget."
            self.ui.updateButton.enabled = True
        else:
            self.ui.updateButton.toolTip = "Import input label map and atlas structure json file."
            self.ui.updateButton.enabled = False
        
        # Merge button
        if self._parameterNode.GetNodeReference("InputLabelMap") and self._parameterNode.GetNodeReference("OutputLabelMap"):
            self.ui.mergeButton.toolTip = "Merge input label map and output label map."
            self.ui.mergeButton.enabled = True
        else:
            self.ui.mergeButton.toolTip = "Select input label map and output label map."
            self.ui.mergeButton.enabled = False

        # Remove button
        if self._parameterNode.GetNodeReference("InputLabelMap") and self._parameterNode.GetNodeReference("OutputLabelMap"):
            self.ui.removeButton.toolTip = "Remove input label map and output label map."
            self.ui.removeButton.enabled = True
        else:
            self.ui.removeButton.toolTip = "Select input label map and output label map."
            self.ui.removeButton.enabled = False

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

        self._parameterNode.SetNodeReferenceID("InputLabelMap", self.ui.atlasLabelMapInputSelector.currentNodeID)
        self._parameterNode.SetNodeReferenceID("OutputLabelMap", self.ui.atlasLabelMapOutputSelector.currentNodeID)
        self._parameterNode.SetParameter("InputStructurePath", self.ui.atlasStructureInputPath.currentPath)


        self._parameterNode.EndModify(wasModified)

    def onDownloadButton(self):
        """
        Run processing when user clicks "Download" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            self.logic.downloadAtlas(self.ui.atlasInputSelector.currentIndex, self.ui.atlasLabelMapInputSelector, self.ui.atlasStructureInputPath, self.ui.structureTreeWidget, self.ui.atlasLabelMapOutputSelector)

    def onMergeButton(self):
        """
        Run processing when user clicks "Merge" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            self.logic.merge(self.ui.atlasLabelMapInputSelector.currentNode(), self.ui.atlasLabelMapOutputSelector.currentNode())
    
    def onRemoveButton(self):
        """
        Run processing when user clicks "Remove" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            self.logic.remove(self.ui.atlasLabelMapInputSelector.currentNode(), self.ui.atlasLabelMapOutputSelector.currentNode())

    def onUpdateButton(self):
        """
        Run processing when user clicks "Update" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
            
            self.logic.setup(self.ui.atlasLabelMapInputSelector.currentNode(), self.ui.atlasLabelMapOutputSelector.currentNode(), self.ui.atlasStructureInputPath.currentPath, self.ui.structureTreeWidget)

            self.logic.updateStructureView()


#
# AtlasEditorLogic
#

class AtlasEditorLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self.atlasInputLabelMapVolumeNode = None
        self.atlasOutputLabelMapVolumeNode = None
        self.atlasStructureTreeWidget = None
        self.atlasStructureJSON = None
        self.atlasStructureTree = None
    """
    Dictionary of atlas_data. Key is atlas ID, value is a list of URLs to download atlas data.
    Key:
        0: SPL/NAC Brain Atlas 
        1: SPL Liver Atlas

    List Index:
        0: Atlas Label Map (.nrrd) URL
        1: Atlas Color Table (.ctbl) URL
        2: Atlas Structure (.json) URL

    """
    atlas_data = {
        0: ["https://drive.google.com/uc?export=download&id=1sb_Syoi33pYwxCzCqITXyKrZAxRger5O",
              "https://drive.google.com/uc?export=download&id=1ed-OuzGz6DNJ9DsYmQT2nQHN8r0s8FV7",
              "https://drive.google.com/uc?export=download&id=17_NLdqOVEiAxQtOuhcFcOZTuEBlvbYHd"],
        1: ["https://drive.google.com/uc?export=download&id=1ZdIiO7CjT5-27NtofimN16brsNbh2pjB",
            "https://drive.google.com/uc?export=download&id=1oQ8gXMN8wFA5fhl7J9xydRtUcH4bDGHV",
            "https://drive.google.com/uc?export=download&id=1TGzNZO-j5V1gJ5m_R1RjJPXI-zwXcdov"]
    }

    def setup(self, atlasInputLabelMapVolumeNode, atlasOutputLabelMapVolumeNode, atlasStructureJsonPath, atlasStructureTreeWidget):
        """
        Setup variables for atlas editor
        """
        self.atlasInputLabelMapVolumeNode = atlasInputLabelMapVolumeNode
        self.atlasOutputLabelMapVolumeNode = atlasOutputLabelMapVolumeNode
        self.atlasStructureJSON = json.load(open(atlasStructureJsonPath))
        self.atlasStructureTreeWidget = atlasStructureTreeWidget

    def downloadFromURL(self, url, filename):
        """
        Download file from URL and save to filename (folder must exist)
        """
        try:         
            print("Downloading file from " + url + " ...")
            import urllib
            urllib.request.urlretrieve(url, filename)
        except Exception as e:
            print("Error: can not download file  ...")
            print(e)   
            return -1

    def downloadAtlas(self, atlasIndex, atlasInputNode, atlasStructureInputPath, structureTree, atlasOutputNode):
        """
        Download atlas data from URL and load into Slicer
        """
        # Checks if atlas is supported from the atlas selector
        if atlasIndex != 0:
            slicer.util.errorDisplay("Atlas not yet supported.", waitCursor=True)
            return
        
        # Set up paths for downloading atlas data using Slicer's cache directory
        cache_path = slicer.mrmlScene.GetCacheManager().GetRemoteCacheDirectory()
        atlas_path = cache_path + "/atlas.nrrd"
        atlas_lut_path = cache_path + "/atlas-lut.ctbl"
        atlas_structure_path = cache_path + "/atlas-structure.json"

        # Download atlas data from atlas_data dictionary
        self.downloadFromURL(self.atlas_data[atlasIndex][0], atlas_path)
        self.downloadFromURL(self.atlas_data[atlasIndex][1], atlas_lut_path)
        self.downloadFromURL(self.atlas_data[atlasIndex][2], atlas_structure_path)

        # Load atlas data into Slicer as a labelmap volume
        atlas_lut = slicer.util.loadColorTable(atlas_lut_path)
        atlas = slicer.util.loadVolume(atlas_path, properties={'labelmap': True, 'colorNodeID': atlas_lut.GetID()})
        
        # Update the 'Manually Import Atlas' fields
        atlasInputNode.setCurrentNode(atlas)
        atlasOutputNode.setCurrentNode(atlas)
        
        atlasStructureInputPath.setCurrentPath(atlas_structure_path)

        # Sets up variables and Update the 'Atlas Structure' tree widget
        self.setup(atlasInputNode.currentNode(), atlasOutputNode.currentNode(), atlasStructureInputPath.currentPath, structureTree)
        self.updateStructureView()

        return

    def buildHierarchy(self, currentTree = None, groups=None):
        """
        Build the hierarchy of the atlas in the widget tree.
        """
        # If currentTree is None -> we set up the root of the tree.
        if currentTree is None and groups is None:
            groups = []
            root = []
            for item in self.atlasStructureJSON:
                if item['@id'] == "#__header__":
                    for member in item['root']:
                        root.append(member)
            
            for item in self.atlasStructureJSON:
                if item['@id'] in root:
                    self.atlasStructureTree = qt.QTreeWidgetItem(self.atlasStructureTreeWidget)
                    self.atlasStructureTree.setFlags(self.atlasStructureTree.flags() | qt.Qt.ItemIsTristate | qt.Qt.ItemIsUserCheckable)
                    self.atlasStructureTree.setText(0, item['annotation']['name'])
                    currentTree = self.atlasStructureTree
                    for member in item['member']:
                        groups.append(member)
        
        # If currentTree is not None -> We are set up the children of the tree.
        for group in groups:
            for item in self.atlasStructureJSON:
                if item['@id'] == group:
                    child = qt.QTreeWidgetItem()
                    currentTree.addChild(child)
                    child.setText(0, item['annotation']['name'])
                    child.setFlags(child.flags() | qt.Qt.ItemIsTristate | qt.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, qt.Qt.Unchecked)
                    if item['@type'] == "Group":
                        groups1 = []
                        for member in item['member']:
                            groups1.append(member)
                        self.buildHierarchy(child, groups1)
    
    def updateStructureView(self):
        """
        Update the structure view of the atlas.
        """
        # clear the tree
        self.atlasStructureTreeWidget.clear()
        self.buildHierarchy()
        self.atlasStructureTreeWidget.expandToDepth(0)

    def getCheckedItems(self):
        """
        Helper function to get the checked items of the structure view for mergined/removing functions.
        """
        checked = dict()

        signal_count = self.atlasStructureTree.childCount()

        for i in range(signal_count):
            if self.atlasStructureTree.child(i).checkState(0) == qt.Qt.Checked:

                signal = self.atlasStructureTree.child(i)
                checked_sweeps = list()
                num_children = signal.childCount()

                for n in range(num_children):
                    child = signal.child(n)
                    
                    if child.checkState(0) == qt.Qt.Checked:
                        checked_sweeps.append(child.text(0))

                checked[signal.text(0)] = checked_sweeps
            
            elif self.atlasStructureTree.child(i).checkState(0) == qt.Qt.PartiallyChecked:
                checked.update(self.getCheckedItems(self.atlasStructureTree.child(i)))

        return checked

    def getStructureIdOfGroups(self, groups):
        """
        Helper function to get the structure ids of the groups for merging/removing function.
        """
        structureIds = []
        for group in groups:
            for item in self.atlasStructureJSON:
                if item['@id'] == group:
                    if item['@type'] == "Structure":
                        if "-" in item['annotation']['name']:
                            structureIds.append(item['annotation']['name'].replace("-", " "))
                        else:
                            structureIds.append(item['annotation']['name'])
                    if item['@type'] == "Group":
                        groups.extend(item['member'])

        return structureIds
    
    def getIdfromName(self, name):
        """
        Helper function to get the ids by name for merging/removing function.
        """
        for item in self.atlasStructureJSON:
            if (item['@type'] == "Structure" or item['@type'] == "Group"):
                if item['annotation']['name'] == name:
                    return item['@id']  
        
    def remove(self, inputLabelMap, outputLabelMap):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        """
        groupsToRemove = []
        checkedItems = self.getCheckedItems()
        for checkedItem in checkedItems:
            group = checkedItems[checkedItem]
            if group:
                groupsToRemove.append(group)

        # flatten the list
        groupsToRemove = [item for sublist in groupsToRemove for item in sublist]

        groupIdsToRemove = []
        for group in groupsToRemove:
            groupIdsToRemove.append(self.getIdfromName(group))
        
        structureIds = self.getStructureIdOfGroups(groupIdsToRemove)

        # Create segmentation
        segmentationNode = slicer.vtkMRMLSegmentationNode()
        slicer.mrmlScene.AddNode(segmentationNode)
        segmentationNode.CreateDefaultDisplayNodes() # only needed for display
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputLabelMap)

        slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(inputLabelMap, segmentationNode)

        for structureId in structureIds:
            segmentationNode.RemoveSegment(structureId)

        slicer.vtkSlicerSegmentationsModuleLogic.ExportAllSegmentsToLabelmapNode(segmentationNode, outputLabelMap)

        slicer.mrmlScene.RemoveNode(segmentationNode)

    def mergeSegments(self, segmentationNode, segmentsToMerge, mergedSegmentName):

        groupIdsToMerge = []
        for group in segmentsToMerge:
            groupIdsToMerge.append(self.getIdfromName(group))
        structureIds = self.getStructureIdOfGroups(groupIdsToMerge)

        # Create temporary segment editor to get access to effects
        self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
        self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)
        
        firstSegment = structureIds[0]

        for i in range(len(structureIds) - 1):
            modifierSegmentID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(structureIds[i + 1])
            selectedSegmentID = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName(firstSegment)
            self.segmentEditorWidget.setSegmentationNode(segmentationNode)
            self.segmentEditorNode.SetOverwriteMode(slicer.vtkMRMLSegmentEditorNode.OverwriteAllSegments) 
            self.segmentEditorNode.SetMaskMode(slicer.vtkMRMLSegmentationNode.EditAllowedEverywhere)
            self.segmentEditorNode.SetSelectedSegmentID(selectedSegmentID)
            self.segmentEditorWidget.setActiveEffectByName("Logical operators")
            effect = self.segmentEditorWidget.activeEffect()
            effect.setParameter("BypassMasking","0")
            effect.setParameter("ModifierSegmentID",modifierSegmentID)
            effect.setParameter("Operation","UNION")
            effect.self().onApply()
        
        segmentationNode.GetSegmentation().GetSegment(selectedSegmentID).SetName(mergedSegmentName)

    def merge(self, inputLabelMap, outputLabelMap):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        """
        # Create segmentation
        segmentationNode = slicer.vtkMRMLSegmentationNode()
        slicer.mrmlScene.AddNode(segmentationNode)
        segmentationNode.CreateDefaultDisplayNodes() # only needed for display
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputLabelMap)

        # Convert labelmap to Segmentation Node
        slicer.vtkSlicerSegmentationsModuleLogic.ImportLabelmapToSegmentationNode(inputLabelMap, segmentationNode)

        # Get checked items
        checkedItems = self.getCheckedItems(self.atlasStructureTree)

        itemsToMerge = dict()
        for checkedItem in checkedItems:
            item = checkedItems[checkedItem]
            if item:
                itemsToMerge[checkedItem] = item

        for i in itemsToMerge.items():
            self.mergeSegments(segmentationNode, i[1], i[0]),

        slicer.vtkSlicerSegmentationsModuleLogic.ExportAllSegmentsToLabelmapNode(segmentationNode, outputLabelMap)

        slicer.mrmlScene.RemoveNode(segmentationNode)