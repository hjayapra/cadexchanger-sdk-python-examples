# $Id$
#
# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2023, CADEX. All rights reserved.
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

import math
import os
import sys

from pathlib import Path

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK as mtk

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../../"))
sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../helpers/"))

import cadex_license as license
import mtk_license

import feature_group
import shape_processor

def ToDegrees(theAngleRad: float):
    return theAngleRad * 180.0 / math.pi

def PrintFeatureParameters(theIssue: mtk.MTKBase_Feature):
    #drilling
    if mtk.DFMMachining_SmallDiameterHoleIssue.CompareType(theIssue):
        aSDHIssue = mtk.DFMMachining_SmallDiameterHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected min diameter", aSDHIssue.ExpectedMinDiameter(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual diameter",       aSDHIssue.ActualDiameter(),      "mm")
    elif mtk.DFMMachining_DeepHoleIssue.CompareType(theIssue):
        aDHIssue = mtk.DFMMachining_DeepHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected max depth", aDHIssue.ExpectedMaxDepth(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual depth",       aDHIssue.ActualDepth(),      "mm")
    elif mtk.DFMMachining_NonStandardDiameterHoleIssue.CompareType(theIssue):
        aNSDHIssue = mtk.DFMMachining_NonStandardDiameterHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("nearest standard diameter", aNSDHIssue.NearestStandardDiameter(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual diameter",           aNSDHIssue.ActualDiameter(),          "mm")
    elif mtk.DFMMachining_NonStandardDrillPointAngleBlindHoleIssue.CompareType(theIssue):
        aNSDPABHIssue = mtk.DFMMachining_NonStandardDrillPointAngleBlindHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("nearest standard angle", ToDegrees(aNSDPABHIssue.NearestStandardAngle()), "deg")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual angle",           ToDegrees(aNSDPABHIssue.ActualAngle()),          "deg")
    elif mtk.DFMMachining_FlatBottomHoleIssue.CompareType(theIssue):
        pass #no parameters
    elif mtk.DFMMachining_NonPerpendicularHoleIssue.CompareType(theIssue):
        pass #no parameters
    elif mtk.DFMMachining_IntersectingCavityHoleIssue.CompareType(theIssue):
        pass #no parameters
    elif mtk.DFMMachining_PartialHoleIssue.CompareType(theIssue):
        aPHIssue = mtk.DFMMachining_PartialHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "expected min material percent", aPHIssue.ExpectedMinMaterialPercent(), "")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual material percent",       aPHIssue.ActualMaterialPercent(),      "")
    #milling
    elif mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.CompareType(theIssue):
        aNSRMPFFIssue = mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("nearest standard radius", aNSRMPFFIssue.NearestStandardRadius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual radius",           aNSRMPFFIssue.ActualRadius(),          "mm")
    elif mtk.DFMMachining_DeepPocketIssue.CompareType(theIssue):
        aDPIssue = mtk.DFMMachining_DeepPocketIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected max depth", aDPIssue.ExpectedMaxDepth(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual depth",       aDPIssue.ActualDepth(),      "mm")
    elif mtk.DFMMachining_HighBossIssue.CompareType(theIssue):
        aHBIssue = mtk.DFMMachining_HighBossIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected max height", aHBIssue.ExpectedMaxHeight(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual height",       aHBIssue.ActualHeight(),      "mm")
    elif mtk.DFMMachining_LargeMilledPartIssue.CompareType(theIssue):
        aLMPIssue = mtk.DFMMachining_LargeMilledPartIssue.Cast(theIssue)
        anExpectedSize = aLMPIssue.ExpectedMaxMilledPartSize()
        anActualSize = aLMPIssue.ActualMilledPartSize()
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "expected max size (LxWxH)",
            feature_group.Dimension(anExpectedSize.Length(), anExpectedSize.Width(), anExpectedSize.Height()),
            "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual size (LxWxH)",
            feature_group.Dimension(anActualSize.Length(), anActualSize.Width(), anActualSize.Height()),
            "mm")
    elif mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.CompareType(theIssue):
        aSRMPICIssue = mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected min radius", aSRMPICIssue.ExpectedMinRadius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual radius",       aSRMPICIssue.ActualRadius(),      "mm")
    elif mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.CompareType(theIssue):
        aNPMPSIssue = mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual angle", ToDegrees (aNPMPSIssue.ActualAngle()), "deg")
    elif mtk.DFMMachining_MilledPartExternalEdgeFilletIssue.CompareType(theIssue):
        pass #no parameters
    elif mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.CompareType(theIssue):
        aIRMPFFIssue = mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected radius", aIRMPFFIssue.ExpectedRadius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual radius",   aIRMPFFIssue.ActualRadius(),   "mm")
    elif mtk.DFMMachining_NarrowRegionInPocketIssue.CompareType(theIssue):
        aSMNRDIssue = mtk.DFMMachining_NarrowRegionInPocketIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected minimum region size", aSMNRDIssue.ExpectedMinRegionSize(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual region size",           aSMNRDIssue.ActualRegionSize(),      "mm")
    elif mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.CompareType(theIssue):
        aLMNRRIssue = mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected regions maximum to minimum size ratio", aLMNRRIssue.ExpectedMaxRegionsMaxToMinSizeRatio(), "")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual regions maximum to minimum size ratio",   aLMNRRIssue.ActualMaxRegionsMaxToMinSizeRatio(),   "")
    #turning
    elif mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.CompareType(theIssue):
        anITPODPRIssue = mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "expected max incline angle", ToDegrees (anITPODPRIssue.ExpectedMaxFaceInclineAngle()), "deg")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual incline angle",       ToDegrees (anITPODPRIssue.ActualFaceInclineAngle()),      "deg")
    elif mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.CompareType(theIssue):
        aSRTPICIssue = mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected min radius", aSRTPICIssue.ExpectedMinRadius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual radius",       aSRTPICIssue.ActualRadius(),      "mm")
    elif mtk.DFMMachining_LargeTurnedPartIssue.CompareType(theIssue):
        aLTPIssue = mtk.DFMMachining_LargeTurnedPartIssue.Cast(theIssue)
        anExpectedSize = aLMPIssue.ExpectedMaxTurnedPartSize()
        anActualSize = aLMPIssue.ActualTurnedPartSize()
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "expected max size (LxR)",
            feature_group.Pair(anExpectedSize.Length(), anExpectedSize.Radius()),
            "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual size (LxR)",
            feature_group.Pair(anActualSize.Length(), anActualSize.Radius()),
            "mm")
    elif mtk.DFMMachining_LongSlenderTurnedPartIssue.CompareType(theIssue):
        aLSTPIssue = mtk.DFMMachining_LongSlenderTurnedPartIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected min length", aLSTPIssue.ExpectedMaxLength(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual length",       aLSTPIssue.ActualLength(),      "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual min diameter", aLSTPIssue.ActualMinDiameter(), "mm")
    elif mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.CompareType(theIssue):
        aSDBBHRIssue = mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "expected min relief depth", aSDBBHRIssue.ExpectedMinReliefDepth(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual relief depth",       aSDBBHRIssue.ActualReliefDepth(),      "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter(
            "actual diameter",           aSDBBHRIssue.ActualDiameter(),         "mm")
    elif mtk.DFMMachining_DeepBoredHoleIssue.CompareType(theIssue):
        aDBHIssue = mtk.DFMMachining_DeepBoredHoleIssue.Cast(theIssue)
        feature_group.FeatureGroupManager.PrintFeatureParameter("expected max depth", aDBHIssue.ExpectedMaxDepth(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual depth",       aDBHIssue.ActualDepth(),      "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("actual diameter",    aDBHIssue.ActualDiameter(),   "mm")
    elif mtk.DFMMachining_SquareEndKeywayIssue.CompareType(theIssue):
        pass #no parameters
    elif mtk.DFMMachining_NonSymmetricalAxialSlotIssue.CompareType(theIssue):
        pass #no parameters

def PrintIssues(theIssueList: mtk.MTKBase_FeatureList):
    aManager = feature_group.FeatureGroupManager()

    #group by parameters to provide more compact information about features
    for anIssue in theIssueList:
        #drilling
        if mtk.DFMMachining_SmallDiameterHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Small Diameter Hole Issue(s)", "Hole(s)", True, anIssue)
        elif mtk.DFMMachining_DeepHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Deep Hole Issue(s)", "Hole(s)", True, anIssue)
        elif mtk.DFMMachining_NonStandardDiameterHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Non Standard Diameter Hole Issue(s)", "Hole(s)", True, anIssue)
        elif mtk.DFMMachining_NonStandardDrillPointAngleBlindHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Non Standard Drill Point Angle Blind Hole Issue(s)", "Hole(s)", True, anIssue)
        elif mtk.DFMMachining_FlatBottomHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Flat Bottom Hole Issue(s)", "", False, anIssue)
        elif mtk.DFMMachining_NonPerpendicularHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Non Perpendicular Hole Issue(s)", "", False, anIssue)
        elif mtk.DFMMachining_IntersectingCavityHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Intersecting Cavity Hole Issue(s)", "", False, anIssue)
        elif mtk.DFMMachining_PartialHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Partial Hole Issue(s)", "Hole(s)", True, anIssue)
        #milling
        elif mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.CompareType(anIssue):
            aManager.AddFeature("Non Standard Radius Milled Part Floor Fillet Issue(s)", "Floor Fillet(s)", True, anIssue)
        elif mtk.DFMMachining_DeepPocketIssue.CompareType(anIssue):
            aManager.AddFeature("Deep Pocket Issue(s)", "Pocket(s)", True, anIssue)
        elif mtk.DFMMachining_DeepPocketIssue.CompareType(anIssue):
            aManager.AddFeature("High Boss Issue(s)", "Boss(es)", True, anIssue)
        elif mtk.DFMMachining_LargeMilledPartIssue.CompareType(anIssue):
            aManager.AddFeature("Large Milled Part Issue(s)", "Part(s)", True, anIssue)
        elif mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.CompareType(anIssue):
            aManager.AddFeature("Small Radius Milled Part Internal Corner Issue(s)", "Internal Corner(s)", True, anIssue)
        elif mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.CompareType(anIssue):
            aManager.AddFeature("Non Perpendicular Milled Part Shape Issue(s)", "Shape(s)", True, anIssue)
        elif mtk.DFMMachining_MilledPartExternalEdgeFilletIssue.CompareType(anIssue):
            aManager.AddFeature("Milled Part External Edge Fillet Issue(s)", "", False, anIssue)
        elif mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.CompareType(anIssue):
            aManager.AddFeature("Inconsistent Radius Milled Part Floor Fillet Issue(s)", "Floor Fillet(s)", True, anIssue)
        elif mtk.DFMMachining_NarrowRegionInPocketIssue.CompareType(anIssue):
            aManager.AddFeature("Narrow Region In Pocket Issue(s)", "Region(s)", True, anIssue)
        elif mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.CompareType(anIssue):
            aManager.AddFeature("Large Difference Regions Size In Pocket Issue(s)", "Region Size(s)", True, anIssue)
        #turning
        elif mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.CompareType(anIssue):
            aManager.AddFeature("Irregular Turned Part Outer Diameter Profile Relief Issue(s)", "Outer Diameter Profile Relief(s)", True, anIssue)
        elif mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.CompareType(anIssue):
            aManager.AddFeature("Small Radius Turned Part Internal Corner Issue(s)", "Internal Corner(s)", True, anIssue)
        elif mtk.DFMMachining_LargeTurnedPartIssue.CompareType(anIssue):
            aManager.AddFeature("Large Turned Part Issue(s)", "Part(s)", True, anIssue)
        elif mtk.DFMMachining_LongSlenderTurnedPartIssue.CompareType(anIssue):
            aManager.AddFeature("Long Slender Turned Part Issue(s)", "Part(s)", True, anIssue)
        elif mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.CompareType(anIssue):
            aManager.AddFeature("Small Depth Blind Bored Hole Relief Issue(s)", "Blind Bored Hole(s)", True, anIssue)
        elif mtk.DFMMachining_DeepBoredHoleIssue.CompareType(anIssue):
            aManager.AddFeature("Deep Bored Hole Issue(s)", "Bored Hole(s)", True, anIssue)
        elif mtk.DFMMachining_SquareEndKeywayIssue.CompareType(anIssue):
            aManager.AddFeature("Square End Keyway Issue(s)", "", False, anIssue)
        elif mtk.DFMMachining_NonSymmetricalAxialSlotIssue.CompareType(anIssue):
            aManager.AddFeature("Non Symmetrical Axial Slot Issue(s)", "", False, anIssue)

    aManager.Print ("issues", PrintFeatureParameters)

class PartProcessor(shape_processor.SolidProcessor):
    def __init__(self, theOperation):
        super().__init__()
        self.myOperation = theOperation

    def CombineFeatureLists(self, theFirst: mtk.MTKBase_FeatureList, theSecond: mtk.MTKBase_FeatureList):
        for anElement in theSecond:
            if (self.myOperation == mtk.Machining_OT_LatheMilling
                and mtk.DFMMachining_MillingIssue.CompareType(anElement)
                and not mtk.DFMMachining_DeepPocketIssue.CompareType(anElement)):
                continue
            theFirst.Append(anElement)

    def ProcessSolid(self, theSolid: cadex.ModelData_Solid):
        # Find features
        aData = mtk.Machining_Data()
        aRecognizer = mtk.Machining_FeatureRecognizer()
        aRecognizer.Parameters().SetOperation(self.myOperation)
        aRecognizer.Perform (theSolid, aData)

        # Run drilling analyzer for found features
        aDrillingParameters = mtk.DFMMachining_DrillingAnalyzerParameters()
        aDrillingAnalyzer = mtk.DFMMachining_Analyzer(aDrillingParameters)
        anIssueList = aDrillingAnalyzer.Perform(theSolid, aData)

        # Run milling analyzer for found features
        aMillingParameters = mtk.DFMMachining_MillingAnalyzerParameters()
        aMillingAnalyzer = mtk.DFMMachining_Analyzer(aMillingParameters)
        aMillingIssueList = aMillingAnalyzer.Perform(theSolid, aData)
        # Combine issue lists
        self.CombineFeatureLists(anIssueList, aMillingIssueList)

        aTurningIssueList = mtk.MTKBase_FeatureList()
        if self.myOperation == mtk.Machining_OT_LatheMilling:
            # Run turning analyzer for found features
            aTurninigParameters = mtk.DFMMachining_TurningAnalyzerParameters()
            aTurningAnalyzer = mtk.DFMMachining_Analyzer(aTurninigParameters)
            aTurningIssueList = aTurningAnalyzer.Perform(theSolid, aData)

            # Combine issue lists
            self.CombineFeatureLists(anIssueList, aTurningIssueList)

        PrintIssues(anIssueList)

def PrintSupportedOperations():
    print("Supported operations:")
    print("    milling:\t CNC Machining Milling feature recognition")
    print("    turning:\t CNC Machining Lathe+Milling feature recognition")

def OperationType(theOperationStr: str):
    aProcessMap = {
        "milling": mtk.Machining_OT_Milling,
        "turning": mtk.Machining_OT_LatheMilling
    }

    if theOperationStr in aProcessMap:
        return aProcessMap[theOperationStr]
    else:
        return mtk.Machining_OT_Undefined

def main(theSource: str, theOperationStr: str):
    aKey = license.Value()
    anMTKKey = mtk_license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1
    if not cadex.LicenseManager.Activate(anMTKKey):
        print("Failed to activate Manufacturing Toolkit license.")
        return 1
    aModel = cadex.ModelData_Model()
    aReader = cadex.ModelData_ModelReader()

    # Reading the file
    if not aReader.Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to open and convert the file " + theSource)
        return 1

    print("Model: ", aModel.Name(), "\n", sep="")

    anOperation = OperationType(theOperationStr)
    if anOperation == mtk.Machining_OT_Undefined:
        print("Unsupported operation - " , theOperationStr)
        print("Please use one of the following.")
        PrintSupportedOperations()
        return 1

    # Processing
    aPartProcessor = PartProcessor(anOperation)
    aVisitor = cadex.ModelData_SceneGraphElementUniqueVisitor(aPartProcessor)
    aModel.AcceptElementVisitor(aVisitor)

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: <input_file> <operation>, where:")
        print("    <input_file> is a name of the file to be read")
        print("    <operation> is a name of desired machining operation")
        PrintSupportedOperations()
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])
    anOperation = sys.argv[2]

    sys.exit(main(aSource, anOperation))
