import os
import re
import unittest
from unittest.runner import TextTestResult
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# OpenAnatomyExport
#

class OpenAnatomyExport(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "OpenAnatomy Export"
    self.parent.categories = ["OpenAnatomy"]
    self.parent.dependencies = []
    self.parent.contributors = ["Andras Lasso (PerkLab), Csaba Pinter (PerkLab)"]
    self.parent.helpText = """
Export model hierarchy or segmentation to OpenAnatomy-compatible glTF file.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
""" # replace with organization, grant and thanks.

#
# OpenAnatomyExportWidget
#

class OpenAnatomyExportWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = OpenAnatomyExportLogic()
    self.logic.logCallback = self.addLog

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/OpenAnatomyExport.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets
    self.ui.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.imageInputSelector.setMRMLScene(slicer.mrmlScene)

    # Connections
    self.ui.exportButton.connect('clicked(bool)', self.onExportButton)
    self.ui.inputSelector.connect("currentItemChanged(vtkIdType)", self.onSelect)
    self.ui.outputFormatSelector.connect("currentIndexChanged(int)", self.onSelect)

    self.ui.imageExportButton.connect('clicked(bool)', self.onImageExportButton)
    self.ui.imageInputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.imageOutputFormatSelector.connect("currentIndexChanged(int)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Export button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    currentItemId = self.ui.inputSelector.currentItem()
    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    owner = shNode.GetItemOwnerPluginName(currentItemId) if currentItemId else ""
    self.ui.exportButton.enabled = (owner == "Folder" or owner == "Segmentations")

    currentFormat = self.ui.outputFormatSelector.currentText
    self.ui.outputModelHierarchyLabel.visible = (currentFormat == "scene")
    self.ui.outputFileFolderSelector.visible = (currentFormat != "scene")

    self.ui.imageExportButton.enabled = self.ui.imageInputSelector.currentNode()

  def onExportButton(self):
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      self.ui.statusLabel.plainText = ''
      self.addLog('Exporting...')
      self.ui.outputFileFolderSelector.addCurrentPathToHistory()
      reductionFactor = self.ui.reductionFactorSliderWidget.value
      outputFormat = self.ui.outputFormatSelector.currentText
      outputFolder = self.ui.inputSelector.currentItem() if outputFormat == "models" else self.ui.outputFileFolderSelector.currentPath
      self.logic.exportModel(self.ui.inputSelector.currentItem(), outputFolder, reductionFactor, outputFormat)
      self.addLog('Export successful.')
    except Exception as e:
      self.addLog("Error: {0}".format(str(e)))
      import traceback
      traceback.print_exc()
      self.addLog('Export failed.')
    slicer.app.restoreOverrideCursor()

  def onImageExportButton(self):
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      self.ui.imageOutputFileFolderSelector.addCurrentPathToHistory()
      imageOutputFormat = self.ui.imageOutputFormatSelector.currentText
      imageOutputFolder = self.ui.imageOutputFileFolderSelector.currentPath
      self.logic.exportImage(self.ui.imageInputSelector.currentNode(), imageOutputFormat, imageOutputFolder)
      slicer.util.delayDisplay('Export successful.')
    except Exception as e:
      logging.error("Error: {0}".format(str(e)))
      import traceback
      traceback.print_exc()
      slicer.util.errorDisplay('Export failed. See application log for details.')
    slicer.app.restoreOverrideCursor()

  def addLog(self, text):
    """Append text to log window
    """
    self.ui.statusLabel.appendPlainText(text)
    slicer.app.processEvents() # force update

#
# OpenAnatomyExportLogic
#

class OpenAnatomyExportLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.logCallback = None
    self._exportToFile = True  # Save to files or just to the scene, normally on, maybe useful to turn off for debugging
    self.reductionFactor = 0.9

    # Slicer uses Gouraud lighting model by default, while glTF requires PBR.
    # Material properties conversion in VTK makes the model appear in glTF very dull, faded out,
    # therefore if we export models with Gouraud lighting we adjust the saturation and brightness.
    # By testing on a few anatomical atlases, saturation increase by 1.5x and no brightness
    # change seems to be working well.
    self.saturationBoost = 1.5
    self.brightnessBoost = 1.0

    self._outputShFolderItemId = None
    self._numberOfExpectedModels = 0
    self._numberOfProcessedModels = 0
    self._renderer = None
    self._renderWindow = None
    self._decimationParameterNode = None
    self._temporaryExportNodes = []  # temporary nodes used during exportModel
    self._gltfNodes = []
    self._gltfMeshes = []


  def addLog(self, text):
    logging.info(text)
    if self.logCallback:
      self.logCallback(text)


  def isValidInputOutputData(self, inputNode):
    """Validates if the output is not the same as input
    """
    if not inputNode:
      logging.debug('isValidInputOutputData failed: no input node defined')
      return False
    return True


  def exportModel(self, inputItem, outputFolder=None, reductionFactor=None, outputFormat=None):
    if outputFormat is None:
      outputFormat = "glTF"
    if reductionFactor is not None:
      self.reductionFactor = reductionFactor
    self._exportToFile = (outputFormat != "scene")
    if outputFolder is None:
      if self._exportToFile:
        raise ValueError("Output folder must be specified if output format is not 'scene'")

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
    inputName = shNode.GetItemName(inputItem)

    # Get input as a subject hierarchy folder
    owner = shNode.GetItemOwnerPluginName(inputItem)
    if owner == "Folder":
      # Input is already a model hiearachy
      inputShFolderItemId = inputItem
      self._outputShFolderItemId = shNode.CreateFolderItem(shNode.GetSceneItemID(), inputName + " export")
    elif owner == "Segmentations":
      # Export segmentation to model hierarchy
      segLogic = slicer.modules.segmentations.logic()
      folderName = inputName + '_Models'
      inputShFolderItemId = shNode.CreateFolderItem(shNode.GetSceneItemID(), folderName)
      inputSegmentationNode = shNode.GetItemDataNode(inputItem)
      self.addLog('Export segmentation to models. This may take a few minutes.')
      success = segLogic.ExportAllSegmentsToModels(inputSegmentationNode, inputShFolderItemId)

      self._outputShFolderItemId = inputShFolderItemId
    else:
      raise ValueError("Input item must be a segmentation node or a folder containing model nodes")

    modelNodes = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(inputShFolderItemId, modelNodes, "vtkMRMLModelNode")
    planeNodes = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(inputShFolderItemId, planeNodes, "vtkMRMLMarkupsPlaneNode")
    self._numberOfExpectedModels = modelNodes.GetNumberOfItems() + planeNodes.GetNumberOfItems()
    self._numberOfProcessedModels = 0
    self._gltfNodes = []
    self._gltfMeshes = []

    # Add models to a self._renderer
    self.addModelsToRenderer(inputShFolderItemId, boostGouraudColor = (outputFormat == "glTF"))

    if self._exportToFile:
      outputFileName = inputName
      # import datetime
      # dateTimeStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      # outputFileName += dateTimeStr
      outputFilePathBase = os.path.join(outputFolder, outputFileName)
      if outputFormat == "glTF":
        exporter = vtk.vtkGLTFExporter()
        outputFilePath = outputFilePathBase+'.gltf'
        exporter.SetFileName(outputFilePath)
        exporter.InlineDataOn()  # save to single file
        exporter.SaveNormalOn()  # save surface normals
      elif outputFormat == "OBJ":
        exporter = vtk.vtkOBJExporter()
        outputFilePath = outputFilePathBase + '.obj'
        exporter.SetFilePrefix(outputFilePathBase)
      else:
        raise ValueError("Output format must be scene, glTF, or OBJ")

      self.addLog(f"Writing file {outputFilePath}...")
      exporter.SetRenderWindow(self._renderWindow)
      exporter.Write()

      if outputFormat == "glTF":

        # Fix up the VTK-generated glTF file

        import json
        with open(outputFilePath, 'r') as f:
          jsonData = json.load(f)

        # Update mesh names
        for meshIndex, mesh in enumerate(self._gltfMeshes):
          jsonData['meshes'][meshIndex]['name'] = mesh['name']

        # VTK uses "OPAQUE" alpha mode for all meshes, which would make all nodes appear opaque.
        # Replace alpha mode by "BLEND" for semi-transparent meshes.
        for material in jsonData['materials']:
          rgbaColor = material['pbrMetallicRoughness']['baseColorFactor']
          if rgbaColor[3] < 1.0:
            material['alphaMode'] = 'BLEND'

        # Add camera nodes from the VTK-exported file
        for node in enumerate(self._gltfNodes):
          if 'camera' in node:
            self._gltfNodes.append(node)

        # Replace the entire hierarchy
        jsonData['nodes'] = self._gltfNodes

        # Set up root node
        rootNodeIndex = len(self._gltfNodes)-1

        # According to glTF specifications (3.4. Coordinate System and Units
        # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#coordinate-system-and-units):
        #
        #   glTF uses a right-handed coordinate system. glTF defines +Y as up, +Z as forward, and -X as right; the front of a glTF asset faces +Z.
        #   The units for all linear distances are meters.

        # View up direction in glTF is +Y.
        # We map that to anatomical S direction by this transform (from LPS to LSA coordinate system).

        # Default coordinate system unit in Slicer is millimeters, therefore we need to scale the model
        # from the scene's length unit. Currently only "mm" and "m" units are supported.
        selectionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLSelectionNodeSingleton")
        unitNode = slicer.mrmlScene.GetNodeByID(selectionNode.GetUnitNodeID("length"))
        lengthUnitSuffix = unitNode.GetSuffix()
        if lengthUnitSuffix == "mm":
          scaleToMeters = 0.001
        elif lengthUnitSuffix == "m":
          scaleToMeters = 1.0
        else:
          msg = f"Unsupported length unit ({lengthUnitSuffix}). Exported glTF file will not be scaled to meters!"
          self.addLog(msg)
          logging.warning(msg)
          scaleToMeters = 1.0

        # Transform from LPS coordinate system (in millimeters) to LSA coordinate system (in meters)
        jsonData['nodes'][rootNodeIndex]['matrix'] = [
            scaleToMeters,    0.0,    0.0,    0.0,
            0.0,    0.0,   -scaleToMeters,    0.0,
            0.0,    scaleToMeters,    0.0,    0.0,
            0.0,    0.0,    0.0,    1.0
            ]

        # The scene root is the last node in the self._gltfNodes list
        jsonData['scenes'][0]['nodes'] = [rootNodeIndex]

        jsonData['asset']['generator'] = f"{slicer.app.applicationName} {slicer.app.applicationVersion}"

        with open(outputFilePath, 'w') as f:
          f.write(json.dumps(jsonData, indent=3))

        # TODO:
        # - Add scene view states as scenes
        # - Add option to change up vector (glTF defines the y axis as up, https://github.com/KhronosGroup/glTF/issues/1043
        #   https://castle-engine.io/manual_up.php)

    # # Preview
    # iren = vtk.vtkRenderWindowInteractor()
    # iren.SetRenderWindow(renderWindow)
    # iren.Initialize()
    # renderer.ResetCamera()
    # renderer.GetActiveCamera().Zoom(1.5)
    # renderWindow.Render()
    # iren.Start()

    # Remove temporary nodes
    for node in self._temporaryExportNodes:
      slicer.mrmlScene.RemoveNode(node)
    self._temporaryExportNodes = []

    self._numberOfExpectedModels = 0
    self._numberOfProcessedModels = 0
    self._renderer = None
    self._renderWindow = None
    self._decimationParameterNode = None

    if self._exportToFile:
      shNode.RemoveItem(self._outputShFolderItemId)

  def exportImage(self, volumeNode, outputFormat, outputFolder):
    writer=vtk.vtkXMLImageDataWriter()
    writer.SetFileName("{0}/{1}.vti".format(outputFolder, volumeNode.GetName()))
    writer.SetInputData(volumeNode.GetImageData())
    writer.SetCompressorTypeToZLib()
    writer.Write()


  def addModelsToRenderer(self, shFolderItemId, boostGouraudColor=False):
    if not shFolderItemId:
      raise ValueError("Subject hierarchy folder does not exist.")

    gltfFolderNodeChildren = []  # gltf node indices of these item's children

    if self._exportToFile:
      if not self._renderer:
        self._renderer = vtk.vtkRenderer()
      if not self._renderWindow:
        self._renderWindow = vtk.vtkRenderWindow()
        self._renderWindow.AddRenderer(self._renderer)

    slicer.app.pauseRender()
    try:

      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      folderName = shNode.GetItemName(shFolderItemId)
      self.addLog(f"Writing {folderName}...")

      # Write all children of this item (recursively)
      childIds = vtk.vtkIdList()
      shNode.GetItemChildren(shFolderItemId, childIds)
      for itemIdIndex in range(childIds.GetNumberOfIds()):
        shItemId = childIds.GetId(itemIdIndex)
        dataNode = shNode.GetItemDataNode(shItemId)
        dataNotNone = dataNode is not None
        isModel = dataNotNone and dataNode.IsA("vtkMRMLModelNode")
        isMarkupsPlane = dataNotNone and dataNode.IsA("vtkMRMLMarkupsPlaneNode")
        dataIsValid = (isModel or isMarkupsPlane)
        if dataIsValid:
          if dataNode.IsA("vtkMRMLModelNode"):
            inputModelNode = dataNode
          else:
            inputModelNode = self.createPlaneModelFromMarkupsPlane(dataNode)
          meshName = dataNode.GetName()
          self._numberOfProcessedModels += 1
          self.addLog("Model {0}/{1}: {2}".format(self._numberOfProcessedModels, self._numberOfExpectedModels, meshName))

          # Reuse existing model node if already exists
          existingOutputModelItemId = shNode.GetItemChildWithName(self._outputShFolderItemId, inputModelNode.GetName())
          if existingOutputModelItemId:
            outputModelNode = shNode.GetItemDataNode(existingOutputModelItemId)
          else:
            outputModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            outputModelNode.CreateDefaultDisplayNodes()
            outputModelNode.SetName(inputModelNode.GetName())
            outputModelNode.GetDisplayNode().CopyContent(inputModelNode.GetDisplayNode())
            if self._exportToFile:
              self._temporaryExportNodes.append(outputModelNode)

          if self.addModelToRenderer(inputModelNode, outputModelNode, boostGouraudColor):

            # Convert atlas model names (such as 'Model_505_left_lateral_geniculate_body') to simple names
            # by stripping the prefix and converting underscore to space.
            match = re.match(r'^Model_[0-9]+_(.+)', meshName)
            if match:
              meshName = match.groups()[0].replace('_', ' ')

            gltfMeshIndex = len(self._gltfMeshes)
            self._gltfMeshes.append({'name': meshName})
            gltfMeshNodeIndex = len(self._gltfNodes)
            self._gltfNodes.append({'mesh': gltfMeshIndex, 'name': meshName})
            gltfFolderNodeChildren.append(gltfMeshNodeIndex)

          if dataNode and dataNode.IsA("vtkMRMLMarkupsPlaneNode"):
            slicer.mrmlScene.RemoveNode(inputModelNode)

        # Write all children of this child item
        grandChildIds = vtk.vtkIdList()
        shNode.GetItemChildren(shItemId, grandChildIds)
        if grandChildIds.GetNumberOfIds() > 0:
          self.addModelsToRenderer(shItemId, boostGouraudColor)
          # added highest-level parent folder is the last node
          gltfFolderNodeIndex = len(self._gltfNodes)-1
          gltfFolderNodeChildren.append(gltfFolderNodeIndex)

      # Processed all items in the folder, now save the folder information
      self._gltfNodes.append({'name': folderName, 'children': gltfFolderNodeChildren})

    finally:
      slicer.app.resumeRender()


  def addModelToRenderer(self, inputModelNode, outputModelNode, boostGouraudColor=False):
    '''Update output model in the scene and if valid add to self._renderer.
    :return: True if an actor is added to the renderer.
    '''
    decimation = slicer.modules.decimation
    if not self._decimationParameterNode:
      self._decimationParameterNode = slicer.modules.decimation.logic().CreateNodeInScene()
      self._decimationParameterNode.SetParameterAsFloat("reductionFactor", self.reductionFactor)
      self._temporaryExportNodes.append(self._decimationParameterNode)

    # Quadric decimation
    #
    # Models with very small number of points are not decimated, as the memory saving is
    # negligible and the models may become severely distorted.
    #
    # Models that contain lines or vertices are not decimated either because the current
    # quadric decimation implementation would remove vertices and lines.

    if ((self.reductionFactor == 0.0) or (inputModelNode.GetPolyData().GetNumberOfPoints() < 50)
        or (inputModelNode.GetPolyData().GetLines().GetNumberOfCells() > 0)
        or (inputModelNode.GetPolyData().GetVerts().GetNumberOfCells() > 0)):

      # Skip decimation
      outputModelNode.CopyContent(inputModelNode)

    else:

      # Temporary workaround (part 1/2):
      # VTK 9.0 OBJ writer creates invalid OBJ file if there are triangle
      # strips and normals but no texture coords.
      # As a workaround, temporarily remove point normals in this case.
      # This workaround can be removed when Slicer's VTK includes this fix:
      # https://gitlab.kitware.com/vtk/vtk/-/merge_requests/8747
      if (inputModelNode.GetPolyData().GetNumberOfStrips() > 0
          and inputModelNode.GetPolyData().GetPointData()
          and inputModelNode.GetPolyData().GetPointData().GetNormals()
          and not inputModelNode.GetPolyData().GetPointData().GetTCoords()):
        # Save original normals and temporarily remove normals
        originalNormals = inputModelNode.GetPolyData().GetPointData().GetNormals()
        inputModelNode.GetPolyData().GetPointData().SetNormals(None)
      else:
        originalNormals = None

      self._decimationParameterNode.SetParameterAsNode("inputModel", inputModelNode)
      self._decimationParameterNode.SetParameterAsNode("outputModel", outputModelNode)
      slicer.cli.runSync(decimation, self._decimationParameterNode)

      # Temporary workaround (part 2/2):
      # Restore original normals.
      if originalNormals:
        inputModelNode.GetPolyData().GetPointData().SetNormals(originalNormals)

    # Compute normals
    decimatedNormals = vtk.vtkPolyDataNormals()
    decimatedNormals.SetInputData(outputModelNode.GetPolyData())
    decimatedNormals.SplittingOff()
    decimatedNormals.Update()
    outputPolyData = decimatedNormals.GetOutput()

    if outputPolyData.GetNumberOfPoints()==0 or outputPolyData.GetNumberOfCells()==0:
      self.addLog("  Warning: empty model, not exported.")
      return False

    if not self._exportToFile:
      return True

    # Normal array name is hardcoded into glTF exporter to "NORMAL".
    normalArray = outputPolyData.GetPointData().GetNormals()
    if normalArray is not None:  # polylines and vertices do not have normals
      normalArray.SetName("NORMAL")
    outputModelNode.SetAndObservePolyData(outputPolyData)

    ras2lps = vtk.vtkMatrix4x4()
    ras2lps.SetElement(0,0,-1)
    ras2lps.SetElement(1,1,-1)
    ras2lpsTransform = vtk.vtkTransform()
    ras2lpsTransform.SetMatrix(ras2lps)
    transformer = vtk.vtkTransformPolyDataFilter()
    transformer.SetTransform(ras2lpsTransform)
    transformer.SetInputConnection(outputModelNode.GetPolyDataConnection())

    actor = vtk.vtkActor()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(transformer.GetOutputPort())
    actor.SetMapper(mapper)
    displayNode = outputModelNode.GetDisplayNode()

    colorRGB = displayNode.GetColor()
    if displayNode.GetInterpolation() == slicer.vtkMRMLDisplayNode.PBRInterpolation:
      actor.GetProperty().SetColor(colorRGB[0], colorRGB[1], colorRGB[2])
      actor.GetProperty().SetInterpolationToPBR()
      actor.GetProperty().SetMetallic(displayNode.GetMetallic())
      actor.GetProperty().SetRoughness(displayNode.GetRoughness())
    else:
      if boostGouraudColor:
        bf = colorRGB
        colorHSV = [0, 0, 0]
        vtk.vtkMath.RGBToHSV(colorRGB, colorHSV)
        colorHSV[1] = min(colorHSV[1] * self.saturationBoost, 1.0)  # increase saturation
        colorHSV[2] = min(colorHSV[2] * self.brightnessBoost, 1.0)  # increase brightness
        colorRGB = [0, 0, 0]
        vtk.vtkMath.HSVToRGB(colorHSV, colorRGB)
      actor.GetProperty().SetColor(colorRGB[0], colorRGB[1], colorRGB[2])
      actor.GetProperty().SetInterpolationToGouraud()
      actor.GetProperty().SetAmbient(displayNode.GetAmbient())
      actor.GetProperty().SetDiffuse(displayNode.GetDiffuse())
      actor.GetProperty().SetSpecular(displayNode.GetSpecular())
      actor.GetProperty().SetSpecularPower(displayNode.GetPower())

    actor.GetProperty().SetOpacity(displayNode.GetOpacity())
    self._renderer.AddActor(actor)

    return True

  def createPlaneModelFromMarkupsPlane(self,planeMarkup):
    planeBounds = planeMarkup.GetPlaneBounds()
    objectToWorld = vtk.vtkMatrix4x4()
    planeMarkup.GetObjectToWorldMatrix(objectToWorld)

    # Create plane polydata
    planeSource = vtk.vtkPlaneSource()
    planeSource.SetOrigin(objectToWorld.MultiplyPoint([planeBounds[0], planeBounds[2], 0.0, 1.0])[0:3])
    planeSource.SetPoint1(objectToWorld.MultiplyPoint([planeBounds[1], planeBounds[2], 0.0, 1.0])[0:3])
    planeSource.SetPoint2(objectToWorld.MultiplyPoint([planeBounds[0], planeBounds[3], 0.0, 1.0])[0:3])
    planeModel = slicer.modules.models.logic().AddModel(planeSource.GetOutputPort())

    # Copy props from markups to model
    planeMarkupDisplayNode = planeMarkup.GetDisplayNode()
    planeModelDisplayNode = planeModel.GetDisplayNode()
    planeModelDisplayNode.SetColor(planeMarkupDisplayNode.GetSelectedColor())
    planeOpacity = planeMarkupDisplayNode.GetFillOpacity()
    planeModelDisplayNode.SetOpacity(planeOpacity)
    planeModel.SetName(planeMarkup.GetName())

    return planeModel

class OpenAnatomyExportTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_OpenAnatomyExport1()

  def test_OpenAnatomyExport1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    SampleData.downloadFromURL(
      nodeNames='FA',
      fileNames='FA.nrrd',
      uris='http://slicer.kitware.com/midas3/download?items=5767',
      checksums='SHA256:12d17fba4f2e1f1a843f0757366f28c3f3e1a8bb38836f0de2a32bb1cd476560')
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = OpenAnatomyExportLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
