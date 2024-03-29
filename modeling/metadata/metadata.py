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

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + r"/../../"))
import cadex_license as license


def main():
    aKey = license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    # Create a simple box
    aBox = cadex.ModelAlgo_TopoPrimitives.CreateBox(5.0, 5.0, 5.0)
    aBRep = cadex.ModelData_BRepRepresentation(aBox)

    # Color the box
    aFaceIt = cadex.ModelData_Shape_Iterator(aBox, cadex.ModelData_ST_Face)
    r = 10
    g = 10
    b = 250
    a = 255
    for aFace in aFaceIt:
        r += 30
        b -= 30
        anApp = cadex.ModelData_Appearance(cadex.ModelData_Color(r, g, b, a))
        aBRep.SetAppearance(aFace, anApp)

    # Change properties
    aPart = cadex.ModelData_Part(aBRep, cadex.Base_UTF16String("ColorBox"))
    aTable = cadex.ModelData_PropertyTable()
    aTable.AddUTF16String(cadex.Base_UTF16String("Color"), cadex.Base_UTF16String("Different"))
    aPart.AddProperties(aTable)

    aModel = cadex.ModelData_Model()
    aModel.AddRoot(aPart)
    cadex.ModelData_ModelWriter().Write(aModel, cadex.Base_UTF16String("out/ColorBox.cdx"))

    print("Completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())

