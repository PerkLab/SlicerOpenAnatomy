import os
import unittest
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

    self.ui.inputSelector.setMRMLScene(slicer.mrmlScene)
    self.ui.inputSelector.setNodeTypes(["vtkMRMLSegmentationNode"])

    # Connections
    self.ui.exportButton.connect('clicked(bool)', self.onExportButton)
    self.ui.inputSelector.connect("currentItemChanged(vtkIdType)", self.onSelect)
    self.ui.outputFormatSelector.connect("currentIndexChanged(int)", self.onSelect)

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

  def onExportButton(self):
    slicer.app.setOverrideCursor(qt.Qt.WaitCursor)
    try:
      self.ui.statusLabel.plainText = ''
      self.addLog('Exporting...')
      self.ui.outputFileFolderSelector.addCurrentPathToHistory()
      reductionFactor = self.ui.reductionFactorSliderWidget.value
      outputFormat = self.ui.outputFormatSelector.currentText
      outputFolder = self.ui.inputSelector.currentItem() if outputFormat == "models" else self.ui.outputFileFolderSelector.currentPath
      self.logic.run(self.ui.inputSelector.currentItem(), reductionFactor, outputFormat, outputFolder)
      self.addLog('Export successful.')
    except Exception as e:
      self.addLog("Error: {0}".format(str(e)))
      import traceback
      traceback.print_exc()
      self.addLog('Export failed.')
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

  def run(self, inputItem, reductionFactor, outputFormat, outputFolder):
    """
    Run the actual algorithm
    """

    exportToFile = (outputFormat != "scene")

    shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)

    inputName = shNode.GetItemName(inputItem)

    owner = shNode.GetItemOwnerPluginName(inputItem)
    if owner == "Folder":
      # Input is already a model hiearachy
      inputShFolderItemId = inputItem
      outputShFolderItemId = shNode.CreateFolderItem(shNode.GetSceneItemID(), inputName + " export")
    elif owner == "Segmentations":
      # Export segmentation to model hierarchy
      segLogic = slicer.modules.segmentations.logic()
      folderName = inputName + '_Models'
      inputShFolderItemId = shNode.CreateFolderItem(shNode.GetSceneItemID(), folderName)
      inputSegmentationNode = shNode.GetItemDataNode(inputItem)
      self.addLog('Export segmentation to models. This may take a few minutes.')
      success = segLogic.ExportAllSegmentsToModels(inputSegmentationNode, inputShFolderItemId)

      outputShFolderItemId = inputShFolderItemId
    else:
      raise ValueError("Input item must be a segmentation node or a folder containing model nodes")

    inputNodes = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(inputItem, inputNodes, "vtkMRMLModelNode")

    if exportToFile:
      renderer = vtk.vtkRenderer()
      renderWindow = vtk.vtkRenderWindow()
      renderWindow.AddRenderer(renderer)

    decimation = slicer.modules.decimation
    decimationParameterNode = slicer.modules.decimation.logic().CreateNodeInScene()
    decimationParameterNode.SetParameterAsFloat("reductionFactor", reductionFactor)

    nodesToDelete = []
    nodesToDelete.append(decimationParameterNode)

    modelNodes = vtk.vtkCollection()
    shNode.GetDataNodesInBranch(inputShFolderItemId, modelNodes, "vtkMRMLModelNode")
    for modelNodeIndex in range(modelNodes.GetNumberOfItems()):
      inputModelNode = modelNodes.GetItemAsObject(modelNodeIndex)

      self.addLog("Model {0}/{1}: {2}".format(modelNodeIndex+1, modelNodes.GetNumberOfItems(), inputModelNode.GetName()))
      slicer.app.processEvents()

      existingOutputModelItemId = shNode.GetItemChildWithName(outputShFolderItemId, inputModelNode.GetName())
      if existingOutputModelItemId:
        outputModelNode = shNode.GetItemDataNode(existingOutputModelItemId)
      else:
        outputModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        outputModelNode.CreateDefaultDisplayNodes()
        outputModelNode.SetName(inputModelNode.GetName())
        outputModelNode.GetDisplayNode().CopyContent(inputModelNode.GetDisplayNode())
        if exportToFile:
          nodesToDelete.append(outputModelNode)

      # Quadric decimation
      if reductionFactor == 0.0:
        outputModelNode.CopyContent(inputModelNode)
      else:
        decimationParameterNode.SetParameterAsNode("inputModel", inputModelNode)
        decimationParameterNode.SetParameterAsNode("outputModel", outputModelNode)
        slicer.cli.runSync(decimation, decimationParameterNode)

      # Compute normals
      decimatedNormals = vtk.vtkPolyDataNormals()
      decimatedNormals.SetInputData(outputModelNode.GetPolyData())
      decimatedNormals.SplittingOff()
      decimatedNormals.Update()
      outputModelNode.SetAndObservePolyData(decimatedNormals.GetOutput())

      outputPolyData = outputModelNode.GetPolyData()
      if outputPolyData.GetNumberOfPoints()==0 or outputPolyData.GetNumberOfCells()==0:
        self.addLog("  Warning: empty model, not exported.")
        continue

      if exportToFile:

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
        color = displayNode.GetColor()
        ambient = 0.1
        diffuse = 0.9
        specular = 0.2
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        actor.GetProperty().SetAmbientColor(ambient * color[0], ambient * color[1], ambient * color[2])
        actor.GetProperty().SetDiffuseColor(diffuse * color[0], diffuse * color[1], diffuse * color[2])
        actor.GetProperty().SetSpecularColor(specular * color[0], specular * color[1], specular * color[2])
        actor.GetProperty().SetSpecularPower(3.0)
        actor.GetProperty().SetOpacity(displayNode.GetOpacity())
        renderer.AddActor(actor)

    if exportToFile:
      outputFileName = inputName
      # import datetime
      # dateTimeStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      # outputFileName += dateTimeStr
      outputFilePathBase = os.path.join(outputFolder, outputFileName)
      if outputFormat == "glTF":
        exporter = slicer.vtkGLTFExporter()
        exporter.SetFileName(outputFilePathBase+'.gltf')
        exporter.InlineDataOn() # save to single file
      elif outputFormat == "OBJ":
        exporter = vtk.vtkOBJExporter()
        exporter.SetFilePrefix(outputFilePathBase)
      else:
        raise ValueError("Output format must be scene, glTF, or OBJ")
      exporter.SetRenderWindow(renderWindow)
      exporter.Write()

    # # Preview
    # iren = vtk.vtkRenderWindowInteractor()
    # iren.SetRenderWindow(renderWindow)
    # iren.Initialize()
    # renderer.ResetCamera()
    # renderer.GetActiveCamera().Zoom(1.5)
    # renderWindow.Render()
    # iren.Start()

    # Remove temporary nodes
    for node in nodesToDelete:
      slicer.mrmlScene.RemoveNode(node)

    if exportToFile:
      shNode.RemoveItem(outputShFolderItemId)


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
