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

 # Creates a "unique" color
def CreateColor(theColorId: int) -> cadex.ModelData_Color:
        r = (theColorId * 61) % 256
        g = (theColorId * 101) % 256
        b = (theColorId * 151) % 256
        a = 255

        return cadex.ModelData_Color(r, g, b, a)

def CreateAppearance(theAppearanceId: int) -> cadex.ModelData_Appearance:
        aMaterial = cadex.ModelData_Material()
        aMaterial.SetDiffuseColor(CreateColor(theAppearanceId))
        aMaterial.SetAmbientColor(cadex.ModelData_Color(0.24725, 0.1995, 0.0745))
        aMaterial.SetSpecularColor(cadex.ModelData_Color(0.75164, 0.60648, 0.22648))
        aMaterial.SetEmissionColor(cadex.ModelData_Color(0.2, 0.2, 0.2))
        aMaterial.SetShininess(83.2)

        anAppearance = cadex.ModelData_Appearance(aMaterial)

        aLineProperties = cadex.ModelData_LineProperties()
        aLineProperties.SetType(cadex.ModelData_LineProperties.Dotted)
        anAppearance.Set(aLineProperties)

        return anAppearance

class SubshapeAppearanceModifier(cadex. ModelData_BRepRepresentation_SubshapeVisitor):
    def __init__(self, theBRep: cadex.ModelData_BRepRepresentation, theAppearanceId: int):
        super().__init__()
        self.myBRep = theBRep
        self.myAppearanceId = theAppearanceId
    
    def VisitShape(self, theShape: cadex.ModelData_Shape):
        anAppearance = self.myBRep.Appearance(theShape)
        if anAppearance:
            self.myBRep.SetAppearance(theShape, CreateAppearance(self.myAppearanceId))

class RepresentationAppearanceModifier(cadex.ModelData_Part_RepresentationVisitor):
    def __init__(self, theAppearanceId: int):
        super().__init__()
        self.myAppearanceId = theAppearanceId
    
    def VisitBRep(self, theBRep: cadex.ModelData_BRepRepresentation):
        aBRep = theBRep
        aBodyList = aBRep.Get()

        for aBody in aBodyList:
            anAppearance = aBRep.Appearance(aBody)
            if anAppearance:
                aBRep.SetAppearance(aBody, anAppearance)
        
        aModifier = SubshapeAppearanceModifier(theBRep, self.myAppearanceId)
        theBRep.Accept(aModifier)

    def VisitPoly(self, thePolyRep: cadex.ModelData_PolyRepresentation):
        aPolyRep = thePolyRep
        aPolyList = aPolyRep.Get()

        for aPoly in aPolyList:
            if aPoly.TypeId() == cadex.ModelData_IndexedTriangleSet.GetTypeId():
                anITS = cadex.ModelData_IndexedTriangleSet.Cast(aPoly) 
                anAppearance = anITS.Appearance()
                if anAppearance:
                    anITS.SetAppearance(CreateAppearance(self.myAppearanceId))

class SceneGraphAppearanceModifier(cadex.ModelData_Model_VoidElementVisitor):
    def __init__(self, theAppearanceId = 0):
        super().__init__()
        self.myAppearanceId = theAppearanceId

    def VisitPart(self, thePart: cadex.ModelData_Part):
        aPart = thePart
        anAppearance = aPart.Appearance()

        if anAppearance:
            self.myAppearanceId += 1
            aPart.SetAppearance(CreateAppearance(self.myAppearanceId))
        
        aModifier = RepresentationAppearanceModifier(self.myAppearanceId)
        thePart.Accept(aModifier)

    def VisitEnterAssembly(self, theAssembly: cadex.ModelData_Assembly):
        anAssembly = theAssembly
        anAppearance = anAssembly.Appearance()

        if anAppearance:
            self.myAppearanceId += 1
            anAssembly.SetAppearance(CreateAppearance(self.myAppearanceId))

        return True
    
    def VisitEnterInstance(self, theInstance: cadex.ModelData_Instance):
        anInstance = theInstance
        anAppearance = anInstance.Appearance()

        if anAppearance:
            self.myAppearanceId += 1
            anInstance.SetAppearance(CreateAppearance(self.myAppearanceId))
        

        return True

def main(theSource: str, theDest: str):
    aKey = license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1

    aModel = cadex.ModelData_Model()
    aReader = cadex.ModelData_ModelReader()

    # Opening and converting the file
    if not aReader.Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to open and convert the file " + theSource)
        return 1

    aModifier = SceneGraphAppearanceModifier()
    aUniqueModifier = cadex.ModelData_SceneGraphElementUniqueVisitor(aModifier)

    # Modifying the appearance of the model  
    aModel.AcceptElementVisitor(aUniqueModifier)

    aWriter = cadex.ModelData_ModelWriter()

    # Converting and writing the model to file
    if not aWriter.Write(aModel, cadex.Base_UTF16String(theDest)):
        print("Failed to convert and write the file to specified format " + theDest)
        return 1

    print("Completed")
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("    <input_file>  is a name of the model file to be read")
        print("    <output_file> is a name of the model file to Save() the model")     
        sys.exit()

    aSource = os.path.abspath(sys.argv[1])
    aDest = os.path.abspath(sys.argv[2])

    sys.exit(main(aSource, aDest))
