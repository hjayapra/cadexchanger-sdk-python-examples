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
import cadexchanger.CadExMTK as mtk

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../../"))

import cadex_license as license
import mtk_license

def WriteToDrawing(theFlatPattern: mtk.SheetMetal_FlatPattern, theFilePath: str):
    aDrawing = theFlatPattern.ToDrawing();
    if aDrawing.IsNull():
        return False
    aDrawingModel = cadex.ModelData_Model()
    aDrawingModel.SetDrawing(aDrawing)
    aWriter = cadex.ModelData_ModelWriter()
    aRes = aWriter.Write(aDrawingModel, cadex.Base_UTF16String(theFilePath))
    return aRes

def PrintFlatPattern(theFlatPattern: mtk.SheetMetal_FlatPattern):
    print("    Flat Pattern with:")
    print("          length: ",    theFlatPattern.Length(),    " mm", sep="")
    print("          width: ",     theFlatPattern.Width(),     " mm", sep="")
    print("          thickness: ", theFlatPattern.Thickness(), " mm", sep="")
    print("          perimeter: ", theFlatPattern.Perimeter(), " mm", sep="")

def PrintFlatPatternAndWriteToDrawing(theFlatPattern: mtk.SheetMetal_FlatPattern, theDrawingFileName: str):
    if theFlatPattern.IsNull():
        print("    Failed to create flat pattern.")

    PrintFlatPattern(theFlatPattern)

    if WriteToDrawing(theFlatPattern, theDrawingFileName):
        print("    A drawing of the flat pattern has been saved to ", str(theDrawingFileName), sep="")
    else:
        print("    Failed to save drawing of the flat pattern to ", str(theDrawingFileName), sep="")

# Compute approximate thickness value, which can be used as the input thickness value for SheetMetal_Unfolder.
def CalculateInitialThicknessValue(theShape: cadex.ModelData_Shape):
    aVolume = cadex.ModelAlgo_ValidationProperty_ComputeVolume(theShape)
    aSurfaceArea = cadex.ModelAlgo_ValidationProperty_ComputeSurfaceArea(theShape)
    aThickness = aVolume / (aSurfaceArea / 2.0)
    return aThickness

class PartProcessor(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self, theDrawingFolderPath: str):
        super().__init__()
        self.myPartIndex = 0
        self.myUnfolder = mtk.SheetMetal_Unfolder()
        self.myDrawingFolderPath = theDrawingFolderPath

    def __DrawingFileName(self, thePartName: str, theShapeIndex: str, theShapeName: str):
        aPartName = "Part " + str(self.myPartIndex) + " [" + thePartName + "]"
        aShapeName = theShapeName + " " + str(theShapeIndex)
        aFileName = cadex.Base_UTF16String(self.myDrawingFolderPath + "/" + aPartName + " - " + aShapeName + " - drawing.dxf")
        return aFileName

    def ProcessSolid(self, theSolid: cadex.ModelData_Solid, thePartName: str, theShapeIndex: int):
        aThickness = CalculateInitialThicknessValue(theSolid)
        aFlatPattern = self.myUnfolder.Perform(theSolid, aThickness)
        aFileName = self.__DrawingFileName(thePartName, theShapeIndex, "solid")
        PrintFlatPatternAndWriteToDrawing(aFlatPattern, aFileName)

    def ProcessShell(self, theShell: cadex.ModelData_Shell, thePartName: str, theShapeIndex: int):
        aFlatPattern = self.myUnfolder.Perform(theShell)
        aFileName = self.__DrawingFileName(thePartName, theShapeIndex, "shell")
        PrintFlatPatternAndWriteToDrawing(aFlatPattern, aFileName)

    def VisitPart(self, thePart: cadex.ModelData_Part):
        aPartName = "noname" if thePart.Name().IsEmpty() else str(thePart.Name())
        aBRep = thePart.BRepRepresentation()
        if aBRep:
            aBodyList = aBRep.Get()
            i = 0
            for aBody in aBodyList:
                aShapeIt = cadex.ModelData_Shape_Iterator(aBody)
                for aShape in aShapeIt:
                    if aShape.Type() == cadex.ModelData_ST_Solid:
                        print("Part #", self.myPartIndex, " [\"", aPartName, "\"] - solid #", i, " has:", sep="")
                        self.ProcessSolid(cadex.ModelData_Solid.Cast(aShape), aPartName, i)
                        i += 1
                    elif aShape.Type() == cadex.ModelData_ST_Shell:
                        print("Part #", self.myPartIndex, " [\"", aPartName, "\"] - shell #", i, " has:", sep="")
                        self.ProcessShell(cadex.ModelData_Shell.Cast (aShape), aPartName, i)
                        i += 1
        self.myPartIndex += 1

def main(theSource: str, theDrawingPath: str):
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

    aPartProcessor = PartProcessor(theDrawingPath)
    aVisitor = cadex.ModelData_SceneGraphElementUniqueVisitor(aPartProcessor)
    aModel.AcceptElementVisitor(aVisitor)

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: <input_file> <output_folder>, where:")
        print("    <input_file> is a name of the file to be read")
        print("    <output_folder> is a name of the folder where DXF files with drawing to be written")
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])
    aRes = os.path.abspath(sys.argv[2])

    sys.exit(main(aSource, aRes))
