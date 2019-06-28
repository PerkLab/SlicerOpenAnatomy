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
    self.parent.contributors = ["Andras Lasso (PerkLab)"]
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
    self.ui.outputSelector.setMRMLScene(slicer.mrmlScene)

    # connections
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.ui.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.ui.applyButton.enabled = self.ui.inputSelector.currentNode() and self.ui.outputSelector.currentNode()

  def onApplyButton(self):
    logic = OpenAnatomyExportLogic()
    enableScreenshotsFlag = self.ui.enableScreenshotsFlagCheckBox.checked
    imageThreshold = self.ui.imageThresholdSliderWidget.value
    logic.run(self.ui.inputSelector.currentNode(), self.ui.outputSelector.currentNode(), imageThreshold, enableScreenshotsFlag)

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

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def run(self, inputVolume, outputVolume, imageThreshold, enableScreenshots=0):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputVolume):
      slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
      return False

    logging.info('Processing started')

    # Compute the thresholded output volume using the Threshold Scalar Volume CLI module
    cliParams = {'InputVolume': inputVolume.GetID(), 'OutputVolume': outputVolume.GetID(), 'ThresholdValue' : imageThreshold, 'ThresholdType' : 'Above'}
    cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True)

    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('OpenAnatomyExportTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

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




# outputFileName = r"c:\Users\andra\OneDrive\Projects\OpenAnatomy\20190627-GltfExport\babacar-inline-dec60.gltf"
# decimationFactor = 0.8

# allModelNodes = slicer.util.getNodesByClass("vtkMRMLModelNode")
# modelNodes = []
# for modelNode in allModelNodes:
#   if "Volume Slice" in modelNode.GetName():
#     continue
#   modelNodes.append(modelNode)

# renderer = vtk.vtkRenderer()
# renderWindow = vtk.vtkRenderWindow()
# renderWindow.AddRenderer(renderer)

# for modelNode in modelNodes:
#   mapper = vtk.vtkPolyDataMapper()
#   if decimationFactor == 0.0:
#     mapper.SetInputConnection(modelNode.GetPolyDataConnection())
#   else:
#     deci = vtk.vtkDecimatePro()
#     deci.SetInputConnection(modelNode.GetPolyDataConnection())
#     deci.SetTargetReduction(decimationFactor)
#     deci.PreserveTopologyOn()
#     decimatedNormals = vtk.vtkPolyDataNormals()
#     decimatedNormals.SetInputConnection(deci.GetOutputPort())
#     decimatedNormals.SplittingOff()
#     mapper.SetInputConnection(decimatedNormals.GetOutputPort())
#   actor = vtk.vtkActor()
#   actor.SetMapper(mapper)
#   displayNode = modelNode.GetDisplayNode()
#   color = displayNode.GetColor()
#   actor.GetProperty().SetColor(color[0], color[1], color[2]);
#   actor.GetProperty().SetSpecularPower(3.0)
#   actor.GetProperty().SetOpacity(displayNode.GetOpacity())
#   renderer.AddActor(actor)

# exporter=slicer.vtkGLTFExporter()
# exporter.SetRenderWindow(renderWindow)
# exporter.SetFileName(outputFileName)
# exporter.InlineDataOn() # save to single file
# exporter.Write()

# # # Preview
# # iren = vtk.vtkRenderWindowInteractor()
# # iren.SetRenderWindow(renderWindow)
# # iren.Initialize()
# # renderer.ResetCamera()
# # renderer.GetActiveCamera().Zoom(1.5)
# # renderWindow.Render()
# # iren.Start()
