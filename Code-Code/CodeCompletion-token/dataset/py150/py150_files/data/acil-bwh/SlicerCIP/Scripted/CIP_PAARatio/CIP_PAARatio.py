# -*- coding: utf-8 -*-
import os, sys
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

import logging

# Add the CIP common library to the path if it has not been loaded yet
try:
    from CIP.logic.SlicerUtil import SlicerUtil
except Exception as ex:
    currentpath = os.path.dirname(os.path.realpath(__file__))
    # We assume that CIP_Common is in the development structure
    path = os.path.normpath(currentpath + '/../CIP_Common')
    if not os.path.exists(path):
        # We assume that CIP is a subfolder (Slicer behaviour)
        path = os.path.normpath(currentpath + '/CIP')
    sys.path.append(path)
    print("The following path was manually added to the PythonPath in CIP_PAARatio: " + path)
    from CIP.logic.SlicerUtil import SlicerUtil

from CIP.logic import Util
from CIP.ui import CaseReportsWidget


#
# CIP_PAARatio
#
class CIP_PAARatio(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PAA Ratio"
        self.parent.categories = SlicerUtil.CIP_ModulesCategory
        self.parent.dependencies = [SlicerUtil.CIP_ModuleName]
        self.parent.contributors = ["Jorge Onieva (jonieva@bwh.harvard.edu)", "Applied Chest Imaging Laboratory", "Brigham and Women's Hospital"]
        self.parent.helpText = """Calculate the ratio between pulmonary arterial and aorta. This biomarker has been proved
                                to predict acute exacerbations of COPD (Wells, J. M., Washko, G. R., Han, M. K., Abbas,
                                N., Nath, H., Mamary, a. J., Dransfield, M. T. (2012). Pulmonary Arterial Enlargement and Acute Exacerbations
                                of COPD. New England Journal of Medicine, 367(10), 913-921).
                                For more information refer to:
                                http://www.nejm.org/doi/full/10.1056/NEJMoa1203830"""
        self.parent.acknowledgementText = SlicerUtil.ACIL_AcknowledgementText

#
# CIP_PAARatioWidget
#

class CIP_PAARatioWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """
    @property
    def moduleName(self):
        return "CIP_PAARatio"

    def __init__(self, parent):
        ScriptedLoadableModuleWidget.__init__(self, parent)

        from functools import partial
        def __onNodeAddedObserver__(self, caller, eventId, callData):
            """Node added to the Slicer scene"""
            if callData.GetClassName() == 'vtkMRMLScalarVolumeNode' \
                    and slicer.util.mainWindow().moduleSelector().selectedModule == self.moduleName:    # Current module visible
                self.volumeSelector.setCurrentNode(callData)

        self.__onNodeAddedObserver__ = partial(__onNodeAddedObserver__, self)
        self.__onNodeAddedObserver__.CallDataType = vtk.VTK_OBJECT

    def setup(self):
        """This is called one time when the module GUI is initialized
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Create objects that can be used anywhere in the module. Example: in most cases there should be just one
        # object of the logic class
        self.logic = CIP_PAARatioLogic()

        #
        # Create all the widgets. Example Area
        mainAreaCollapsibleButton = ctk.ctkCollapsibleButton()
        mainAreaCollapsibleButton.text = "Main parameters"
        self.layout.addWidget(mainAreaCollapsibleButton)
        self.mainAreaLayout = qt.QGridLayout(mainAreaCollapsibleButton)

        self.label = qt.QLabel("Select the volume")
        self.label.setStyleSheet("margin:10px 0 20px 7px")
        self.mainAreaLayout.addWidget(self.label, 0, 0)

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ( "vtkMRMLScalarVolumeNode", "" )
        # DEPRECATED. Now there is a new vtkMRMLLabelMapNode
        #self.volumeSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", "0" )  # No labelmaps
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.autoFillBackground = True
        self.volumeSelector.addEnabled = True
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.showHidden = False
        self.volumeSelector.showChildNodeTypes = False
        self.volumeSelector.setMRMLScene( slicer.mrmlScene )
        self.volumeSelector.setStyleSheet("margin:0px 0 0px 0; padding:2px 0 2px 5px")
        self.mainAreaLayout.addWidget(self.volumeSelector, 0, 1)


        # self.label2 = qt.QLabel("Select the slice")
        # self.label2.setStyleSheet("margin:0px 0 20px 7px; padding-top:20px")
        # self.mainAreaLayout.addWidget(self.label2, 1, 0)

        self.placeDefaultRulersButton = ctk.ctkPushButton()
        self.placeDefaultRulersButton.text = "Place default rulers"
        # self.placeDefaultRulersSliceButton.toolTip = "Navigate to the best estimated slice to place the rulers"
        self.placeDefaultRulersButton.setIcon(qt.QIcon("{0}/next.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeDefaultRulersButton.setIconSize(qt.QSize(20, 20))
        self.placeDefaultRulersButton.setStyleSheet("font-weight: bold;")
        # self.placeDefaultRulersButton.setFixedWidth(140)
        self.mainAreaLayout.addWidget(self.placeDefaultRulersButton, 1, 1)

        ### Structure Selector
        self.structuresGroupbox = qt.QGroupBox("Select the structure")
        self.groupboxLayout = qt.QVBoxLayout()
        self.structuresGroupbox.setLayout(self.groupboxLayout)
        self.mainAreaLayout.addWidget(self.structuresGroupbox, 2, 0)


        self.structuresButtonGroup=qt.QButtonGroup()
        # btn = qt.QRadioButton("None")
        # btn.visible = False
        # self.structuresButtonGroup.addButton(btn)
        # self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Both")
        btn.checked = True
        self.structuresButtonGroup.addButton(btn, 0)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Pulmonary Arterial")
        self.structuresButtonGroup.addButton(btn, 1)
        self.groupboxLayout.addWidget(btn)

        btn = qt.QRadioButton("Aorta")
        self.structuresButtonGroup.addButton(btn, 2)
        self.groupboxLayout.addWidget(btn)

        ### Buttons toolbox
        self.buttonsToolboxFrame = qt.QFrame()
        self.buttonsToolboxLayout = qt.QGridLayout()
        self.buttonsToolboxFrame.setLayout(self.buttonsToolboxLayout)
        self.mainAreaLayout.addWidget(self.buttonsToolboxFrame, 2, 1)


        self.placeRulersButton = ctk.ctkPushButton()
        self.placeRulersButton.text = "Place ruler/s"
        self.placeRulersButton.toolTip = "Place the ruler/s for the selected structure/s in the current slice"
        self.placeRulersButton.setIcon(qt.QIcon("{0}/ruler.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.placeRulersButton.setIconSize(qt.QSize(20,20))
        self.placeRulersButton.setFixedWidth(105)
        self.placeRulersButton.setStyleSheet("font-weight:bold")
        self.buttonsToolboxLayout.addWidget(self.placeRulersButton, 0, 0)

        self.moveUpButton = ctk.ctkPushButton()
        self.moveUpButton.text = "Move up"
        self.moveUpButton.toolTip = "Move the selected ruler/s one slice up"
        self.moveUpButton.setIcon(qt.QIcon("{0}/move_up.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveUpButton.setIconSize(qt.QSize(20,20))
        self.moveUpButton.setFixedWidth(95)
        self.buttonsToolboxLayout.addWidget(self.moveUpButton, 0, 1)

        self.moveDownButton = ctk.ctkPushButton()
        self.moveDownButton.text = "Move down"
        self.moveDownButton.toolTip = "Move the selected ruler/s one slice down"
        self.moveDownButton.setIcon(qt.QIcon("{0}/move_down.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.moveDownButton.setIconSize(qt.QSize(20,20))
        self.moveDownButton.setFixedWidth(95)
        self.buttonsToolboxLayout.addWidget(self.moveDownButton, 0, 2)

        self.removeButton = ctk.ctkPushButton()
        self.removeButton.text = "Remove ALL rulers"
        self.removeButton.toolTip = "Remove all the rulers for this volume"
        self.removeButton.setIcon(qt.QIcon("{0}/delete.png".format(SlicerUtil.CIP_ICON_DIR)))
        self.removeButton.setIconSize(qt.QSize(20,20))
        self.buttonsToolboxLayout.addWidget(self.removeButton, 1, 1, 1, 2, 2)

        ### Textboxes
        self.textboxesFrame = qt.QFrame()
        self.textboxesLayout = qt.QFormLayout()
        self.textboxesFrame.setLayout(self.textboxesLayout)
        self.textboxesFrame.setFixedWidth(190)
        self.mainAreaLayout.addWidget(self.textboxesFrame, 3, 0)

        self.paTextBox = qt.QLineEdit()
        self.paTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("PA (mm):  ", self.paTextBox)

        self.aortaTextBox = qt.QLineEdit()
        self.aortaTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("Aorta (mm):  ", self.aortaTextBox)

        self.ratioTextBox = qt.QLineEdit()
        self.ratioTextBox.setReadOnly(True)
        self.textboxesLayout.addRow("Ratio PA/A: ", self.ratioTextBox)


        # Save case data
        self.reportsCollapsibleButton = ctk.ctkCollapsibleButton()
        self.reportsCollapsibleButton.text = "Reporting"
        self.layout.addWidget(self.reportsCollapsibleButton)
        self.reportsLayout = qt.QHBoxLayout(self.reportsCollapsibleButton)

        self.storedColumnNames = ["caseId", "paDiameter_mm", "aortaDiameter_mm",
                                  "pa1r", "pa1a", "pa1s", "pa2r", "pa2a", "pa2s",
                                  "a1r", "a1a", "a1s", "a2r", "a2a", "a2s"]
        self.reportsWidget = CaseReportsWidget("CIP_PAARatio", columnNames=self.storedColumnNames, parentWidget=self.reportsCollapsibleButton)
        self.reportsWidget.setup()

        self.switchToRedView()

        #####
        # Case navigator
        if SlicerUtil.isSlicerACILLoaded():
            caseNavigatorAreaCollapsibleButton = ctk.ctkCollapsibleButton()
            caseNavigatorAreaCollapsibleButton.text = "Case navigator"
            self.layout.addWidget(caseNavigatorAreaCollapsibleButton, 0x0020)
            # caseNavigatorLayout = qt.QVBoxLayout(caseNavigatorAreaCollapsibleButton)

            # Add a case list navigator
            from ACIL.ui import CaseNavigatorWidget
            self.caseNavigatorWidget = CaseNavigatorWidget(self.moduleName, caseNavigatorAreaCollapsibleButton)
            self.caseNavigatorWidget.setup()

        self.layout.addStretch()


        # Connections
        self.observers = []
        self.__addSceneObservables__()

        self.volumeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelectorChanged)
        self.placeDefaultRulersButton.connect('clicked()', self.oPlaceDefaultRulersClicked)
        self.placeRulersButton.connect('clicked()', self.onPlaceRulersClicked)
        self.moveUpButton.connect('clicked()', self.onMoveUpRulerClicked)
        self.moveDownButton.connect('clicked()', self.onMoveDownRulerClicked)
        self.removeButton.connect('clicked()', self.onRemoveRulerClicked)

        self.reportsWidget.addObservable(self.reportsWidget.EVENT_SAVE_BUTTON_CLICKED, self.onSaveReport)


    def enter(self):
        """This is invoked every time that we select this module as the active module in Slicer (not only the first time)"""
        # activeVolumeId = SlicerUtil.getActiveVolumeIdInRedSlice()
        # if activeVolumeId is not None:
        #     self.volumeSelector.setCurrentNodeID(activeVolumeId)
        #     if activeVolumeId not in self.logic.currentVolumesLoaded:
        #         self.placeDefaultRulers(activeVolumeId)
        volumeId = self.volumeSelector.currentNodeId
        if volumeId:
            SlicerUtil.setActiveVolumeId(volumeId)

    def exit(self):
        """This is invoked every time that we switch to another module (not only when Slicer is closed)."""
        pass

    def cleanup(self):
        """This is invoked as a destructor of the GUI when the module is no longer going to be used"""
        pass


    def jumpToTemptativeSlice(self, volumeId):
        """ Jump the red window to a predefined slice based on the size of the volume
        :param volumeId:
        """
        # Get the default coordinates of the ruler
        aorta1, aorta2, pa1, pa2 = self.logic.getDefaultCoords(volumeId)
        # Set the display in the right slice
        self.moveRedWindowToSlice(aorta1[2])

    def placeDefaultRulers(self, volumeId):
        """ Set the Aorta and PA rulers to a default estimated position and jump to that slice
        :param volumeId:
        """
        if not volumeId:
            return
        # Hide all the actual ruler nodes
        self.logic.hideAllRulers()
        # Remove the current rulers for this volume
        self.logic.removeRulers(volumeId)
        # Create the default rulers
        self.logic.createDefaultRulers(volumeId, self.onRulerUpdated)
        # Activate both structures
        self.structuresButtonGroup.buttons()[0].setChecked(True)
        # Jump to the slice where the rulers are
        self.jumpToTemptativeSlice(volumeId)
        # Place the rulers in the current slice
        self.placeRuler()
        # Add the current volume to the list of loaded volumes
        self.logic.currentVolumesLoaded.add(volumeId)

        # Modify the zoom of the Red slice
        redSliceNode = slicer.util.getFirstNodeByClassByName("vtkMRMLSliceNode", "Red")
        factor = 0.5
        newFOVx = redSliceNode.GetFieldOfView()[0] * factor
        newFOVy = redSliceNode.GetFieldOfView()[1] * factor
        newFOVz = redSliceNode.GetFieldOfView()[2]
        redSliceNode.SetFieldOfView( newFOVx, newFOVy, newFOVz )
        # Move the camera up to fix the view
        redSliceNode.SetXYZOrigin(0, 50, 0)
        # Refresh the data in the viewer
        redSliceNode.UpdateMatrices()


    def placeRuler(self):
        """ Place one or the two rulers in the current visible slice in Red node
        """
        volumeId = self.volumeSelector.currentNodeId
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Pulmonary Arterial, Aorta or both to place the right ruler/s')
            return

        # Get the current slice
        currentSlice = self.getCurrentRedWindowSlice()

        if selectedStructure == self.logic.BOTH:
            structures = [self.logic.PA, self.logic.AORTA]
        else:
            structures = [selectedStructure]

        for structure in structures:
            self.logic.placeRulerInSlice(volumeId, structure, currentSlice, self.onRulerUpdated)

        self.refreshTextboxes()


    def getCurrentSelectedStructure(self):
        """ Get the current selected structure id
        :return: self.logic.AORTA or self.logic.PA
        """
        selectedStructureText = self.structuresButtonGroup.checkedButton().text
        if selectedStructureText == "Aorta": return self.logic.AORTA
        elif selectedStructureText == "Pulmonary Arterial": return  self.logic.PA
        elif selectedStructureText == "Both": return self.logic.BOTH
        return self.logic.NONE

    def stepSlice(self, offset):
        """ Move the selected structure one slice up or down
        :param offset: +1 or -1
        :return:
        """
        volumeId = self.volumeSelector.currentNodeId

        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return

        selectedStructure = self.getCurrentSelectedStructure()
        if selectedStructure == self.logic.NONE:
            self.showUnselectedStructureWarningMessage()
            return

        if selectedStructure == self.logic.BOTH:
            # Move both rulers
            self.logic.stepSlice(volumeId, self.logic.AORTA, offset)
            newSlice = self.logic.stepSlice(volumeId, self.logic.PA, offset)
        else:
            newSlice = self.logic.stepSlice(volumeId, selectedStructure, offset)

        self.moveRedWindowToSlice(newSlice)

    def removeRulers(self):
        """ Remove all the rulers related to the current volume node
        :return:
        """
        self.logic.removeRulers(self.volumeSelector.currentNodeId)
        self.refreshTextboxes(reset=True)


    def getCurrentRedWindowSlice(self):
        """ Get the current slice (in RAS) of the Red window
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        return redNodeSliceNode.GetSliceOffset()

    def moveRedWindowToSlice(self, newSlice):
        """ Moves the red display to the specified RAS slice
        :param newSlice: slice to jump (RAS format)
        :return:
        """
        redNodeSliceNode = slicer.app.layoutManager().sliceWidget('Red').sliceLogic().GetSliceNode()
        redNodeSliceNode.JumpSlice(0,0,newSlice)

    def refreshTextboxes(self, reset=False):
        """ Update the information of the textboxes that give information about the measurements
        """
        self.aortaTextBox.setText("0")
        self.paTextBox.setText("0")
        self.ratioTextBox.setText("0")
        self.ratioTextBox.setStyleSheet(" QLineEdit { background-color: white; color: black}");

        volumeId = self.volumeSelector.currentNodeId
        if volumeId not in self.logic.currentVolumesLoaded:
            return

        if volumeId:
            self.logic.changeColor(volumeId, self.logic.defaultColor)
        aorta = None
        pa = None
        if not reset:
            rulerAorta, newAorta = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeId,
                                        self.logic.AORTA, createIfNotExist=False)
            rulerPA, newPA = self.logic.getRulerNodeForVolumeAndStructure(self.volumeSelector.currentNodeId,
                                        self.logic.PA, createIfNotExist=False)
            if rulerAorta:
                aorta = rulerAorta.GetDistanceMeasurement()
                self.aortaTextBox.setText(str(aorta))
            if rulerPA:
                pa = rulerPA.GetDistanceMeasurement()
                self.paTextBox.setText(str(pa))
            if aorta is not None and aorta != 0:
                try:
                    ratio = pa / aorta
                    self.ratioTextBox.setText(str(ratio))
                    if ratio > 1:
                        # Switch colors ("alarm")
                        self.ratioTextBox.setStyleSheet(" QLineEdit { background-color: rgb(255, 0, 0); color: white}");
                        self.logic.changeColor(volumeId, self.logic.defaultWarningColor)
                except Exception:
                    Util.print_last_exception()

    def showUnselectedVolumeWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Select a volume',
                'Please select a volume')

    def showUnselectedStructureWarningMessage(self):
        qt.QMessageBox.warning(slicer.util.mainWindow(), 'Review structure',
                'Please select Aorta, Pulmonary Arterial or Both to place the right ruler/s')

    def switchToRedView(self):
        """ Switch the layout to Red slice only
        :return:
        """
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(6)

    def __addSceneObservables__(self):
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.NodeAddedEvent, self.__onNodeAddedObserver__))
        self.observers.append(slicer.mrmlScene.AddObserver(slicer.vtkMRMLScene.EndCloseEvent, self.__onSceneClosed__))

    def __removeSceneObservables(self):
        for observer in self.observers:
            slicer.mrmlScene.RemoveObserver(observer)
            self.observers.remove(observer)

    #########
    # EVENTS
    def onVolumeSelectorChanged(self, node):
        #if node is not None and node.GetID() not in self.currentVolumesLoaded:
        # if node is not None:
        #     # New node. Load default rulers
        #     if node.GetID() not in self.logic.currentVolumesLoaded:
        #         self.placeDefaultRulers(node.GetID())
        self.refreshTextboxes()

    def onStructureClicked(self, button):
        fiducialsNode = self.getFiducialsNode(self.volumeSelector.currentNodeId)
        if fiducialsNode is not None:
            self.__addRuler__(button.text, self.volumeSelector.currentNodeId)

            markupsLogic = slicer.modules.markups.logic()
            markupsLogic.SetActiveListID(fiducialsNode)

            applicationLogic = slicer.app.applicationLogic()
            selectionNode = applicationLogic.GetSelectionNode()

            selectionNode.SetReferenceActivePlaceNodeClassName("vtkMRMLAnnotationRulerNode")
            interactionNode = applicationLogic.GetInteractionNode()
            interactionNode.SwitchToSinglePlaceMode()

    def oPlaceDefaultRulersClicked(self):
        volumeId = self.volumeSelector.currentNodeId
        if volumeId == '':
            self.showUnselectedVolumeWarningMessage()
            return
        self.placeDefaultRulers(volumeId)

    def onRulerUpdated(self, node, event):
        self.refreshTextboxes()

    def onPlaceRulersClicked(self):
        self.placeRuler()

    def onMoveUpRulerClicked(self):
        self.stepSlice(1)

    def onMoveDownRulerClicked(self):
        self.stepSlice(-1)

    def onRemoveRulerClicked(self):
        if (qt.QMessageBox.question(slicer.util.mainWindow(), 'Remove rulers',
            'Are you sure you want to remove all the rulers from this volume?',
            qt.QMessageBox.Yes|qt.QMessageBox.No)) == qt.QMessageBox.Yes:
            self.logic.removeRulers(self.volumeSelector.currentNodeId)
            self.refreshTextboxes()

    def onSaveReport(self):
        """ Save the current values in a persistent csv file
        :return:
        """
        volumeId = self.volumeSelector.currentNodeId
        if volumeId:
            caseName = slicer.mrmlScene.GetNodeByID(volumeId).GetName()
            coords = [0, 0, 0, 0]
            pa1 = pa2 = a1 = a2 = None
            # PA
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.PA, createIfNotExist=False)
            if rulerNode:
                # Get current RAS coords
                rulerNode.GetPositionWorldCoordinates1(coords)
                pa1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                pa2 = list(coords)
            # AORTA
            rulerNode, newNode = self.logic.getRulerNodeForVolumeAndStructure(volumeId, self.logic.AORTA, createIfNotExist=False)
            if rulerNode:
                rulerNode.GetPositionWorldCoordinates1(coords)
                a1 = list(coords)
                rulerNode.GetPositionWorldCoordinates2(coords)
                a2 = list(coords)
            self.reportsWidget.saveCurrentValues(
                caseId=caseName,
                paDiameter_mm=self.paTextBox.text,
                aortaDiameter_mm=self.aortaTextBox.text,
                pa1r = pa1[0] if pa1 is not None else '',
                pa1a = pa1[1] if pa1 is not None else '',
                pa1s = pa1[2] if pa1 is not None else '',
                pa2r = pa2[0] if pa2 is not None else '',
                pa2a = pa2[1] if pa2 is not None else '',
                pa2s = pa2[2] if pa2 is not None else '',
                a1r = a1[0] if a1 is not None else '',
                a1a = a1[1] if a1 is not None else '',
                a1s = a1[2] if a1 is not None else '',
                a2r = a2[0] if a2 is not None else '',
                a2a = a2[1] if a2 is not None else '',
                a2s = a2[2] if a2 is not None else ''
            )
            qt.QMessageBox.information(slicer.util.mainWindow(), 'Data saved', 'The data were saved successfully')

    def __onSceneClosed__(self, arg1, arg2):
        """ Scene closed. Reset currently loaded volumes
        :param arg1:
        :param arg2:
        :return:
        """
        self.logic.currentVolumesLoaded.clear()


# CIP_PAARatioLogic
#
class CIP_PAARatioLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    NONE = 0
    AORTA = 1
    PA = 2
    BOTH = 3
    SLICEFACTOR = 0.6

    # Default XY coordinates for Aorta and PA (the Z will be stimated depending on the number of slices)
    defaultAorta1 = [220, 170, 0]
    defaultAorta2 = [275, 175, 0]
    defaultPA1 = [280, 175, 0]
    defaultPA2 = [320, 190, 0]

    defaultColor = [0.5, 0.5, 1]
    defaultWarningColor = [1, 0, 0]

    def __init__(self):
        self.currentVolumesLoaded = set()

    def getRootAnnotationsNode(self):
        """ Get the root annotations node global to the scene, creating it if necessary
        :return: "All Annotations" vtkMRMLAnnotationHierarchyNode
        """
        return SlicerUtil.getRootAnnotationsNode()

    def getRulersListNode(self, volumeId, createIfNotExist=True):
        """ Get the rulers node for this volume, creating it if it doesn't exist yet
        :param volumeId:
        :return: "volumeId_paaRulersNode" vtkMRMLAnnotationHierarchyNode
        """
        # Search for the current volume hierarchy node (each volume has its own hierarchy)
        nodeName = volumeId + '_paaRulersNode'
        rulersNode = slicer.util.getNode(nodeName)

        if rulersNode is None and createIfNotExist:
            # Create the node
            annotationsLogic = slicer.modules.annotations.logic()
            rootHierarchyNode = self.getRootAnnotationsNode()
            annotationsLogic.SetActiveHierarchyNodeID(rootHierarchyNode.GetID())
            annotationsLogic.AddHierarchy()
            n = rootHierarchyNode.GetNumberOfChildrenNodes()
            rulersNode = rootHierarchyNode.GetNthChildNode(n-1)
            # Rename the node
            rulersNode.SetName(nodeName)
            logging.debug("Created node " + nodeName + " (general rulers node for this volume")
        # Return the node
        return rulersNode

    def getRulerNodeForVolumeAndStructure(self, volumeId, structureId, createIfNotExist=True, callbackWhenRulerModified=None):
        """ Search for the right ruler node to be created based on the volume and the selected
        structure (Aorta or PA).
        It also creates the necessary node hierarchy if it doesn't exist.
        :param volumeId:
        :param structureId: Aorta (1), PA (2)
        :param createIfNotExist: create the ruler node if it doesn't exist yet
        :param callbackWhenRulerModified: function to call when the ruler node is modified
        :return: node and a boolean indicating if the node has been created now
        """
        isNewNode = False
        if structureId == 0: # none
            return None, isNewNode
        if structureId == self.AORTA:     # Aorta
             #nodeName = volumeId + '_paaRulers_aorta'
            nodeName = "A"
        elif structureId == self.PA:   # 'Pulmonary Arterial':
        #     nodeName = volumeId + '_paaRulers_pa'
            nodeName = "PA"
        # Get the node that contains all the rulers for this volume
        rulersListNode = self.getRulersListNode(volumeId, createIfNotExist=createIfNotExist)
        node = None
        if rulersListNode:
            # Search for the node
            for i in range(rulersListNode.GetNumberOfChildrenNodes()):
                nodeWrapper = rulersListNode.GetNthChildNode(i)
                # nodeWrapper is also a HierarchyNode. We need to look for its only child that will be the rulerNode
                col = vtk.vtkCollection()
                nodeWrapper.GetChildrenDisplayableNodes(col)
                rulerNode = col.GetItemAsObject(0)

                if rulerNode.GetName() == nodeName:
                    node = rulerNode
                    break

            if node is None and createIfNotExist:
                # Create the node
                # Set the active node, so that the new ruler is a child node
                annotationsLogic = slicer.modules.annotations.logic()
                annotationsLogic.SetActiveHierarchyNodeID(rulersListNode.GetID())
                node = slicer.mrmlScene.CreateNodeByClass('vtkMRMLAnnotationRulerNode')
                node.SetName(nodeName)
                self.__changeColor__(node, self.defaultColor)
                slicer.mrmlScene.AddNode(node)
                isNewNode = True
                node.AddObserver(vtk.vtkCommand.ModifiedEvent, callbackWhenRulerModified)
                logging.debug("Created node " + nodeName + " for volume " + volumeId)

        return node, isNewNode

    def hideAllRulers(self):
        """ Hide all the ruler nodes
        """
        for volume in self.currentVolumesLoaded:
            rulersNode = self.getRulersListNode(volume, False)
            if rulersNode:
                print("Hiding " + rulersNode.GetID())

    def __changeColor__(self, node, color):
        for i in range(3):
            n = node.GetNthDisplayNode(i)
            if n:
                n.SetColor(color)
        # Refresh UI to repaint both rulers. Is this the best way? Who knows...
        slicer.app.layoutManager().sliceWidget("Red").sliceView().mrmlSliceNode().Modified()

    def changeColor(self, volumeId, color):
        """ Change the color for all the rulers in this volume
        :param volumeId:
        :param color:
        :return:
        """
        for structureId in [self.PA, self.AORTA]:
            node, new = self.getRulerNodeForVolumeAndStructure(volumeId, structureId, createIfNotExist=False)
            if node:
                self.__changeColor__(node, color)



    def createDefaultRulers(self, volumeId, callbackWhenRulerModified):
        """ Set the Aorta and PA rulers to their default position.
        The X and Y will be configured in "defaultAorta1, defaultAorta2, defaultPA1, defaultPA2" properties
        The Z will be estimated based on the number of slices of the volume
        :param volumeId: volume id
        :param callbackWhenRulerModified: function to invoke when the ruler is modified
        :return: a tuple of 4 vales. For each node, return the node and a boolean indicating if the node was
        created now
        """
        aorta1, aorta2, pa1, pa2 = self.getDefaultCoords(volumeId)

        rulerNodeAorta, newNodeAorta = self.getRulerNodeForVolumeAndStructure(volumeId, self.AORTA,
                                    createIfNotExist=True, callbackWhenRulerModified=callbackWhenRulerModified)
        rulerNodeAorta.SetPositionWorldCoordinates1(aorta1)
        rulerNodeAorta.SetPositionWorldCoordinates2(aorta2)

        rulerNodePA, newNodePA = self.getRulerNodeForVolumeAndStructure(volumeId, self.PA,
                                    createIfNotExist=True, callbackWhenRulerModified=callbackWhenRulerModified)
        rulerNodePA.SetPositionWorldCoordinates1(pa1)
        rulerNodePA.SetPositionWorldCoordinates2(pa2)

        return rulerNodeAorta, newNodeAorta, rulerNodePA, newNodePA

    def stepSlice(self, volumeId, structureId, sliceStep):
        """ Move the selected ruler up or down one slice.
        :param volumeId:
        :param structureId:
        :param sliceStep: +1 or -1
        :return: new slice in RAS format
        """
        # Calculate the RAS coords of the slice where we should jump to
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId, createIfNotExist=False)
        if not rulerNode:
            # The ruler has not been created. This op doesn't make sense
            return False

        coords = [0, 0, 0, 0]
        # Get current RAS coords
        rulerNode.GetPositionWorldCoordinates1(coords)

        # Get the transformation matrixes
        rastoijk=vtk.vtkMatrix4x4()
        ijktoras=vtk.vtkMatrix4x4()
        scalarVolumeNode = slicer.mrmlScene.GetNodeByID(volumeId)
        scalarVolumeNode.GetRASToIJKMatrix(rastoijk)
        scalarVolumeNode.GetIJKToRASMatrix(ijktoras)

        # Get the current slice (Z). It will be the same in both positions
        ijkCoords = list(rastoijk.MultiplyPoint(coords))

        # Add/substract the offset to Z
        ijkCoords[2] += sliceStep
        # Convert back to RAS, just replacing the Z
        newSlice = ijktoras.MultiplyPoint(ijkCoords)[2]

        self._placeRulerInSlice_(rulerNode, structureId, volumeId, newSlice)

        return newSlice


    def placeRulerInSlice(self, volumeId, structureId, newSlice, callbackWhenUpdated=None):
        """ Move the ruler to the specified slice (in RAS format)
        :param volumeId:
        :param structureId:
        :param newSlice: slice in RAS format
        :return: tuple with ruler node and a boolean indicating if the node was just created
        """
        # Get the correct ruler
        rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId, createIfNotExist=True)

        # Add the volume to the list of volumes that have some ruler
        self.currentVolumesLoaded.add(volumeId)

        # Move the ruler
        self._placeRulerInSlice_(rulerNode, structureId, volumeId, newSlice)

        #return rulerNode, newNode

    def _placeRulerInSlice_(self, rulerNode, structureId, volumeId, newSlice):
        """ Move the ruler to the specified slice (in RAS format)
        :param rulerNode: node of type vtkMRMLAnnotationRulerNode
        :param newSlice: slice in RAS format
        :return: True if the operation was succesful
        """
        coords1 = [0, 0, 0, 0]
        coords2 = [0, 0, 0, 0]
        # Get RAS coords of the ruler node
        rulerNode.GetPositionWorldCoordinates1(coords1)
        rulerNode.GetPositionWorldCoordinates2(coords2)

        # Set the slice of the coordinate
        coords1[2] = coords2[2] = newSlice

        if coords1[0] == 0 and coords1[1] == 0:
            # New node, get default coordinates depending on the structure
            defaultCoords = self.getDefaultCoords(volumeId)
            if structureId == self.AORTA:
                coords1[0] = defaultCoords[0][0]
                coords1[1] = defaultCoords[0][1]
                coords2[0] = defaultCoords[1][0]
                coords2[1] = defaultCoords[1][1]
            elif structureId == self.PA:
                coords1[0] = defaultCoords[2][0]
                coords1[1] = defaultCoords[2][1]
                coords2[0] = defaultCoords[3][0]
                coords2[1] = defaultCoords[3][1]

        rulerNode.SetPositionWorldCoordinates1(coords1)
        rulerNode.SetPositionWorldCoordinates2(coords2)

    def getDefaultCoords(self, volumeId):
        """ Get the default coords for aorta and PA in this volume (RAS format)
        :param volumeId:
        :return: (aorta1, aorta2, pa1, pa2). All of them lists of 3 positions in RAS format
        """
        volume = slicer.mrmlScene.GetNodeByID(volumeId)
        rasBounds = [0,0,0,0,0,0]
        volume.GetRASBounds(rasBounds)
        # Get the slice (Z)
        ijk = self.RAStoIJK(volume, [0, 0, rasBounds[5]])
        slice = int(ijk[2] * self.SLICEFACTOR)       # Empiric estimation

        # Get the default coords, converting from IJK to RAS
        aorta1 = list(self.defaultAorta1)
        aorta1[2] = slice
        aorta1 = self.IJKtoRAS(volume, aorta1)
        aorta2 = list(self.defaultAorta2)
        aorta2[2] = slice
        aorta2 = self.IJKtoRAS(volume, aorta2)

        pa1 = list(self.defaultPA1)
        pa1[2] = slice
        pa1 = self.IJKtoRAS(volume, pa1)
        pa2 = list(self.defaultPA2)
        pa2[2] = slice
        pa2 = self.IJKtoRAS(volume, pa2)

        return aorta1, aorta2, pa1, pa2


    def removeRulers(self, volumeId):
        """ Remove all the rulers for the selected volume
        :param volumeId:
        :param structureId:
        """
        #rulerNode, newNode = self.getRulerNodeForVolumeAndStructure(volumeId, structureId)
        rulersListNode = self.getRulersListNode(volumeId, createIfNotExist=False)
        if rulersListNode:
            rulersListNode.RemoveAllChildrenNodes()
            slicer.mrmlScene.RemoveNode(rulersListNode)


    def RAStoIJK(self, volumeNode, rasCoords):
        """ Transform a list of RAS coords in IJK for a volume
        :return: list of IJK coordinates
        """
        rastoijk=vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(rastoijk)
        rasCoords.append(1)
        return list(rastoijk.MultiplyPoint(rasCoords))

    def IJKtoRAS(self, volumeNode, ijkCoords):
        """ Transform a list of IJK coords in RAS for a volume
        :return: list of RAS coordinates
        """
        ijktoras=vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijktoras)
        ijkCoords.append(1)
        return list(ijktoras.MultiplyPoint(ijkCoords))


class CIP_PAARatioTest(ScriptedLoadableModuleTest):
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
        self.test_CIP_PAARatio_PrintMessage()

    def test_CIP_PAARatio_PrintMessage(self):
        self.delayDisplay("Starting the test")
        logic = CIP_PAARatioLogic()
        # Load a volume (TODO: get it from Slicer Data Store)
        volume = slicer.util.loadVolume('/Volumes/Mac500/Data/tempdata/10002K_INSP_STD_BWH_COPD.nhdr', returnNode=True)
        self.assertTrue(volume[0])  # The volume loaded correctly
        volumeId = volume[1].GetID()
        logic.createDefaultRulers(volumeId)
        # Make sure a ruler was created
        ruler = logic.getRulerNodeForVolumeAndStructure(volumeId, logic.AORTA, createIfNotExist=False)
        self.assertFalse(ruler[0] is None)
        self.delayDisplay('Test passed!')

