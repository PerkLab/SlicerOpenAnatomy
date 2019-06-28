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

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/OpenAnatomyExport.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    self.ui.inputSelector.setMRMLScene(slicer.mrmlScene)

    # Connections
    self.ui.exportButton.connect('clicked(bool)', self.onExportButton)
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Export button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.ui.exportButton.enabled = self.ui.inputSelector.currentNode()

  def onExportButton(self):
    logic = OpenAnatomyExportLogic()
    reductionFactor = self.ui.reductionFactorSliderWidget.value
    outputFolder = self.ui.folderSelectorButton.directory
    logic.run(self.ui.inputSelector.currentNode(), reductionFactor, outputFolder)

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

  def isValidInputOutputData(self, inputNode):
    """Validates if the output is not the same as input
    """
    if not inputNode:
      logging.debug('isValidInputOutputData failed: no input node defined')
      return False
    return True

  def run(self, inputNode, reductionFactor, outputFolder):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputNode):
      slicer.util.errorDisplay('Invalid input')
      return False

    import datetime
    dateTimeStr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    outputFileName = dateTimeStr + "_SlicerScene.gltf"
    outputFilePath = os.path.join(outputFolder, outputFileName)

    allModelNodes = slicer.util.getNodesByClass("vtkMRMLModelNode")
    modelNodes = []
    for modelNode in allModelNodes:
      if "Volume Slice" in modelNode.GetName():
        continue
      modelNodes.append(modelNode)

    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)

    for modelNode in modelNodes:
      mapper = vtk.vtkPolyDataMapper()
      if reductionFactor == 0.0:
        mapper.SetInputConnection(modelNode.GetPolyDataConnection())
      else:
        deci = vtk.vtkDecimatePro()
        deci.SetInputConnection(modelNode.GetPolyDataConnection())
        deci.SetTargetReduction(reductionFactor)
        deci.PreserveTopologyOn()
        decimatedNormals = vtk.vtkPolyDataNormals()
        decimatedNormals.SetInputConnection(deci.GetOutputPort())
        decimatedNormals.SplittingOff()
        mapper.SetInputConnection(decimatedNormals.GetOutputPort())
      actor = vtk.vtkActor()
      actor.SetMapper(mapper)
      displayNode = modelNode.GetDisplayNode()
      color = displayNode.GetColor()
      actor.GetProperty().SetColor(color[0], color[1], color[2])
      actor.GetProperty().SetSpecularPower(3.0)
      actor.GetProperty().SetOpacity(displayNode.GetOpacity())
      renderer.AddActor(actor)

    exporter=slicer.vtkGLTFExporter()
    exporter.SetRenderWindow(renderWindow)
    exporter.SetFileName(outputFilePath)
    exporter.InlineDataOn() # save to single file
    exporter.Write()

    # # Preview
    # iren = vtk.vtkRenderWindowInteractor()
    # iren.SetRenderWindow(renderWindow)
    # iren.Initialize()
    # renderer.ResetCamera()
    # renderer.GetActiveCamera().Zoom(1.5)
    # renderWindow.Render()
    # iren.Start()

    return True


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
