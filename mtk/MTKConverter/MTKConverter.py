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

import os
import sys

from pathlib import Path

import cadexchanger.CadExCore as cadex

sys.path.append(os.path.abspath(os.path.dirname(Path(__file__).resolve()) + "/../../"))

import cadex_license as license
import mtk_license

import MTKConverter_Application as app

def PrintUsage():
    print ("Usage:")
    print ("MTKConverter -i <import_file> -p <process> -e <export_folder>\n")
    print ("Arguments:")
    print ("  <import_file> - import file name")
    print ("  <process> - manufacturing process or algorithm name")
    print ("  <export_folder> - export folder name")
    print ("Example:")
    print ("MTKConverter -i C:\\models\\test.step -p machining_milling -e C:\\models\\test")

    print ("\nRecognized processes:")
    print ("  wall_thickness   :\t Wall Thickness analysis")
    print ("  machining_milling:\t CNC Machining Milling feature recognition and dfm analyzis")
    print ("  machining_turning:\t CNC Machining Lathe+Milling feature recognition and dfm analyzis")
    print ("  sheet_metal      :\t Sheet Metal feature recognition, unfolding and dfm analysis")

def main (theSource: str, theProcess: str, theTarget: str):
    aKey = license.Value()
    anMTKKey = mtk_license.Value()

    if not cadex.LicenseManager.Activate(aKey):
        print("Failed to activate CAD Exchanger license.")
        return 1
    if not cadex.LicenseManager.Activate(anMTKKey):
        print("Failed to activate Manufacturing Toolkit license.")
        return 1

    anApp = app.MTKConverter_Application()
    aRes = anApp.Run (theSource, theProcess, theTarget)
    return aRes.value

if __name__ == "__main__":
    if (len(sys.argv) == 1
        or sys.argv[1] == "-?" or sys.argv[1] == "/?"
        or sys.argv[1] == "-h" or sys.argv[1] == "--help"):
        PrintUsage()
        sys.exit()

    if len(sys.argv) < 6 :
        print("Invalid number of arguments. Please use \"-h\" or \"--help\" for usage information.")
        sys.exit(app.MTKConverter_ReturnCode.InvalidArgumentsNumber.value)

    aSource  = os.path.abspath(sys.argv[2])
    aProcess = sys.argv[4]
    aTarget  = os.path.abspath(sys.argv[6])

    sys.exit(main(aSource, aProcess, aTarget))
