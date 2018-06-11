import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import platform
import subprocess
import threading
from os.path import expanduser
import SimpleITK as sitk
import sitkUtils
#
# DockerVesselSeg
#

class DockerVesselSeg(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "DockerVesselSeg" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# DockerVesselSegWidget
#

class DockerVesselSegWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...


    self.dockerGroupBox = ctk.ctkCollapsibleGroupBox()
    self.dockerGroupBox.setTitle('Docker Settings')
    self.layout.addWidget(self.dockerGroupBox)
    dockerForm = qt.QFormLayout(self.dockerGroupBox)
    self.dockerPath = ctk.ctkPathLineEdit()
    # self.dockerPath.setMaximumWidth(300)
    if platform.system() == 'Darwin':
      self.dockerPath.setCurrentPath('/usr/local/bin/docker')
    if platform.system() == 'Linux':
      self.dockerPath.setCurrentPath('/usr/bin/docker')
    if platform.system() == 'Windows':
      self.dockerPath.setCurrentPath("C:/Program Files/Docker/Docker/resources/bin/docker.exe")

    ### use nvidia-docker if it is installed
    nvidiaDockerPath = self.dockerPath.currentPath.replace('bin/docker', 'bin/nvidia-docker')
    if os.path.isfile(nvidiaDockerPath):
      self.dockerPath.setCurrentPath(nvidiaDockerPath)

    self.downloadButton = qt.QPushButton('Download')
    self.downloadButton.connect('clicked(bool)', self.onDownloadButton)
    dockerForm.addRow("Docker Executable Path:", self.dockerPath)
    dockerForm.addRow("Download the docker image:", self.downloadButton)
    self.progressDownload = qt.QProgressBar()
    self.progressDownload.setRange(0, 100)
    self.progressDownload.setValue(0)
    self.progressDownload.hide()

    self.dockerVolumePath = ctk.ctkPathLineEdit()
    defaultVolumePath = os.path.join(expanduser("~"), ".dockerVolume")
    if not os.path.exists(defaultVolumePath):
      os.makedirs(defaultVolumePath)
    self.dockerVolumePath.setCurrentPath(defaultVolumePath)
    dockerForm.addRow("Docker Volume Directory:", self.dockerVolumePath)


    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showHidden = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Input Volume: ", self.inputSelector)

    #
    # output vessel model selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )
    parametersFormLayout.addRow("Output vessel model: ", self.outputSelector)

    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    self.logic = DockerVesselSegLogic()

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onReload(self,moduleName="DockerVesselSeg"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    self.logic.clear()
    globals()[moduleName] = slicer.util.reloadScriptedModule(moduleName)

  def onSelect(self):
    self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

  def onDownloadButton(self):
    resoponse = qt.QMessageBox.question(None, "Download", "The size of the selected image to download is 590 MB. Are you sure you want to proceed?", qt.QMessageBox.Yes, qt.QMessageBox.No) == qt.QMessageBox.Yes
    if resoponse:
      cmd = []
      cmd.append(self.dockerPath.currentPath)
      cmd.append('pull')
      cmd.append("li3igtlab/brain-vessel-seg" + '@' + "sha256:2095141606837f364a857ec90a19efe49f8879918881a24a4cf0e72c74a2c2d2")
      p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
      print(cmd)
      parts = dict()
      try:
        while True:
          self.progressDownload.show()
          slicer.app.processEvents()
          line = p.stdout.readline()
          if not line:
            break
          line = line.rstrip()
          print(line)
          part = line.split(':')[0]
          if len(part) == 12:
            parts[part] = line.split(':')[1]
          if parts.keys():
            print('-' * 100)
            print(parts)
            n_parts = len(parts.keys())
            n_completed = len([status for status in parts.values() if status == ' Pull complete'])
            self.progressDownload.setValue(int((100 * n_completed) / n_parts))

      except Exception as e:
        print("Exception: {}".format(e))
      print(parts)
      self.progressDownload.setValue(0)
      self.progressDownload.hide()
    else:
      print("Download was canceled!")


  def onApplyButton(self):
    self.logic.run(self.dockerPath.currentPath, self.dockerVolumePath.currentPath, self.inputSelector.currentNode(), self.outputSelector.currentNode())

#
# DockerVesselSegLogic
#

class DockerVesselSegLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  DOCKERVOLUMEDIMENSION = [512.0,192.0,128.0]
  def __init__(self):
    self.resampledVolume = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    slicer.mrmlScene.AddNode(self.resampledVolume)

  def clear(self):
    if self.resampledVolume:
      slicer.mrmlScene.RemoveNode(self.resampledVolume.GetDisplayNode())
      slicer.mrmlScene.RemoveNode(self.resampledVolume)
      self.resampledVolume = None

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

  def isValidInputOutputData(self, inputVolumeNode, outputModel):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputModel:
      logging.debug('isValidInputOutputData failed: no output vessel model node defined')
      return False
    return True

  def run(self, dockerPath, dockerVolumePath, inputVolume, outputModel):
    """
    Run the actual algorithm
    """

    if not self.isValidInputOutputData(inputVolume, outputModel):
      slicer.util.errorDisplay('Input volume is the same as output vessel model. Choose a different output vessel model.')
      return False
    slicer.app.processEvents()
    fileList = os.listdir(dockerVolumePath)
    for fileName in fileList:
      os.remove(os.path.join(dockerVolumePath, fileName))
    parameters = {}
    parameters["InputVolume"] = inputVolume.GetID()
    inputVolumeDim = inputVolume.GetImageData().GetDimensions()
    inputVolumeSpacing = inputVolume.GetSpacing()
    parameters["outputPixelSpacing"] = "%.5f,%.5f,%.5f"%(inputVolumeSpacing[0]*inputVolumeDim[0]/self.DOCKERVOLUMEDIMENSION[0], \
                                                         inputVolumeSpacing[1]*inputVolumeDim[1]/self.DOCKERVOLUMEDIMENSION[1], \
                                                         inputVolumeSpacing[2]*inputVolumeDim[2]/self.DOCKERVOLUMEDIMENSION[2])
    parameters["OutputVolume"]= self.resampledVolume.GetID()
    resampleModule = slicer.modules.resamplescalarvolume
    slicer.cli.run(resampleModule, None, parameters, wait_for_completion=True)
    slicer.app.processEvents()
    img = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(self.resampledVolume.GetName()))
    fileName = "quarterVolume.nii.gz"
    sitk.WriteImage(img, str(os.path.join(dockerVolumePath, fileName)))
    #-----------------------------------

    logging.info('Processing started')
    cmd = list()
    cmd.append(dockerPath)
    cmd.extend(('run', '-t', '-v'))
    cmd.append(str(dockerVolumePath) + ':' + "/workspace/data/Case1")
    cmd.append('li3igtlab/brain-vessel-seg@sha256:2095141606837f364a857ec90a19efe49f8879918881a24a4cf0e72c74a2c2d2')
    cmd.extend(('python3', '/workspace/NiftyNet/net_run.py', 'inference'))
    cmd.extend(('-a', 'brainVesselSegApp.brainVesselSegApp', '-c', '/workspace/data/vesselSeg.ini'))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    print cmd
    progress = 0
    while True:
      progress += 0.15
      slicer.app.processEvents()
      line = p.stdout.readline()
      if not line:
        print "no line"
        break
      print(line)
    #outputImage = sitk.ReadImage(os.path.join(dockerVolumePath, "Case1__niftynet_out.nii.gz"))
    #sitkUtils.PushToSlicer(outputImage, "niftyOutput", 0, True)
    imageCollection = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLScalarVolumeNode", "niftyOutput")
    if imageCollection:
      niftyOutputNode = imageCollection.GetItemAsObject(0)
      if niftyOutputNode:
        matrix = vtk.vtkMatrix4x4()
        inputVolume.GetIJKToRASMatrix(matrix)
        niftyOutputNode.SetIJKToRASMatrix(matrix)
        # croppedImage = slicer.mrmlScene.GetNodeByID("vtkMRMLScalarVolumeNode1")
        invertedImage = self.inverseVTKImage(niftyOutputNode.GetImageData())
        slicer.mrmlScene.AddNode(invertedImage)
        invertedImage.SetIJKToRASMatrix(matrix)
        parameters = {}
        parameters["InputVolume"] = invertedImage.GetID()
        parameters["Threshold"] = 0.9
        parameters["OutputGeometry"] = outputModel.GetID()
        grayMaker = slicer.modules.grayscalemodelmaker
        slicer.cli.run(grayMaker, None, parameters, wait_for_completion=True)

    logging.info('Processing completed')

    return True

  def inverseVTKImage(self, inputImageData):
    imgvtk = vtk.vtkImageData()
    imgvtk.DeepCopy(inputImageData)
    imgvtk.GetPointData().GetScalars().FillComponent(0, 1)
    subtractFilter = vtk.vtkImageMathematics()
    subtractFilter.SetInput1Data(imgvtk)
    subtractFilter.SetInput2Data(inputImageData)
    subtractFilter.SetOperationToSubtract()  # performed inverse operation on the
    subtractFilter.Update()
    invertedImageNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLScalarVolumeNode")
    invertedImageNode.SetAndObserveImageData(subtractFilter.GetOutput())
    return invertedImageNode

class DockerVesselSegTest(ScriptedLoadableModuleTest):
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
    self.test_DockerVesselSeg1()

  def test_DockerVesselSeg1(self):
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
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = DockerVesselSegLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
