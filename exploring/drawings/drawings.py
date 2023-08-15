#!/usr/bin/env python3

#  $Id$

# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2023, CADEX. All rights reserved.

# This file is part of the CAD Exchanger software.

# You may use this file under the terms of the BSD license as follows:

# Redistribution and use in source and binary forms, with or without
# cadex.modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

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

import sys
from pathlib import Path
import os

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExDWG as dwg

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + r"/../../"))
import cadex_license as license

class DrawingElementCounter(cadex.ModelData_DrawingElementVoidVisitor):
    def __init__(self):
        super().__init__()
        self.myDrawingElementsNumber = {}
        self.myCurves2DNumber = {}
        self.myPoint2DNumber = 0

    def VisitDrawingAngularDimension(self, theElement: cadex.ModelData_DrawingAngularDimension):
        self.CountElement(theElement)

    def VisitDrawingCurveSet(self, theElement: cadex.ModelData_DrawingCurveSet):
        self.CountElement(theElement)
        for i in range(theElement.NumberOfCurves()):
            self.CountCurve2d(theElement.Curve(i))

    def VisitDrawingDiametricDimension(self, theElement: cadex.ModelData_DrawingDiametricDimension):
        self.CountElement(theElement)

    def VisitDrawingHatch(self, theElement: cadex.ModelData_DrawingHatch):
        self.CountElement(theElement)

    def VisitDrawingLinearDimension(self, theElement: cadex.ModelData_DrawingLinearDimension):
        self.CountElement(theElement)

    def VisitDrawingPiecewiseContour(self, theElement: cadex.ModelData_DrawingPiecewiseContour):
        self.CountElement(theElement)
        for i in range(theElement.NumberOfCurves()):
            self.CountCurve2d(theElement.Curve(i))

    def VisitDrawingPointSet(self, theElement: cadex.ModelData_DrawingPointSet):
        self.CountElement(theElement)
        self.myPoint2DNumber += theElement.NumberOfPoints()

    def VisitDrawingRadialDimension(self, theElement: cadex.ModelData_DrawingRadialDimension):
        self.CountElement(theElement)

    def VisitDrawingText(self, theElement: cadex.ModelData_DrawingText):
        self.CountElement(theElement)

    def Print(self):
        print("\nDrawing Elements in the model view:")
        for key, value in self.myDrawingElementsNumber.items():
            print(f"{PrintDrawingElementType(key)}: {value}")

        print("\n2D Geometry in the model view:")
        if (self.myPoint2DNumber != 0):
            print(f"Points: {self.myPoint2DNumber}")
        for key, value in self.myCurves2DNumber.items():
            print(f"{PrintCurveType(key)}: {value}")

    # Count drawing elements in the model, grouped by type
    def CountElement(self, theElement: cadex.ModelData_DrawingElement):
        aType = theElement.TypeId()
        aCount = self.myDrawingElementsNumber.get(aType, 0)
        self.myDrawingElementsNumber[aType] = aCount + 1

    def CountCurve2d(self, theCurve: cadex.ModelData_Curve2d):
        aType = theCurve.Type()
        aCount = self.myCurves2DNumber.get(aType, 0)
        self.myCurves2DNumber[aType] = aCount + 1

#Count 2d curves in the model, grouped by type
def PrintCurveType(theType) -> str:
    if theType == cadex.ModelData_CT_Line:
        return "Lines"
    elif theType == cadex.ModelData_CT_Circle:
        return "Circles"
    elif theType == cadex.ModelData_CT_Ellipse:
        return "Ellipses"
    elif theType == cadex.ModelData_CT_Hyperbola:
        return "Hyperbolas"
    elif theType == cadex.ModelData_CT_Parabola:
        return "Parabolas"
    elif theType == cadex.ModelData_CT_Bezier:
        return "Bezier Curves"
    elif theType == cadex.ModelData_CT_BSpline:
        return "BSpline Curves"
    elif theType == cadex.ModelData_CT_Offset:
        return "Offset Curves"
    elif theType == cadex.ModelData_CT_Trimmed:
        return "Trimmed Curves"
    return "Undefined"

def PrintDrawingElementType(theType) -> str:
    if theType == cadex.ModelData_DrawingAngularDimension_GetTypeId():
        return "Angular Dimensions"
    elif theType == cadex.ModelData_DrawingDiametricDimension_GetTypeId():
        return "Diametric Dimensions"
    elif theType == cadex.ModelData_DrawingHatch_GetTypeId():
        return "Hatches"
    elif theType == cadex.ModelData_DrawingLinearDimension_GetTypeId():
        return "Linear Dimensions"
    elif theType == cadex.ModelData_DrawingPiecewiseContour_GetTypeId():
        return "Piecewise Contours"
    elif theType == cadex.ModelData_DrawingPointSet_GetTypeId():
        return "Point Sets"
    elif theType == cadex.ModelData_DrawingRadialDimension_GetTypeId():
        return "Radial Dimensions"
    elif theType == cadex.ModelData_DrawingText_GetTypeId():
        return "Texts"
    elif theType == cadex.ModelData_DrawingCurveSet_GetTypeId():
        return "Curve Sets"
    return "Undefined elements"

def GetName(theObject: cadex.ModelData_BaseObject) -> str:
    if theObject.Name().IsEmpty():
        return "Unnamed"
    return theObject.Name()

def main(theSource: str):
    aKey = license.Value()
    
    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    # Open a model
    aModel = cadex.ModelData_Model()
    aReader = cadex.ModelData_ModelReader()

    # Enable reading drawing data
    aParams = dwg.DWG_ReaderParameters()
    aParams.SetReadDrawing(True)
    aReader.SetReaderParameters(aParams)

    if not aReader.Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to read the file " + theSource)
        return 1

    # Drawing structure traversal
    aDrawing = aModel.Drawing()
    print(f"Drawing <{GetName(aDrawing)}>: {aDrawing.NumberOfSheets()} sheets")
    for aSheet in aDrawing.GetSheetIterator():
        print(f"Sheet <{GetName(aSheet)}>: {aSheet.NumberOfViews()} views")
        for aView in aSheet.GetViewIterator():
            print(f"View <{GetName(aView)}>: {aView.NumberOfElements()} elements")
            aCounter = DrawingElementCounter()
            aView.Accept(aCounter)
            aCounter.Print()

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: " + os.path.abspath(Path(__file__).resolve()) + " <input_file>, where:")
        print("    <input_file>  is a name of the DWG file to be read")
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])

    sys.exit(main(aSource))
