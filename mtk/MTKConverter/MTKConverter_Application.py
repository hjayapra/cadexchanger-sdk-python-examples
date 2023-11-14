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

from enum import Enum

import cadexchanger.CadExCore as core
import cadexchanger.CadExView as view
import cadexchanger.CadExMTK as mtk

import MTKConverter_PartProcessor as part_proc

from MTKConverter_Report import MTKConverter_Report
from MTKConverter_MachiningProcessor import MTKConverter_MachiningProcessor
from MTKConverter_SheetMetalProcessor import MTKConverter_SheetMetalProcessor
from MTKConverter_WallThicknessProcessor import MTKConverter_WallThicknessProcessor

class MTKConverter_ProcessType(Enum):
    MTKConverter_PT_Undefined        = -1
    MTKConverter_PT_WallThickness    = 0
    MTKConverter_PT_MachiningMilling = 1
    MTKConverter_PT_MachiningTurning = 2
    MTKConverter_PT_SheetMetal       = 3

class MTKConverter_ReturnCode(Enum):
    # General codes
    MTKConverter_RC_OK                     = 0
    MTKConverter_RC_UnknownError           = 1
    MTKConverter_RC_GeneralException       = 2
    MTKConverter_RC_NoValidLicense         = 3
    MTKConverter_RC_InvalidArgumentsNumber = 4
    MTKConverter_RC_InvalidArgument        = 5

    # Import errors
    MTKConverter_RC_UnsupportedVersion     = 100
    MTKConverter_RC_UnexpectedFormat       = 101
    MTKConverter_RC_UnsupportedFileVariant = 102
    MTKConverter_RC_ImportError            = 103

    # Process errors
    MTKConverter_RC_ProcessError           = 200

    # Export errors
    MTKConverter_RC_ExportError            = 300

class MTKConverter_Application:
    def __init__(self):
        self.myCDXWEBWriterParameters = core.ModelData_WriterParameters()

        #setup CDXWEB params
        self.myCDXWEBWriterParameters.SetFileFormat(core.ModelData_WriterParameters.CDXWEB)
        self.myCDXWEBWriterParameters.SetWriteBRepRepresentation(True)
        self.myCDXWEBWriterParameters.SetWritePolyRepresentation(True)
        self.myCDXWEBWriterParameters.SetPreferredLOD(core.ModelData_RM_Any)
        self.myCDXWEBWriterParameters.SetWriteTextures(True)
        self.myCDXWEBWriterParameters.SetWritePMI(True)

    @staticmethod
    def __ProcessType(theProcessName: str):
        aProcessMap = {
            "wall_thickness":    MTKConverter_ProcessType.MTKConverter_PT_WallThickness,
            "machining_milling": MTKConverter_ProcessType.MTKConverter_PT_MachiningMilling,
            "machining_turning": MTKConverter_ProcessType.MTKConverter_PT_MachiningTurning,
            "sheet_metal":       MTKConverter_ProcessType.MTKConverter_PT_SheetMetal
        }

        if theProcessName in aProcessMap:
            return aProcessMap[theProcessName]
        else:
            return mtk.MTKConverter_PT_Undefined

    @staticmethod
    def __Import(theFilePath: str, theModel: core.ModelData_Model):
        print("Importing ", theFilePath, "...", sep="", end="")

        aReader = core.ModelData_ModelReader()
        if not aReader.Read(core.Base_UTF16String(theFilePath), theModel):
            print("\nERROR: Failed to import ", theFilePath, ". Exiting", sep="")
            return MTKConverter_ReturnCode.MTKConverter_RC_ImportError

        return MTKConverter_ReturnCode.MTKConverter_RC_OK

    @staticmethod
    def __CreateOriginModelThumbnail (theFilePath: str, theModel: core.ModelData_Model):
        # Setup offscreen viewport with transparent background and perspective camera
        aViewPort = view.ModelPrs_OffscreenViewPort()
        aViewPort.Resize(800, 600)
        aViewPort.SetCameraProjectionType(view.ModelPrs_CPT_Perspective)
        aViewPort.SetCameraPositionType(view.ModelPrs_CMT_Default)

        aBackgroundColor = core.ModelData_Color(0x00000000)
        aStyle = view.ModelPrs_BackgroundStyle(aBackgroundColor)
        aViewPort.SetBackgroundStyle(aStyle)

        # Create scene and display all entities
        aFactory = view.ModelPrs_SceneNodeFactory()
        aRootNode = aFactory.CreateGraph(theModel, core.ModelData_RM_Any)
        aRootNode.SetDisplayMode(view.ModelPrs_DM_ShadedWithBoundaries)

        aScene = view.ModelPrs_Scene()
        aScene.AddRoot(aRootNode)

        # Attach viewport to the scene
        if not aViewPort.AttachToScene(aScene):
            return False

        # Apply scene changes to viewport and wait until all async operations will be finished
        aScene.Update()
        aScene.Wait()

        # Fit and center model on the image
        aViewPort.FitAll()

        # Save image
        aRes = aViewPort.GrabToImage(theFilePath)

        return aRes

    @staticmethod
    def __ApplyProcessorToModel (theProcessor: part_proc.MTKConverter_PartProcessor,
                                 theModel: core.ModelData_Model,
                                 theReport: MTKConverter_Report):
        aVisitor = core.ModelData_SceneGraphElementUniqueVisitor(theProcessor)
        theModel.AcceptElementVisitor(aVisitor)
        for i in theProcessor.myData:
            theReport.AddData(i)

    @staticmethod
    def __Process (theProcess: str,
                   theModel: core.ModelData_Model,
                   theReport: MTKConverter_Report,
                   theProcessModel: core.ModelData_Model):
        print("Processing ", theProcess, "...", sep="", end="")

        theModel.AssignUuids()

        aProcessType = MTKConverter_Application.__ProcessType(theProcess)
        if aProcessType == MTKConverter_ProcessType.MTKConverter_PT_WallThickness:
            aProcessor = MTKConverter_WallThicknessProcessor(800)
            MTKConverter_Application.__ApplyProcessorToModel(aProcessor, theModel, theReport)
        elif aProcessType == MTKConverter_ProcessType.MTKConverter_PT_MachiningMilling:
            aProcessor = MTKConverter_MachiningProcessor(mtk.Machining_OT_Milling)
            MTKConverter_Application.__ApplyProcessorToModel(aProcessor, theModel, theReport)
        elif aProcessType == MTKConverter_ProcessType.MTKConverter_PT_MachiningTurning:
            aProcessor = MTKConverter_MachiningProcessor(mtk.Machining_OT_LatheMilling)
            MTKConverter_Application.__ApplyProcessorToModel(aProcessor, theModel, theReport)
        elif aProcessType == MTKConverter_ProcessType.MTKConverter_PT_SheetMetal:
            anUnfoldedName = str(theModel.Name()) + "_unfolded"
            theProcessModel.SetName(core.Base_UTF16String(anUnfoldedName))
            aProcessor = MTKConverter_SheetMetalProcessor(theProcessModel)
            MTKConverter_Application.__ApplyProcessorToModel(aProcessor, theModel, theReport)
        else:
            return MTKConverter_ReturnCode.MTKConverter_RC_InvalidArgument

        return MTKConverter_ReturnCode.MTKConverter_RC_OK

    @staticmethod
    def __Export(theFolderPath: core.Base_UTF16String,
                 theWriterParams: core.ModelData_WriterParameters,
                 theModel: core.ModelData_Model,
                 theReport: MTKConverter_Report,
                 theProcessModel: core.ModelData_Model):
        print("Exporting ", theFolderPath, "...", sep="", end="")
        aModelPath = theFolderPath + "/" + str(theModel.Name()) + ".cdxweb" + "/scenegraph.cdxweb"
        if not theModel.Save(core.Base_UTF16String(aModelPath), theWriterParams):
            print("\nERROR: Failed to export ", aModelPath, ". Exiting", sep="")
            return MTKConverter_ReturnCode.ExportError

        aThumbnailPath = theFolderPath + "/thumbnail.png"
        if not MTKConverter_Application.__CreateOriginModelThumbnail(core.Base_UTF16String(aThumbnailPath), theModel):
            print("\nERROR: Failed to create thumbnail ", aThumbnailPath, ". Exiting", sep="")
            return MTKConverter_ReturnCode.ExportError

        if not theProcessModel.IsEmpty():
            aProcessModelPath = theFolderPath + "/" + str(theProcessModel.Name()) + ".cdxweb" + "/scenegraph.cdxweb"
            if not theProcessModel.Save(core.Base_UTF16String(aProcessModelPath), theWriterParams):
                print("\nERROR: Failed to export ", aProcessModelPath, ". Exiting", sep="")
                return MTKConverter_ReturnCode.ExportError

        aJsonPath = theFolderPath + "/process_data.json"
        if not theReport.WriteToJSON (aJsonPath):
            print("\nERROR: Failed to create JSON file ", aJsonPath, ". Exiting", sep="")
            return MTKConverter_ReturnCode.ExportError

        return MTKConverter_ReturnCode.MTKConverter_RC_OK

    def Run(self, theSource: str, theProcess: str, theTarget: str):
        aModel = core.ModelData_Model()
        aProcessModel = core.ModelData_Model()
        aReport = MTKConverter_Report()

        core.Base_Settings.Default().SetValue(core.Base_Settings.UseExceptions, True)

        aRes = MTKConverter_ReturnCode.MTKConverter_RC_OK
        try:
            aRes = MTKConverter_Application.__Import (theSource, aModel)
            print("Done.")
            if aRes == MTKConverter_ReturnCode.MTKConverter_RC_OK:
                aRes = MTKConverter_Application.__Process (theProcess, aModel, aReport, aProcessModel)
                print("Done.")
            if aRes == MTKConverter_ReturnCode.MTKConverter_RC_OK:
                aRes = MTKConverter_Application.__Export (theTarget, self.myCDXWEBWriterParameters, aModel, aReport, aProcessModel)
                print("Done.")
        except core.BaseError_UnsupportedVersion as anE:
            print("Failed.\nERROR: ", anE.What(), sep="")
            return MTKConverter_ReturnCode.MTKConverter_RC_UnsupportedVersion
        except core.BaseError_UnexpectedFormat as anE:
            print("Failed.\nERROR: ", anE.What(), sep="")
            return MTKConverter_ReturnCode.MTKConverter_RC_UnexpectedFormat
        except core.BaseError_UnsupportedFileVariant as anE:
            print("Failed.\nERROR: ", anE.What(), sep="")
            return MTKConverter_ReturnCode.MTKConverter_RC_UnsupportedFileVariant
        except core.Base_Exception as anE:
            print("Failed.\nERROR: ", anE.What(), sep="")
            return MTKConverter_ReturnCode.MTKConverter_RC_GeneralException
        except:
            print("Failed.\nERROR: Unhandled exception caught.")
            return MTKConverter_ReturnCode.MTKConverter_RC_GeneralException

        return aRes
