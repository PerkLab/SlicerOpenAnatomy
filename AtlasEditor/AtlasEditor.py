import logging
import os

import vtk
import ctk
import qt

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
        self.parent.title = "AtlasEditor"  # TODO: make this more human readable by adding spaces
        self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """"""

        # Additional initialization step after application startup is complete
        #slicer.app.connect("startupCompleted()", registerSampleData)


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

        self.ui.atlasLabelMapInputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
        #self.ui.atlasLabelMapOutputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

        # Initialize Structure Tree GUI
        self.ui.structureTreeWidget.setHeaderLabels(["Structure"])

        # Buttons
        self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
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
        #self.ui.atlasLabelMapInputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputLabelMap"))

        # Update buttons states and tooltips


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
        self._parameterNode.SetNodeReferenceID("InputAtlasStructure", self.ui.atlasLabelMapInputSelector.currentNodeID)

        # print check if the node is set
        print(self._parameterNode.GetNodeReference("InputLabelMap"))
        print(self._parameterNode.GetNodeReference("InputAtlasStructure"))
        

        self._parameterNode.EndModify(wasModified)

    def onApplyButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):

            self.logic.process(self.ui.structureTreeWidget)

    def onUpdateButton(self):
        """
        Run processing when user clicks "Apply" button.
        """
        with slicer.util.tryWithErrorDisplay("Failed to compute results.", waitCursor=True):
            
            self.logic.updateStructureView(self.ui.atlasStructureInputPath.currentPath, self.ui.structureTreeWidget)


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

    
    qTreeWidgetItemsTop = qt.QTreeWidgetItem()

    # def getGroups(self, atlasStructureJSON):
    #     groups = []
    #     for item in atlasStructureJSON:
    #         if item['@type'] == "Group":
    #             groups.append([item['@id'], item['annotation']['name']])

    #     return groups
    
    # def getStructures(self, atlasStructureJSON):
    #     structures = []
    #     for item in atlasStructureJSON:
    #         if item['@type'] == "Structure":
    #             structures.append([item['@id'], item['annotation']['name']])

    #     return structures

    def buildTopHierarchy(self, InputStructurePath, qTreeWidgetItemsTop):
        """
        Build the hierarchy of the atlas.
        """
        import json

        defaultAtlasID = "#Brain_Atlas"
        atlasStructureJSON = json.load(open(InputStructurePath))

        groups = []
        for item in atlasStructureJSON:
            if item['@id'] == defaultAtlasID:
                qTreeWidgetItemsTop.setText(0, item['annotation']['name'])
                for member in item['member']:
                    groups.append(member)

        return groups
    
    def buildHierarchy(self, InputStructurePath, structureTreeWidget, groups):
        """
        Build the hierarchy of the atlas.
        """
        import json

        atlasStructureJSON = json.load(open(InputStructurePath))               

        for group in groups:
            for item in atlasStructureJSON:
                if item['@id'] == group:
                    child = qt.QTreeWidgetItem()
                    structureTreeWidget.addChild(child)
                    child.setText(0, item['annotation']['name'])
                    child.setFlags(child.flags() | qt.Qt.ItemIsTristate | qt.Qt.ItemIsUserCheckable)
                    child.setCheckState(0, qt.Qt.Unchecked)
                    if item['@type'] == "Group":
                        groups1 = []
                        for member in item['member']:
                            groups1.append(member)                     
                        self.buildHierarchy(InputStructurePath, child, groups1)

    def getCheckedItems(self):
        """
        Get the checked items of the structure view.
        """

        checked = dict()

        root = self.qTreeWidgetItemsTop
        signal_count = root.childCount()

        for i in range(signal_count):
            signal = root.child(i)
            checked_sweeps = list()
            num_children = signal.childCount()

            for n in range(num_children):
                child = signal.child(n)

                if child.checkState(0) == qt.Qt.Checked:
                    checked_sweeps.append(child.text(0))

            checked[signal.text(0)] = checked_sweeps

        return checked


    def updateStructureView(self, InputStructurePath, structureTreeWidget):
        """
        Update the structure view of the atlas.
        """
            
        # clear the tree
        structureTreeWidget.clear()
    
        # initiate the tree
        self.qTreeWidgetItemsTop = qt.QTreeWidgetItem(structureTreeWidget)
        self.qTreeWidgetItemsTop.setFlags(self.qTreeWidgetItemsTop.flags() | qt.Qt.ItemIsTristate | qt.Qt.ItemIsUserCheckable)

        # get the tree of the structure
        groups = self.buildTopHierarchy(InputStructurePath, self.qTreeWidgetItemsTop)
        self.buildHierarchy(InputStructurePath, self.qTreeWidgetItemsTop, groups)

        structureTreeWidget.expandToDepth(0)


    def process(self, structureTreeWidget):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        """

        checkedItems = self.getCheckedItems()
        print(checkedItems)
