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

def HemTypeToString(theType):
    aHemTypeMap = {
        mtk.SheetMetal_HBT_Flattened: "Flattened Hem Bend(s)",
        mtk.SheetMetal_HBT_Open:      "Open Hem Bend(s)",
        mtk.SheetMetal_HBT_Teardrop:  "Teardrop Hem Bend(s)",
        mtk.SheetMetal_HBT_Rope:      "Rope Hem Bend(s)",
        mtk.SheetMetal_HBT_Rolled:    "Rolled Hem Bend(s)"
    }

    if theType in aHemTypeMap:
        return aHemTypeMap[theType]
    else:
        return "Hem Bend(s)"

def BendName(theBend: mtk.SheetMetal_Bend):
    if mtk.SheetMetal_HemBend.CompareType(theBend):
        aHemBend = mtk.SheetMetal_HemBend.Cast(theBend)
        return HemTypeToString(aHemBend.Type())
    elif mtk.SheetMetal_CurvedBend.CompareType(theBend):
        return "Curved Bend(s)"
    return "Bend(s)"

def HoleName(theHole: mtk.SheetMetal_Hole):
    if mtk.SheetMetal_ComplexHole.CompareType(theHole):
        return "Complex Hole(s)"
    return "Hole(s)"

def NotchName(theNotch: mtk.SheetMetal_Notch):
    if mtk.SheetMetal_StraightNotch.CompareType(theNotch):
        return "Straight Notch(es)"
    elif mtk.SheetMetal_VNotch.CompareType(theNotch):
        return "V Notch(es)"
    return "Notch(es)"

#group by parameters to provide more compact information about features
def GroupByParameters(theFeatureList: mtk.MTKBase_FeatureList, theManager: feature_group.FeatureGroupManager):
    for aFeature in theFeatureList:
        if mtk.SheetMetal_Bead.CompareType(aFeature):
            theManager.AddFeature("Bead(s)", "Bead(s)", True, aFeature)
        elif mtk.SheetMetal_Cutout.CompareType(aFeature):
            theManager.AddFeature("Cutout(s)", "Cutout(s)", True, aFeature)
        elif mtk.SheetMetal_Louver.CompareType(aFeature):
            theManager.AddFeature("Louver(s)", "", False, aFeature)
        elif mtk.SheetMetal_Bridge.CompareType(aFeature):
            theManager.AddFeature("Bridge(s)", "Bridge(s)", True, aFeature)
        elif mtk.SheetMetal_Hole.CompareType(aFeature):
            aHole = mtk.SheetMetal_Hole.Cast(aFeature)
            theManager.AddFeature(HoleName(aHole), "Hole(s)", True, aFeature)
        elif mtk.SheetMetal_Bend.CompareType(aFeature):
            aBend = mtk.SheetMetal_Bend.Cast(aFeature)
            theManager.AddFeature(BendName(aBend), "Bend(s)", True, aFeature)
        elif mtk.SheetMetal_Notch.CompareType(aFeature):
            aNotch = mtk.SheetMetal_Notch.Cast(aFeature)
            theManager.AddFeature(NotchName(aNotch), "Notch(es)", True, aFeature)
        elif mtk.SheetMetal_Tab.CompareType(aFeature):
            theManager.AddFeature("Tab(s)", "Tab(s)", True, aFeature)
        elif mtk.SheetMetal_CompoundBend.CompareType(aFeature):
            aCompoundBend = mtk.SheetMetal_CompoundBend.Cast(aFeature)
            GroupByParameters(aCompoundBend.FeatureList(), theManager)

def PrintFeatureParameters(theFeature: mtk.MTKBase_Feature):
    if mtk.SheetMetal_Bead.CompareType(theFeature):
        aBead = mtk.SheetMetal_Bead.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth", aBead.Depth(), "mm")
    elif mtk.SheetMetal_Cutout.CompareType(theFeature):
        aCutout = mtk.SheetMetal_Cutout.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("perimeter", aCutout.Perimeter(), "mm")
    elif mtk.SheetMetal_Louver.CompareType(theFeature):
        aLouver = mtk.SheetMetal_Louver.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aLouver.Depth(),  "mm")
    elif mtk.SheetMetal_Bridge.CompareType(theFeature):
        aBridge = mtk.SheetMetal_Bridge.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aBridge.Length(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aBridge.Depth(),  "mm")
    elif mtk.SheetMetal_Hole.CompareType(theFeature):
        aHole = mtk.SheetMetal_Hole.Cast(theFeature)
        anAxis = aHole.Axis().Axis()
        aDirection = feature_group.Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
        feature_group.FeatureGroupManager.PrintFeatureParameter("radius", aHole.Radius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aHole.Depth(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("axis",   aDirection,     "")
    elif mtk.SheetMetal_Bend.CompareType(theFeature):
        aBend = mtk.SheetMetal_Bend.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("radius", aBend.Radius(),            "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("angle",  ToDegrees (aBend.Angle()), "deg")
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aBend.Length(),            "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("width",  aBend.Width(),             "mm")
    elif mtk.SheetMetal_Notch.CompareType(theFeature):
        aNotch = mtk.SheetMetal_Notch.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aNotch.Length(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("width",  aNotch.Width(),  "mm")
        if mtk.SheetMetal_StraightNotch.CompareType(aNotch):
            aStraightNotch = mtk.SheetMetal_StraightNotch.Cast(aNotch)
            feature_group.FeatureGroupManager.PrintFeatureParameter ("corner fillet radius", aStraightNotch.CornerFilletRadius(), "mm")
        elif mtk.SheetMetal_VNotch.CompareType(aNotch):
            aVNotch = mtk.SheetMetal_VNotch.Cast(aNotch)
            feature_group.FeatureGroupManager.PrintFeatureParameter ("angle", ToDegrees (aVNotch.Angle()), "deg")
    elif mtk.SheetMetal_Tab.CompareType(theFeature):
        aTab = mtk.SheetMetal_Tab.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aTab.Length(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("width",  aTab.Width(),  "mm")

def PrintFeatures(theFeatureList: mtk.MTKBase_FeatureList):
    aManager = feature_group.FeatureGroupManager()
    GroupByParameters (theFeatureList, aManager)
    aManager.Print ("features", PrintFeatureParameters)

# Compute approximate thickness value, which can be used as the input thickness value for SheetMetal_FeatureRecognizer.
def CalculateInitialThicknessValue(theShape: cadex.ModelData_Shape):
    aVolume = cadex.ModelAlgo_ValidationProperty_ComputeVolume(theShape)
    aSurfaceArea = cadex.ModelAlgo_ValidationProperty_ComputeSurfaceArea(theShape)
    aThickness = aVolume / (aSurfaceArea / 2.0)
    return aThickness

class PartProcessor(shape_processor.ShapeProcessor):
    def __init__(self):
        super().__init__()
        self.myRecognizer = mtk.SheetMetal_FeatureRecognizer()

    def ProcessSolid(self, theSolid: cadex.ModelData_Solid):
        aThickness = CalculateInitialThicknessValue(theSolid)
        aFeatureList = self.myRecognizer.Perform(theSolid, aThickness)
        PrintFeatures(aFeatureList)

    def ProcessShell(self, theShell: cadex.ModelData_Shell):
        aFeatureList = self.myRecognizer.Perform(theShell)
        PrintFeatures(aFeatureList)

def main(theSource: str):
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

    # Opening the file
    if not aReader.Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to open and convert the file " + theSource)
        return 1

    print("Model: ", aModel.Name(), "\n", sep="")

    # Processing
    aPartProcessor = PartProcessor()
    aVisitor = cadex.ModelData_SceneGraphElementUniqueVisitor(aPartProcessor)
    aModel.AcceptElementVisitor(aVisitor)

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: <input_file>, where:")
        print("    <input_file> is a name of the file to be read")
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])

    sys.exit(main(aSource))
