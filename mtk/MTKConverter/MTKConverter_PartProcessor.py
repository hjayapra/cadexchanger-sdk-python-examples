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

from abc import abstractmethod

import cadexchanger.CadExCore as cadex

class MTKConverter_ProcessData:
    def __init__(self, thePart: cadex.ModelData_Part):
        self.myPart = thePart

class MTKConverter_PartProcessor(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self):
        super().__init__()
        self.myData = []

    def VisitPart(self, thePart: cadex.ModelData_Part):
        aBRep = thePart.BRepRepresentation()
        if aBRep:
            aBodyList = aBRep.Get()
            for aBody in aBodyList:
                aShapeIt = cadex.ModelData_Shape_Iterator(aBody)
                for aShape in aShapeIt:
                    if aShape.Type() == cadex.ModelData_ST_Solid:
                        self.ProcessSolid(thePart, cadex.ModelData_Solid.Cast(aShape))
                    elif aShape.Type() == cadex.ModelData_ST_Shell:
                        self.ProcessShell(thePart, cadex.ModelData_Shell.Cast(aShape))
        else:
            aPolyRep = thePart.PolyRepresentation (cadex.ModelData_RM_Poly)
            if not aPolyRep.IsNull():
                aPolyList = aPolyRep.Get()
                for aPVS in aPolyList:
                    if aPVS.TypeId() == cadex.ModelData_IndexedTriangleSet.GetTypeId():
                        self.ProcessMesh (thePart, cadex.ModelData_IndexedTriangleSet.Cast(aPVS))

        self.PostPartProcess (thePart)

    @abstractmethod
    def ProcessSolid(self, thePart: cadex.ModelData_Part, theSolid: cadex.ModelData_Solid):
        pass

    @abstractmethod
    def ProcessShell(self, thePart: cadex.ModelData_Part, theShell: cadex.ModelData_Shell):
        pass

    @abstractmethod
    def ProcessMesh(self, thePart: cadex.ModelData_Part, theShell: cadex.ModelData_IndexedTriangleSet):
        pass

    @abstractmethod
    def PostPartProcess(self, thePart: cadex.ModelData_Part):
        pass

class MTKConverter_VoidPartProcessor(MTKConverter_PartProcessor):
    def __init__(self):
        super().__init__()

    def ProcessSolid (self, thePart :cadex.ModelData_Part, theSolid: cadex.ModelData_Solid):
        pass

    def ProcessShell (self, thePart :cadex.ModelData_Part, theShell: cadex.ModelData_Shell):
        pass

    def ProcessMesh  (self, thePart :cadex.ModelData_Part, theITS: cadex.ModelData_IndexedTriangleSet):
        pass

    def PostPartProcess(self, thePart: cadex.ModelData_Part):
        pass

