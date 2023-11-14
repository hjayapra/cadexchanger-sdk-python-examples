# $Id$
#
# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2022, CADEX. All rights reserved.
#
# This file is part of the CAD Exchanger software.
#
# You may use this file under the terms of the BSD license as follows:
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK  as mtk

import MTKConverter_PartProcessor as part_proc

class MTKConverter_UnfoldedPartData:
    def __init__(self):
        self.myIsInit = False
        self.myLength = 0.0
        self.myWidth = 0.0
        self.myThickness = 0.0
        self.myPerimeter = 0.0
        self.myBRep = cadex.ModelData_BRepRepresentation()
        self.myIssueList = mtk.MTKBase_FeatureList()

class MTKConverter_SheetMetalData(part_proc.MTKConverter_ProcessData):
    def __init__(self, thePart: cadex.ModelData_Part):
        super().__init__(thePart)
        self.myIsSheetMetalPart = True
        self.myFeatureList = mtk.MTKBase_FeatureList()
        self.myIssueList = mtk.MTKBase_FeatureList()
        self.myUnfoldedPartData = MTKConverter_UnfoldedPartData()

class MTKConverter_SheetMetalProcessor(part_proc.MTKConverter_VoidPartProcessor):
    def __init__(self, theUnfoldedModel: cadex.ModelData_Model):
        super().__init__()
        self.myAnalyzer = mtk.SheetMetal_Analyzer()
        self.myUnfoldedModel = theUnfoldedModel
        self.myCurrentUnfoldedBRep = cadex.ModelData_BRepRepresentation()

        self.myAnalyzer.AddTool(mtk.SheetMetal_FeatureRecognizer())
        self.myAnalyzer.AddTool(mtk.SheetMetal_Unfolder())

    # Compute approximate thickness value, which can be used as the input thickness value for SheetMetal_FeatureRecognizer.
    @staticmethod
    def __CalculateInitialThicknessValue(theShape: cadex.ModelData_Shape):
        aVolume = cadex.ModelAlgo_ValidationProperty_ComputeVolume(theShape)
        aSurfaceArea = cadex.ModelAlgo_ValidationProperty_ComputeSurfaceArea(theShape)
        aThickness = aVolume / (aSurfaceArea / 2.0)
        return aThickness

    def __UpdateProcessData(self, theData: mtk.SheetMetal_Data, thePart: cadex.ModelData_Part):
        anSMData = MTKConverter_SheetMetalData(thePart)
        self.myData.append(anSMData)

        if theData.IsEmpty():
            anSMData.myIsSheetMetalPart = False
            return

        for i in theData.FeatureList():
            anSMData.myFeatureList.Append(i)

        anUnfoldedData = anSMData.myUnfoldedPartData
        aFlatPattern = theData.FlatPattern()
        if not aFlatPattern.IsNull():
            anUnfoldedShell = aFlatPattern.UnfoldedShell()
            if anUnfoldedShell:
                self.myCurrentUnfoldedBRep.Add(anUnfoldedShell)
                anUnfoldedData.myBRep = self.myCurrentUnfoldedBRep

                anUnfoldedData.myIsInit = True
                anUnfoldedData.myLength = aFlatPattern.Length()
                anUnfoldedData.myWidth = aFlatPattern.Width()
                anUnfoldedData.myThickness = aFlatPattern.Thickness()
                anUnfoldedData.myPerimeter = aFlatPattern.Perimeter()

        aDFMAnalyzer = mtk.DFMSheetMetal_Analyzer()
        anIssueList = aDFMAnalyzer.Perform(theData)
        for anIssue in anIssueList:
            if (anUnfoldedData.myIsInit
                and (mtk.DFMSheetMetal_FlatPatternInterferenceIssue.CompareType(anIssue)
                     or mtk.DFMSheetMetal_NonStandardSheetSizeIssue.CompareType(anIssue)
                     or mtk.DFMSheetMetal_NonStandardSheetThicknessIssue.CompareType(anIssue))):
                anUnfoldedData.myIssueList.Append(anIssue)
            else:
                anSMData.myIssueList.Append(anIssue)

    def ProcessSolid (self, thePart: cadex.ModelData_Part, theSolid: cadex.ModelData_Solid):
        anSMData = self.myAnalyzer.Perform(theSolid, MTKConverter_SheetMetalProcessor.__CalculateInitialThicknessValue (theSolid))
        self.__UpdateProcessData(anSMData, thePart)

    def ProcessShell (self, thePart: cadex.ModelData_Part, theShell: cadex.ModelData_Shell):
        anSMData = self.myAnalyzer.Perform(theShell)
        self.__UpdateProcessData(anSMData, thePart)

    def PostPartProcess(self, thePart: cadex.ModelData_Part):
        if not self.myCurrentUnfoldedBRep:
            return

        anUnfoldedPart = cadex.ModelData_Part(thePart.Name())
        anUnfoldedPart.SetUuid(thePart.Uuid())
        anUnfoldedPart.AddRepresentation(self.myCurrentUnfoldedBRep)

        aMesher = cadex.ModelAlgo_BRepMesher()
        aMesher.Compute(anUnfoldedPart)

        self.myUnfoldedModel.AddRoot(anUnfoldedPart)
        self.myCurrentUnfoldedBRep = cadex.ModelData_BRepRepresentation()
