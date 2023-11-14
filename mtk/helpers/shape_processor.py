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

from abc import abstractmethod

import cadexchanger.CadExCore as cadex

class ShapeProcessor(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self):
        super().__init__()
        self.myPartIndex = 0

    def VisitPart(self, thePart: cadex.ModelData_Part):
        aPartName = "noname" if thePart.Name().IsEmpty() else thePart.Name()
        aBRep = thePart.BRepRepresentation()
        if aBRep:
            aBodyList = aBRep.Get()
            i = 0
            for aBody in aBodyList:
                aShapeIt = cadex.ModelData_Shape_Iterator(aBody)
                for aShape in aShapeIt:
                    if aShape.Type() == cadex.ModelData_ST_Solid:
                        print("Part #", self.myPartIndex, " [\"", aPartName, "\"] - solid #", i, " has:", sep="")
                        i += 1
                        self.ProcessSolid(cadex.ModelData_Solid.Cast(aShape))
                    elif aShape.Type() == cadex.ModelData_ST_Shell:
                        print("Part #", self.myPartIndex, " [\"", aPartName, "\"] - shell #", i, " has:", sep="")
                        i += 1
                        self.ProcessShell(cadex.ModelData_Shell.Cast (aShape))
        self.myPartIndex += 1

    @abstractmethod
    def ProcessSolid(self, theSolid: cadex.ModelData_Solid):
        pass

    @abstractmethod
    def ProcessShell(self, theShell: cadex.ModelData_Shell):
        pass

class SolidProcessor(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self):
        super().__init__()
        self.myPartIndex = 0

    def VisitPart(self, thePart: cadex.ModelData_Part):
        aPartName = "noname" if thePart.Name().IsEmpty() else thePart.Name()
        aBRep = thePart.BRepRepresentation()
        if aBRep:
            aBodyList = aBRep.Get()
            i = 0
            for aBody in aBodyList:
                aShapeIt = cadex.ModelData_Shape_Iterator(aBody)
                for aShape in aShapeIt:
                    if aShape.Type() == cadex.ModelData_ST_Solid:
                        print("Part #", self.myPartIndex, " [\"", aPartName, "\"] - solid #", i, " has:", sep="")
                        i += 1
                        self.ProcessSolid (cadex.ModelData_Solid.Cast (aShape))
        self.myPartIndex += 1

    @abstractmethod
    def ProcessSolid(self, theSolid: cadex.ModelData_Solid):
        pass
