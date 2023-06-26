#!/usr/bin/env python3

#  $Id$

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

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + r"/../../"))
import cadex_license as license


class BimStructureVisitor(cadex.ModelData_BIMElementVisitor):
    def __init__(self):
        super().__init__()
        self.myNestingLevel = 0
        self.myCounts = {}

    def AddCounts(self, theElementType):
        self.myCounts[theElementType] = self.myCounts.get(theElementType, 0) + 1

    def PrintCounts(self):
        print("Element Types:")
        for eltype, count in self.myCounts.items():
            print("{0}: {1}".format(eltype, count))

    def GetFiller(self):
        return "-" * 4 * self.myNestingLevel

    def VisitEnterBIMBuilding(self, theElement: cadex.ModelData_BIMBuilding) -> bool:
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Building")
        self.myNestingLevel += 1
        return True

    def VisitLeaveBIMBuilding(self, theElement: cadex.ModelData_BIMBuilding):
        self.myNestingLevel -= 1

    def VisitEnterBIMSite(self, theElement: cadex.ModelData_BIMSite) -> bool:
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Site")
        self.myNestingLevel += 1
        return True

    def VisitLeaveBIMSite(self, theElement: cadex.ModelData_BIMSite):
        self.myNestingLevel -= 1

    def VisitEnterBIMSpace(self, theElement: cadex.ModelData_BIMSpace) -> bool:
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Space")
        self.myNestingLevel += 1
        return True

    def VisitLeaveBIMSpace(self, theElement: cadex.ModelData_BIMSpace):
        self.myNestingLevel -= 1

    def VisitEnterBIMStorey(self, theElement: cadex.ModelData_BIMStorey) -> bool:
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Storey")
        self.myNestingLevel += 1
        return True

    def VisitLeaveBIMStorey(self, theElement: cadex.ModelData_BIMStorey):
        self.myNestingLevel -= 1

    def VisitBIMBeam(self, theElement: cadex.ModelData_BIMBeam):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Beam")

    def VisitBIMColumn(self, theElement: cadex.ModelData_BIMColumn):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Column")

    def VisitBIMDoor(self, theElement: cadex.ModelData_BIMDoor):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Door")

    def VisitBIMFurniture(self, theElement: cadex.ModelData_BIMFurniture):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Furniture")

    def VisitBIMPlate(self, theElement: cadex.ModelData_BIMPlate):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Plate")

    def VisitBIMRailing(self, theElement: cadex.ModelData_BIMRailing):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Railing")

    def VisitBIMRoof(self, theElement: cadex.ModelData_BIMRoof):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Roof")

    def VisitBIMSlab(self, theElement: cadex.ModelData_BIMSlab):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Slab")

    def VisitBIMStair(self, theElement: cadex.ModelData_BIMStair):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Stair")

    def VisitBIMCustomGeometryElement(self, theElement: cadex.ModelData_BIMCustomGeometryElement):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("CustomGeometryElement")

    def VisitBIMWall(self, theElement: cadex.ModelData_BIMWall):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Wall")

    def VisitBIMWindow(self, theElement: cadex.ModelData_BIMWindow):
        print(self.GetFiller(), theElement.Name())
        self.AddCounts("Window")


def main(theSource: str):
    aKey = license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    aModel = cadex.ModelData_BIMModel()
    # Reading and converting the file
    if not cadex.ModelData_ModelReader().ReadBIM(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to read the file: " + theSource)
        return 1

    aCounter = BimStructureVisitor()
    aModel.Accept(aCounter)

    print()
    aCounter.PrintCounts()

    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: " + os.path.abspath(Path(__file__).resolve()) + " <input_file>, where:")
        print("    <input_file>  is a name of the IFC file to be read")
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])

    sys.exit(main(aSource))
