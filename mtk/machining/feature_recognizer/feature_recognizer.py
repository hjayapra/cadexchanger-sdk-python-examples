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

import os
import sys

from pathlib import Path

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK  as mtk

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../../"))
sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../helpers/"))

import cadex_license as license
import mtk_license

import shape_processor
import feature_group

def FaceTypeToString(theType):
    aFaceTypeMap = {
        mtk.Machining_FT_FlatFaceMilled:           "Flat Face Milled Face(s)",
        mtk.Machining_FT_FlatSideMilled:           "Flat Side Milled Face(s)",
        mtk.Machining_FT_CurvedMilled:             "Curved Milled Face(s)",
        mtk.Machining_FT_CircularMilled:           "Circular Milled Face(s)",
        mtk.Machining_FT_Deburr:                   "Deburr Face(s)",
        mtk.Machining_FT_ConvexProfileEdgeMilling: "Convex Profile Edge Milling Face(s)",
        mtk.Machining_FT_ConcaveFilletEdgeMilling: "Concave Fillet Edge Milling Face(s)",
        mtk.Machining_FT_FlatMilled:               "Flat Milled Face(s)",
        mtk.Machining_FT_TurnDiameter:             "Turn Diameter Face(s)",
        mtk.Machining_FT_TurnForm:                 "Turn Form Face(s)",
        mtk.Machining_FT_TurnFace:                 "Turn Face Face(s)",
        mtk.Machining_FT_Bore:                     "Bore Face(s)"
    }

    if theType in aFaceTypeMap:
        return aFaceTypeMap[theType]
    else:
        return "Face(s)"

def HoleTypeToString(theType):
    aHoleTypeMap = {
        mtk.Machining_HT_Through:    "Through Hole(s)",
        mtk.Machining_HT_FlatBottom: "Flat Bottom Hole(s)",
        mtk.Machining_HT_Blind:      "Blind Hole(s)",
        mtk.Machining_HT_Partial:    "Partial Hole(s)"
    }

    if theType in aHoleTypeMap:
        return aHoleTypeMap[theType]
    else:
        return "Hole(s)"

def PrintFeatureParameters(theFeature: mtk.MTKBase_Feature):
    if mtk.Machining_TurningFace.CompareType(theFeature):
        aTurningFace = mtk.Machining_TurningFace.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("radius", aTurningFace.Radius(), "mm")
    elif mtk.Machining_Face.CompareType(theFeature):
        pass #no parameters
    elif mtk.Machining_Countersink.CompareType(theFeature):
        aCountersink = mtk.Machining_Countersink.Cast(theFeature)
        anAxis = aCountersink.Axis().Axis()
        aDirection = feature_group.Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
        feature_group.FeatureGroupManager.PrintFeatureParameter("radius", aCountersink.Radius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aCountersink.Depth(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("axis",   aDirection,            "")
    elif mtk.Machining_Hole.CompareType(theFeature):
        aHole = mtk.Machining_Hole.Cast(theFeature)
        anAxis = aHole.Axis().Axis()
        aDirection = feature_group.Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
        feature_group.FeatureGroupManager.PrintFeatureParameter("radius", aHole.Radius(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aHole.Depth(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("axis",   aDirection,     "")
    elif mtk.Machining_Pocket.CompareType(theFeature):
        aPocket = mtk.Machining_Pocket.Cast(theFeature)
        anAxis = aPocket.Axis().Direction()
        aDirection = feature_group.Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aPocket.Length(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("width",  aPocket.Width(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("depth",  aPocket.Depth(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("axis",   aDirection,       "")
    elif mtk.MTKBase_Boss.CompareType(theFeature):
        aBoss = mtk.MTKBase_Boss.Cast(theFeature)
        feature_group.FeatureGroupManager.PrintFeatureParameter("length", aBoss.Length(), "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("width",  aBoss.Width(),  "mm")
        feature_group.FeatureGroupManager.PrintFeatureParameter("height", aBoss.Height(), "mm")

def PrintFeatures(theFeatureList: mtk.MTKBase_FeatureList):
    aManager = feature_group.FeatureGroupManager()

    #group by parameters to provide more compact information about features
    for aFeature in theFeatureList:
        if mtk.Machining_TurningFace.CompareType(aFeature):
            aTurningFace = mtk.Machining_TurningFace.Cast(aFeature)
            aManager.AddFeature(FaceTypeToString (aTurningFace.Type()), "Turning Face(s)", True, aFeature)
        elif mtk.Machining_Face.CompareType(aFeature):
            aFace = mtk.Machining_Face.Cast(aFeature)
            aManager.AddFeature(FaceTypeToString (aFace.Type()), "", False, aFeature)
        elif mtk.Machining_Countersink.CompareType(aFeature):
            aManager.AddFeature("Countersink(s)", "Countersink(s)", True, aFeature)
        elif mtk.Machining_Hole.CompareType(aFeature):
            aHole = mtk.Machining_Hole.Cast(aFeature)
            aManager.AddFeature(HoleTypeToString (aHole.Type()), "Hole(s)", True, aFeature)
        elif mtk.Machining_Pocket.CompareType(aFeature):
            aManager.AddFeature("Pocket(s)", "Pocket(s)", True, aFeature)
        elif mtk.MTKBase_Boss.CompareType(aFeature):
            aManager.AddFeature("Boss(es)", "Boss(es)", True, aFeature)

    aManager.Print ("features", PrintFeatureParameters)

class PartProcessor(shape_processor.SolidProcessor):
    def __init__(self, theOperation): # Not imported swig: mtk.Machining_OperationType?
        super().__init__()
        self.myOperation = theOperation

    def ProcessSolid(self, theSolid: cadex.ModelData_Solid):
        aRecognizer = mtk.Machining_FeatureRecognizer()
        aRecognizer.Parameters().SetOperation (self.myOperation)
        aFeatureList = aRecognizer.Perform (theSolid)
        PrintFeatures(aFeatureList)

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
        print("Unsupported operation - ", theOperationStr, sep="")
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
        print("Usage:")
        print("    <input_file> is a name of the file to be read")
        print("    <operation> is a name of desired machining operation")
        PrintSupportedOperations()
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])
    anOperation = sys.argv[2]

    sys.exit(main(aSource, anOperation))
