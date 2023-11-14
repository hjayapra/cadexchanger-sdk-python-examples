# $Id$
#
# Copyright (C) 2008-2014, Roman Lygin. All rights reserved.
# Copyright (C) 2014-2022, CADEX. All rights reserved.
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

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK as mtk

import MTKConverter_PartProcessor as part_proc

class MTKConverter_MachiningData(part_proc.MTKConverter_ProcessData):
    def __init__(self, thePart: cadex.ModelData_Part):
        super().__init__(thePart)
        self.myFeatureList = mtk.MTKBase_FeatureList()
        self.myIssueList = mtk.MTKBase_FeatureList()
        self.myOperation = mtk.Machining_OT_Undefined

class MTKConverter_MachiningProcessor(part_proc.MTKConverter_VoidPartProcessor):
    def __init__(self, theOperation):
        super().__init__()
        self.myOperation = theOperation

    def ProcessSolid (self, thePart: cadex.ModelData_Part, theSolid: cadex.ModelData_Solid):
        aMachiningData = MTKConverter_MachiningData(thePart)
        self.myData.append(aMachiningData)
        aMachiningData.myOperation = self.myOperation

        aParams = mtk.Machining_FeatureRecognizerParameters()
        aParams.SetOperation(self.myOperation)
        aFeatureRecognizer = mtk.Machining_FeatureRecognizer(aParams)
        anAnalyzer = mtk.Machining_Analyzer()
        anAnalyzer.AddTool (aFeatureRecognizer)
        aData = anAnalyzer.Perform(theSolid)
        if aData.IsEmpty():
            return

        # Features
        for i in aData.FeatureList():
            aMachiningData.myFeatureList.Append(i)

        # Issues
        aDrillingParameters = mtk.DFMMachining_DrillingAnalyzerParameters()
        aDrillingAnalyzer = mtk.DFMMachining_Analyzer(aDrillingParameters)
        aMachiningData.myIssueList = aDrillingAnalyzer.Perform(theSolid, aData)

        aMillingParameters = mtk.DFMMachining_MillingAnalyzerParameters()
        aMillingAnalyzer = mtk.DFMMachining_Analyzer(aMillingParameters)
        aMillingIssueList = aMillingAnalyzer.Perform(theSolid, aData)
        for anIssue in aMillingIssueList:
            if self.myOperation == mtk.Machining_OT_LatheMilling and not mtk.DFMMachining_DeepPocketIssue.CompareType(anIssue):
                continue
            aMachiningData.myIssueList.Append(anIssue)

        if self.myOperation == mtk.Machining_OT_LatheMilling:
            aTurninigParameters = mtk.DFMMachining_TurningAnalyzerParameters()
            aTurningAnalyzer = mtk.DFMMachining_Analyzer(aTurninigParameters)
            aTurningIssueList = aTurningAnalyzer.Perform(theSolid, aData)
            for anIssue in aTurningIssueList:
                aMachiningData.myIssueList.Append(anIssue)
