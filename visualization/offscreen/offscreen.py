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
import cadexchanger.CadExView as view

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + r"/../../"))
import cadex_license as license


def main(theSource: str, theDest: str):
    aKey = license.Value()
    
    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1
    
    aReader = cadex.ModelData_ModelReader()
    aModel = cadex.ModelData_Model()
    
    # Reading the file
    if not aReader.Read(cadex.Base_UTF16String(theSource), aModel):
        print("Failed to read the file " + theSource)
        return 1
    
    # Convert model into visualization entities
    aFactory = view.ModelPrs_SceneNodeFactory()
    aRootNode = aFactory.CreateGraph(aModel, cadex.ModelData_RM_Any)
    aRootNode.SetDisplayMode(view.ModelPrs_DM_ShadedWithBoundaries)
    
    # Create scene and display all entities
    aScene = view.ModelPrs_Scene()
    aScene.AddRoot(aRootNode)
    
    # Setup offscreen viewport with transparent background and perspective camera
    aViewPort = view.ModelPrs_OffscreenViewPort()
    aViewPort.Resize(800, 600)
    aViewPort.SetCameraProjectionType(view.ModelPrs_CPT_Perspective)
    aViewPort.SetCameraPositionType(view.ModelPrs_CMT_Default)
    aBackgroundColor = cadex.ModelData_Color(0x00000000)
    aStyle = view.ModelPrs_BackgroundStyle(aBackgroundColor)
    aViewPort.SetBackgroundStyle(aStyle)
    
    # Attach viewport to the scene
    if not aViewPort.AttachToScene(aScene):
        print("Unable to attach viewport to scene")
        return 1
    
    # Apply scene changes to viewport and wait until all async operations will be finished
    aScene.Update()
    aScene.Wait()
    
    # Fit and center model on the image
    aViewPort.FitAll()
    
    # Grab rendered frame into image
    if not aViewPort.GrabToImage(cadex.Base_UTF16String(theDest)):
        print("Failed to write the file " + theDest)
        return 1
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("    <input_file>  is a name of the file to be read")
        print("    <output_file> is a name of the PNG file to save the model")
        sys.exit(1)

    aSource = os.path.abspath(sys.argv[1])
    aDest = os.path.abspath(sys.argv[2])

    sys.exit(main(aSource, aDest))
