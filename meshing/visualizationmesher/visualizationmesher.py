#!/usr/bin/env python3

# $Id$

# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2023, CADEX. All rights reserved.

# This file is part of the CAD Exchanger software.

# You may use this file under the terms of the BSD license as follows:

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
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
import cadexchanger.CadExMesh as mesh

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + r"/../../"))
import cadex_license as license

import math


class FirstFaceGetter(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self):
        cadex.ModelData_Model_VoidElementVisitor.__init__(self)
        self.myFace = None

    def VisitPart(self, thePart: cadex.ModelData_Part):
        if self.myFace is None:
            aBRep = thePart.BRepRepresentation()
            self.ExploreBRep(aBRep)

    def ExploreBRep(self, theBRep: cadex.ModelData_BRepRepresentation):
        aBodyList = theBRep.Get()
        aFirstBody = aBodyList.First()
        for aShape in cadex.ModelData_Shape_Iterator(aFirstBody, cadex.ModelData_ST_Face):
            self.myFace = cadex.ModelData_Face.Cast(aShape)
            break
            
    def FirstFace(self):
        return self.myFace

def PrintFaceToPolyAssociation(theFace: cadex.ModelData_Face,
                               theAssociations: cadex.ModelData_BRepToPolyAssociations):
    aMeshPatch = theAssociations.Get(theFace)
    anITS = cadex.ModelData_IndexedTriangleSet.Cast(aMeshPatch.PVS())
    aTriangleIndices = aMeshPatch.Indices()

    print(f"Face triangulation contains {len(aTriangleIndices)} triangles.")

    aNumberOfTrianglesToPrint = min(4, len(aTriangleIndices))

    for i in range(aNumberOfTrianglesToPrint):
        aTriangleIndex = aTriangleIndices.Element(i)
        print(f"Triangle index {aTriangleIndex} with vertices: ")
        for aVertexNumber in range(3):
            aVertexIndex = anITS.CoordinateIndex(aTriangleIndex, aVertexNumber);
            aPoint = anITS.Coordinate(aVertexIndex);
            print(f"  Vertex index {aVertexIndex} with coords",
                  f"(X: {aPoint.X()}, Y: {aPoint.Y()}, Z: {aPoint.Z()})")

def main(theSource: str):
    aKey = license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    aModel = cadex.ModelData_Model()

    if not cadex.ModelData_ModelReader().Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to read the file " + theSource)
        return 1

    # Set up mesher and parameters
    aParam = cadex.ModelAlgo_BRepMesherParameters()
    aParam.SetAngularDeflection(math.pi * 10 / 180)
    aParam.SetChordalDeflection(0.003)
    aParam.SetSaveBRepToPolyAssociations(True)

    aMesher = cadex.ModelAlgo_BRepMesher(aParam)
    aMesher.Compute(aModel, True)
    
    # Example of using B-Rep to Poly representation associations:
    aVisitor = FirstFaceGetter();
    aModel.AcceptElementVisitor(aVisitor);

    aFace = aVisitor.FirstFace();
    aBRepToPolyAssociations = aMesher.BRepToPolyAssociations();
    PrintFaceToPolyAssociation(aFace, aBRepToPolyAssociations)
    
    # Save the result
    if not cadex.ModelData_ModelWriter().Write(aModel, cadex.Base_UTF16String("out/VisMesher.cdx")):
        print("Unable to save the model")
        return 1

    print("Completed")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: " + os.path.abspath(Path(__file__).resolve()) + " <input_file>, where:")
        print("    <input_file>  is a name of the XML file to be read")
        sys.exit(1)

    aSource = os.path.abspath(sys.argv[1])

    sys.exit(main(aSource))
