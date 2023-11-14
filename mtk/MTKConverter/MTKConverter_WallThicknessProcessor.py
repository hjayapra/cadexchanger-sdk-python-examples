# $Id$

# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2023, CADEX. All rights reserved.

# This file is part of the CAD Exchanger software.

# You may use this file under the terms of the BSD license as follows:

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

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

from sys import float_info

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK as mtk

import MTKConverter_PartProcessor as part_proc

class PointPair:
    def __init__(self, theFirst: cadex.ModelData_Point, theSecond: cadex.ModelData_Point):
        self.First = theFirst
        self.Second = theSecond

class MTKConverter_WallThicknessData(part_proc.MTKConverter_ProcessData):
    def __init__(self, thePart: cadex.ModelData_Part):
        super().__init__(thePart)
        self.myIsInit = False
        self.myMinThickness = float_info.max
        self.myMaxThickness = -float_info.max
        self.myMinThicknessPoints = PointPair(cadex.ModelData_Point(), cadex.ModelData_Point())
        self.myMaxThicknessPoints = PointPair(cadex.ModelData_Point(), cadex.ModelData_Point())

class MTKConverter_WallThicknessProcessor(part_proc.MTKConverter_VoidPartProcessor):
    def __init__(self, theResolution: int):
        super().__init__()
        self.myAnalyzer = mtk.WallThickness_Analyzer()
        self.myResolution = theResolution

    def __UpdateProcessData(self, theData: mtk.WallThickness_Data, thePart: cadex.ModelData_Part):
        aWTData = MTKConverter_WallThicknessData(thePart)
        self.myData.append(aWTData)

        if theData.IsEmpty():
            return

        aWTData.myIsInit = True
        if aWTData.myMinThickness > theData.MinThickness():
            aWTData.myMinThickness = theData.MinThickness()
            theData.PointsOfMinThickness(aWTData.myMinThicknessPoints.First, aWTData.myMinThicknessPoints.Second)

        if aWTData.myMaxThickness < theData.MaxThickness():
            aWTData.myMaxThickness = theData.MaxThickness()
            theData.PointsOfMaxThickness(aWTData.myMaxThicknessPoints.First, aWTData.myMaxThicknessPoints.Second)

    def ProcessSolid(self, thePart: cadex.ModelData_Part, theSolid: cadex.ModelData_Solid):
        aWTData = self.myAnalyzer.Perform(theSolid, self.myResolution)
        self.__UpdateProcessData(aWTData, thePart)

    def ProcessMesh (self, thePart: cadex.ModelData_Part, theMesh: cadex.ModelData_IndexedTriangleSet):
        aWTData = self.myAnalyzer.Perform(theMesh, self.myResolution)
        self.__UpdateProcessData(aWTData, thePart)

