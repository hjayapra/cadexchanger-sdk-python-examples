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

import io
import math

import cadexchanger.CadExCore as cadex
import cadexchanger.CadExMTK as mtk

import MTKConverter_PartProcessor as part_proc
import MTKConverter_MachiningProcessor as mach_proc
import MTKConverter_SheetMetalProcessor as sm_proc
import MTKConverter_WallThicknessProcessor as wt_proc

class Pair:
    def __init__(self, theFirst: float, theSecond: float):
        self.First = theFirst
        self.Second = theSecond

    def __repr__(self):
        return f"Pair({self.First}, {self.Second})"

    def __str__(self):
        return f"{self.First:.2f} x {self.Second:.2f}"

class Dimension:
    def __init__(self, theX: float, theY: float, theZ: float):
        self.X = theX
        self.Y = theY
        self.Z = theZ

    def __repr__(self):
        return f"Dimension({self.X}, {self.Y}, {self.Z})"

    def __str__(self):
        return f"{self.X:.2f} x {self.Y:.2f} x {self.Z:.2f}"

class Direction:
    def __init__(self, theX: float, theY: float, theZ: float):
        self.X = theX
        self.Y = theY
        self.Z = theZ

    def __repr__(self):
        return f"Direction({self.X}, {self.Y}, {self.Z})"

    def __str__(self):
        return f"({self.X:.2f}, {self.Y:.2f}, {self.Z:.2f})"

class Point:
    def __init__(self, theX: float, theY: float, theZ: float):
        self.X = theX
        self.Y = theY
        self.Z = theZ

    def __repr__(self):
        return f"Point({self.X}, {self.Y}, {self.Z})"

    def __str__(self):
        return f"({self.X:.2f}, {self.Y:.2f}, {self.Z:.2f})"

class JSONWriter:
    def __init__(self, theFile: io.TextIOBase, theStartNestingLevel = 0):
        self.__myStream = theFile
        self.__myNestingLevel = theStartNestingLevel
        self.__myPrevNestingLevel = theStartNestingLevel - 1
        self.__myIsInit = False

    def OpenSection(self, theName = ""):
        self.__DoOpenSection (theName, '{')

    def OpenArraySection (self, theName: str):
        self.__DoOpenSection(theName, '[')

    def CloseSection(self):
        self.__DoCloseSection('}')

    def CloseArraySection(self):
        self.__DoCloseSection(']')

    def WriteData(self, theParamName: str, theValue):
        aValueStr = str(theValue)
        if type(theValue) is float:
            aValueStr = f"{theValue:.2f}"
        self.__Stream().write("\"" + theParamName + "\": \"" + aValueStr + "\"")

    def WriteRawData(self, theRawData: str):
        self.__PrepareStream()
        self.__myStream.write(theRawData)

    def WriteEmptyArray (self, theParamName: str):
        self.__Stream().write("\"" + theParamName + "\": []")

    def NestingLevel(self):
        return self.__myNestingLevel

    def __DoOpenSection(self, theName: str, theOpenBracketSymbol: str):
        aStream = self.__Stream()
        if theName:
            aStream.write("\"" + theName + "\": ")
        aStream.write(theOpenBracketSymbol)
        self.__myNestingLevel += 1

    def __DoCloseSection (self, theCloseBracketSymbol: str):
        self.__myNestingLevel -= 1
        self.__Stream().write(theCloseBracketSymbol)

    def __PrepareStream(self):
        if self.__myNestingLevel == self.__myPrevNestingLevel:
            self.__myStream.write(",")
        self.__myPrevNestingLevel = self.__myNestingLevel
        if self.__myIsInit:
            self.__myStream.write('\n')
        self.__myIsInit = True

    def __Stream(self):
        self.__PrepareStream()
        for i in range(self.__myNestingLevel):
            self.__myStream.write("    ")
        return self.__myStream

class FeatureGroupManager:
    def __init__(self):
        self.__myGroups = []

    def AddGroupData (self,
                      theGroupName: str,
                      theGroupColor: str,
                      theFeatureData: str,
                      theFeatureNb: int):
        # Find or create
        aRes = -1
        for i in range(len(self.__myGroups)):
            aGroup = self.__myGroups[i]
            if aGroup.myName == theGroupName:
                aRes = i
                break

        if aRes == -1:
            self.__myGroups.append(self.FeatureGroup(theGroupName, theGroupColor))
            aRes = len(self.__myGroups) - 1

        # Update
        aGroup = self.__myGroups[aRes]
        aGroup.myFeatureData.append(theFeatureData)
        aGroup.myFeatureCount += theFeatureNb

    def TotalFeatureCount(self):
        aTotalFeatureCount = 0
        for aGroup in self.__myGroups:
            aTotalFeatureCount += aGroup.myFeatureCount
        return aTotalFeatureCount

    def Write(self, theWriter: JSONWriter):
        for aGroup in self.__myGroups:
            theWriter.OpenSection()
            theWriter.WriteData("name", aGroup.myName)
            theWriter.WriteData("color", aGroup.myColor)
            theWriter.WriteData("totalGroupFeatureCount", aGroup.myFeatureCount)

            aFeatureData = aGroup.myFeatureData
            if aFeatureData:
                aHasParams = "parameters" in aFeatureData[0]
                if aHasParams:
                    theWriter.WriteData ("subGroupCount", len(aFeatureData))
                    theWriter.OpenArraySection ("subGroups")
                    for j in aFeatureData:
                        theWriter.WriteRawData(j)
                    theWriter.CloseArraySection()
                else:
                    for j in aFeatureData:
                        theWriter.WriteRawData(j)

            theWriter.CloseSection()

    class FeatureGroup:
        def __init__(self, theName: str, theColor: str):
            self.myName = theName
            self.myColor = theColor
            self.myFeatureData = []
            self.myFeatureCount = 0

class OrderedFeatureList:
    def __init__(self):
        self.__myList = []

    def Append(self, theFeature: mtk.MTKBase_Feature, theShapeIDs):
        anInsertIndex = 0
        for i in self.__myList:
            aRes = OrderedFeatureList.__CompareFeatures(theFeature, i.Feature)
            if aRes == 0:
                i.Count += 1
                i.ShapeIDs.append(theShapeIDs)
                anInsertIndex = -1
                break
            elif aRes < 0:
                break

            anInsertIndex += 1

        if anInsertIndex >= 0:
            self.__myList.insert(anInsertIndex, self.FeatureData(theFeature, theShapeIDs))

    def Size(self):
        return len(self.__myList)

    def GetFeature(self, theIndex: int):
        return self.__GetFeatureData(theIndex).Feature

    def GetFeatureCount(self, theIndex: int):
        return self.__GetFeatureData(theIndex).Count

    def GetFeatureShapeIDs(self, theIndex: int):
        return self.__GetFeatureData(theIndex).ShapeIDs

    def __GetFeatureData(self, theIndex: int):
        return self.__myList[theIndex]

    @staticmethod
    def __CompareFeatures(theA: mtk.MTKBase_Feature, theB: mtk.MTKBase_Feature):
        aComparator = mtk.MTKBase_FeatureComparator()
        anALessThanB = aComparator(theA, theB)
        if anALessThanB:
            return -1

        aBLessThanA = aComparator(theB, theA)
        if aBLessThanA:
            return 1

        return 0

    class FeatureData:
        def __init__(self, theFeature: mtk.MTKBase_Feature, theShapeIDs):
            self.Feature = theFeature
            self.Count = 1
            self.ShapeIDs = []
            self.ShapeIDs.append(theShapeIDs)

class MTKConverter_Report:
    def __init__(self):
        self.__myData = []

    def AddData(self, theData: part_proc.MTKConverter_ProcessData):
        self.__myData.append(theData)

    def WriteToJSON(self, thePath: str):
        aFile = open(thePath, "w")
        if not aFile:
            return False

        aWriter = JSONWriter(aFile)
        aWriter.OpenSection()
        aWriter.WriteData("version", "1")

        if not self.__myData:
            aWriter.WriteData("error", "The model doesn't contain any parts.")
        else:
            aWriter.OpenArraySection("parts")
            for aProcessData in self.__myData:
                aWriter.OpenSection()
                MTKConverter_Report.__WritePartProcessData(aWriter, aProcessData)
                aWriter.CloseSection()
            aWriter.CloseArraySection()
        aWriter.CloseSection()

        aFile.close()
        return True

    @staticmethod
    def __WriteParameter(theWriter: JSONWriter, theParamName: str, theParamUnits: str, theParamValue):
        theWriter.OpenSection()
        theWriter.WriteData("name", theParamName)
        theWriter.WriteData("units", theParamUnits)
        theWriter.WriteData("value", theParamValue)
        theWriter.CloseSection()

    @staticmethod
    def __WriteShapeIDs(theWriter: JSONWriter, theVector):
        if not theVector:
            return

        theWriter.WriteData("featureCount", len(theVector))
        theWriter.OpenArraySection("features")

        for aShapeIDVector in theVector:
            theWriter.OpenSection()
            theWriter.WriteData("shapeIDCount", len(aShapeIDVector))
            if not aShapeIDVector:
                theWriter.WriteEmptyArray("shapeIDs")
            else:
                theWriter.OpenArraySection("shapeIDs")
                for aShapeID in aShapeIDVector:
                    theWriter.OpenSection()
                    theWriter.WriteData("id", aShapeID)
                    theWriter.CloseSection()
                theWriter.CloseArraySection()
            theWriter.CloseSection()

        theWriter.CloseArraySection()

    @staticmethod
    def __DoWriteFeatureDataToString (theFunc, theParamCount: int, theVector):
        aStream = io.StringIO()
        aWriter = JSONWriter(aStream, 7)

        aWriter.OpenSection()
        aWriter.WriteData("parametersCount", theParamCount)
        aWriter.OpenArraySection("parameters")
        theFunc(aWriter)
        aWriter.CloseArraySection()
        MTKConverter_Report.__WriteShapeIDs(aWriter, theVector)
        aWriter.CloseSection()

        aRes = aStream.getvalue()
        aStream.close()
        return aRes

    @staticmethod
    def __WriteFeatureDataToString0(theVector):
        aStream = io.StringIO()
        aWriter = JSONWriter(aStream, 6)

        MTKConverter_Report.__WriteShapeIDs(aWriter, theVector)

        aRes = aStream.getvalue()
        aStream.close()
        return aRes

    @staticmethod
    def __WriteFeatureDataToString1(theParamName: str, theParamUnits: str, theParamValue, theVector):
        def WriteParams (theWriter: JSONWriter):
            MTKConverter_Report.__WriteParameter(theWriter, theParamName, theParamUnits, theParamValue)
        return MTKConverter_Report.__DoWriteFeatureDataToString(WriteParams, 1, theVector)

    @staticmethod
    def __WriteFeatureDataToString2(theParamName1: str, theParamUnits1: str, theParamValue1,
                                    theParamName2: str, theParamUnits2: str, theParamValue2,
                                    theVector):
        def WriteParams (theWriter: JSONWriter):
            MTKConverter_Report.__WriteParameter(theWriter, theParamName1, theParamUnits1, theParamValue1)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName2, theParamUnits2, theParamValue2)
        return MTKConverter_Report.__DoWriteFeatureDataToString (WriteParams, 2, theVector)

    @staticmethod
    def __WriteFeatureDataToString3(theParamName1: str, theParamUnits1: str, theParamValue1,
                                    theParamName2: str, theParamUnits2: str, theParamValue2,
                                    theParamName3: str, theParamUnits3: str, theParamValue3,
                                    theVector):
        def WriteParams (theWriter: JSONWriter):
            MTKConverter_Report.__WriteParameter(theWriter, theParamName1, theParamUnits1, theParamValue1)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName2, theParamUnits2, theParamValue2)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName3, theParamUnits3, theParamValue3)
        return MTKConverter_Report.__DoWriteFeatureDataToString (WriteParams, 3, theVector)

    @staticmethod
    def __WriteFeatureDataToString4(theParamName1: str, theParamUnits1: str, theParamValue1,
                                    theParamName2: str, theParamUnits2: str, theParamValue2,
                                    theParamName3: str, theParamUnits3: str, theParamValue3,
                                    theParamName4: str, theParamUnits4: str, theParamValue4,
                                    theVector):
        def WriteParams (theWriter: JSONWriter):
            MTKConverter_Report.__WriteParameter(theWriter, theParamName1, theParamUnits1, theParamValue1)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName2, theParamUnits2, theParamValue2)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName3, theParamUnits3, theParamValue3)
            MTKConverter_Report.__WriteParameter(theWriter, theParamName4, theParamUnits4, theParamValue4)
        return MTKConverter_Report.__DoWriteFeatureDataToString (WriteParams, 4, theVector)

    @staticmethod
    def __MachiningFaceTypeToString(theType):
        aFaceTypeMap = {
            mtk.Machining_FT_FlatFaceMilled:           "Flat Face Milled Face(s)",
            mtk.Machining_FT_FlatSideMilled:           "Flat Side Milled Face(s)",
            mtk.Machining_FT_CurvedMilled:             "Curved Milled Face(s)",
            mtk.Machining_FT_CircularMilled:           "Circular Milled Face(s)",
            mtk.Machining_FT_Deburr:                   "Deburr Face(s)",
            mtk.Machining_FT_ConvexProfileEdgeMilling: "Convex Profile Edge Milling Face(s)",
            mtk.Machining_FT_ConcaveFilletEdgeMilling: "Concave Fillet Edge Milling Face(s)",
            mtk.Machining_FT_FlatMilled:               "Flat Milled Face(s)",
            mtk.Machining_FT_TurnDiameter:             "Turn Diameter Face(s)",
            mtk.Machining_FT_TurnForm:                 "Turn Form Face(s)",
            mtk.Machining_FT_TurnFace:                 "Turn Face Face(s)",
            mtk.Machining_FT_Bore:                     "Bore Face(s)"
        }

        if theType in aFaceTypeMap:
            return aFaceTypeMap[theType]
        else:
            return "Face(s)"

    @staticmethod
    def __MachiningFaceColor(theType):
        aFaceTypeMap = {
            mtk.Machining_FT_FlatFaceMilled:           "(115, 251, 253)",
            mtk.Machining_FT_FlatSideMilled:           "(0, 35, 245)",
            mtk.Machining_FT_CurvedMilled:             "(22, 65, 124)",
            mtk.Machining_FT_CircularMilled:           "(255, 254, 145)",
            mtk.Machining_FT_Deburr:                   "(0, 0, 0)",
            mtk.Machining_FT_ConvexProfileEdgeMilling: "(240, 155, 89)",
            mtk.Machining_FT_ConcaveFilletEdgeMilling: "(129, 127, 38)",
            mtk.Machining_FT_FlatMilled:               "(115, 43, 245)",
            mtk.Machining_FT_TurnDiameter:             "(88, 19, 94)",
            mtk.Machining_FT_TurnForm:                 "(161, 251, 142)",
            mtk.Machining_FT_TurnFace:                 "(239, 136, 190)",
            mtk.Machining_FT_Bore:                     "(127, 130, 187)"
        }

        if theType in aFaceTypeMap:
            return aFaceTypeMap[theType]
        else:
            return "(0, 0, 0)"

    @staticmethod
    def __MachiningHoleTypeToString(theType):
        aHoleTypeMap = {
            mtk.Machining_HT_Through:    "Through Hole(s)",
            mtk.Machining_HT_FlatBottom: "Flat Bottom Hole(s)",
            mtk.Machining_HT_Blind:      "Blind Hole(s)",
            mtk.Machining_HT_Partial:    "Partial Hole(s)"
        }

        if theType in aHoleTypeMap:
            return aHoleTypeMap[theType]
        else:
            return "Hole(s)"

    @staticmethod
    def __MachiningHoleColor(theType):
        aHoleTypeMap = {
            mtk.Machining_HT_Through:    "(240, 135, 132)",
            mtk.Machining_HT_FlatBottom: "(235, 51, 36)",
            mtk.Machining_HT_Blind:      "(142, 64, 58)",
            mtk.Machining_HT_Partial:    "(58, 6, 3)"
        }

        if theType in aHoleTypeMap:
            return aHoleTypeMap[theType]
        else:
            return "(0, 0, 0)"

    @staticmethod
    def __HemTypeToString(theType):
        aHemTypeMap = {
            mtk.SheetMetal_HBT_Flattened: "Flattened Hem Bend(s)",
            mtk.SheetMetal_HBT_Open:      "Open Hem Bend(s)",
            mtk.SheetMetal_HBT_Teardrop:  "Teardrop Hem Bend(s)",
            mtk.SheetMetal_HBT_Rope:      "Rope Hem Bend(s)",
            mtk.SheetMetal_HBT_Rolled:    "Rolled Hem Bend(s)"
        }

        if theType in aHemTypeMap:
            return aHemTypeMap[theType]
        else:
            return "Hem Bend(s)"

    @staticmethod
    def __BendName(theBend: mtk.SheetMetal_Bend):
        if mtk.SheetMetal_HemBend.CompareType(theBend):
            aHemBend = mtk.SheetMetal_HemBend.Cast(theBend)
            return MTKConverter_Report.__HemTypeToString(aHemBend.Type())
        elif mtk.SheetMetal_CurvedBend.CompareType(theBend):
            return "Curved Bend(s)"
        return "Bend(s)"

    @staticmethod
    def __BendColor(theBend: mtk.SheetMetal_Bend):
        if mtk.SheetMetal_HemBend.CompareType(theBend):
            aHemBend = mtk.SheetMetal_HemBend.Cast(theBend)
            aType = aHemBend.Type()

            aHemTypeMap = {
                mtk.SheetMetal_HBT_Flattened: "(22, 65, 124)",
                mtk.SheetMetal_HBT_Open:      "(42, 85, 144)",
                mtk.SheetMetal_HBT_Teardrop:  "(62, 105, 164)",
                mtk.SheetMetal_HBT_Rope:      "(82, 125, 184)",
                mtk.SheetMetal_HBT_Rolled:    "(102, 145, 204)"
            }

            if aType in aHemTypeMap:
                return aHemTypeMap[aType]
            else:
                return "(0, 0, 0)"
        elif mtk.SheetMetal_CurvedBend.CompareType(theBend):
            return "(255, 254, 145)"
        return "(0, 35, 245)"

    @staticmethod
    def __SheetMetalHoleName(theHole: mtk.SheetMetal_Hole):
        if mtk.SheetMetal_ComplexHole.CompareType(theHole):
            return "Complex Hole(s)"
        return "Hole(s)"

    @staticmethod
    def __SheetMetalHoleColor(theHole: mtk.SheetMetal_Hole):
        if mtk.SheetMetal_ComplexHole.CompareType(theHole):
            return "(115, 43, 245)"
        return "(129, 127, 38)"

    @staticmethod
    def __SmallDistanceIssueName(theIssue: mtk.DFMSheetMetal_SmallDistanceBetweenFeaturesIssue):
        if mtk.DFMSheetMetal_SmallDistanceBetweenBendAndLouverIssue.CompareType(theIssue):
            return "Small Distance Between Bend And Louver Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndBendIssue.CompareType(theIssue):
            return "Small Distance Between Extruded Hole And Bend Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndEdgeIssue.CompareType(theIssue):
            return "Small Distance Between Extruded Hole And Edge Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHolesIssue.CompareType(theIssue):
            return "Small Distance Between Extruded Holes Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndBendIssue.CompareType(theIssue):
            return "Small Distance Between Hole And Bend Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndCutoutIssue.CompareType(theIssue):
            return "Small Distance Between Hole And Cutout Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndEdgeIssue.CompareType(theIssue):
            return "Small Distance Between Hole And Edge Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndLouverIssue.CompareType(theIssue):
            return "Small Distance Between Hole And Louver Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndNotchIssue.CompareType(theIssue):
            return "Small Distance Between Hole And Notch Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHolesIssue.CompareType(theIssue):
            return "Small Distance Between Holes Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchAndBendIssue.CompareType(theIssue):
            return "Small Distance Between Notch And Bend Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchesIssue.CompareType(theIssue):
            return "Small Distance Between Notches Issue(s)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenTabsIssue.CompareType(theIssue):
            return "Small Distance Between Tabs Issue(s)"
        return "Small Distance Between Feature(s)"

    @staticmethod
    def __SmallDistanceIssueColor(theIssue: mtk.DFMSheetMetal_SmallDistanceBetweenFeaturesIssue):
        if mtk.DFMSheetMetal_SmallDistanceBetweenBendAndLouverIssue.CompareType(theIssue):
            return "(195, 56, 19)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndBendIssue.CompareType(theIssue):
            return "(212, 75, 90)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndEdgeIssue.CompareType(theIssue):
            return "(198, 75, 105)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHolesIssue.CompareType(theIssue):
            return "(170, 65, 120)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndBendIssue.CompareType(theIssue):
            return "(239, 136, 190)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndCutoutIssue.CompareType(theIssue):
            return "(127, 130, 187)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndEdgeIssue.CompareType(theIssue):
            return "(240, 135, 132)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndLouverIssue.CompareType(theIssue):
            return "(15, 5, 129)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndNotchIssue.CompareType(theIssue):
            return "(235, 51, 36)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenHolesIssue.CompareType(theIssue):
            return "(142, 64, 58)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchAndBendIssue.CompareType(theIssue):
            return "(58, 6, 3)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchesIssue.CompareType(theIssue):
            return "(0, 215, 3)"
        elif mtk.DFMSheetMetal_SmallDistanceBetweenTabsIssue.CompareType(theIssue):
            return "(157, 160, 207)"
        return "(0, 0, 0)"

    @staticmethod
    def __AddShapeFeature(theManager: FeatureGroupManager, theFeature: mtk.MTKBase_ShapeFeature, theCount: int, theShapeIdVector):
        aFeature = theFeature
        #machining
        if mtk.Machining_TurningFace.CompareType(aFeature):
            aTurningFace = mtk.Machining_TurningFace.Cast(aFeature)
            aType = aTurningFace.Type()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString1("Radius", "mm", aTurningFace.Radius(), theShapeIdVector)
            theManager.AddGroupData(MTKConverter_Report.__MachiningFaceTypeToString(aType),
                                    MTKConverter_Report.__MachiningFaceColor(aType),
                                    aFeatureData, theCount)
        elif mtk.Machining_Face.CompareType(aFeature):
            aFace = mtk.Machining_Face.Cast(aFeature)
            aType = aFace.Type()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData(MTKConverter_Report.__MachiningFaceTypeToString(aType),
                                    MTKConverter_Report.__MachiningFaceColor(aType),
                                    aFeatureData, theCount)
        elif mtk.Machining_Countersink.CompareType(aFeature):
            aCountersink = mtk.Machining_Countersink.Cast(aFeature)
            anAxis = aCountersink.Axis().Axis()
            aDirection = Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Radius", "mm", aCountersink.Radius(),
                "Depth",  "mm", aCountersink.Depth(),
                "Axis",    "",  aDirection,
                theShapeIdVector)
            theManager.AddGroupData("Countersink(s)", "(55, 125, 34)", aFeatureData, theCount)
        elif mtk.Machining_Hole.CompareType(aFeature):
            aHole = mtk.Machining_Hole.Cast(aFeature)
            anAxis = aHole.Axis().Axis()
            aDirection = Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
            aType = aHole.Type()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Radius", "mm", aHole.Radius(),
                "Depth",  "mm", aHole.Depth(),
                "Axis",    "",  aDirection,
                theShapeIdVector)
            theManager.AddGroupData(MTKConverter_Report.__MachiningHoleTypeToString(aType),
                                    MTKConverter_Report.__MachiningHoleColor(aType),
                                    aFeatureData, theCount)
        elif mtk.Machining_Pocket.CompareType(aFeature):
            aPocket = mtk.Machining_Pocket.Cast(aFeature)
            anAxis = aPocket.Axis().Direction()
            aDirection = Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString4(
                "Length", "mm", aPocket.Length(),
                "Width",  "mm", aPocket.Width(),
                "Depth",  "mm", aPocket.Depth(),
                "Axis",    "",  aDirection,
                theShapeIdVector)
            theManager.AddGroupData ("Pocket(s)", "(23, 63, 63)", aFeatureData, theCount)
        elif mtk.MTKBase_Boss.CompareType(aFeature):
            aBoss = mtk.MTKBase_Boss.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString4(
                "Length", "mm", aBoss.Length(),
                "Width",  "mm", aBoss.Width(),
                "Height", "mm", aBoss.Height(),
                theShapeIdVector)
            theManager.AddGroupData ("Boss(es)", "(56, 72, 13)", aFeatureData, theCount)

        #sheet metal
        elif mtk.SheetMetal_Bead.CompareType(aFeature):
            aBead = mtk.SheetMetal_Bead.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString1("Depth", "mm", aBead.Depth(), theShapeIdVector)
            theManager.AddGroupData("Bead(s)", "(115, 251, 253)", aFeatureData, theCount)
        elif mtk.SheetMetal_Bend.CompareType(aFeature):
            aBend = mtk.SheetMetal_Bend.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString4(
                "Radius", "mm",  aBend.Radius(),
                "Angle",  "deg", aBend.Angle() * 180 / math.pi,
                "Length", "mm",  aBend.Length(),
                "Width",  "mm",  aBend.Width(),
                theShapeIdVector)
            theManager.AddGroupData(MTKConverter_Report.__BendName(aBend), MTKConverter_Report.__BendColor(aBend),
                                    aFeatureData, theCount)
        elif mtk.SheetMetal_Bridge.CompareType(aFeature):
            aBridge = mtk.SheetMetal_Bridge.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Length", "mm", aBridge.Length(),
                "Depth",  "mm", aBridge.Depth(),
                theShapeIdVector)
            theManager.AddGroupData("Bridge(s)", "(240, 155, 89)", aFeatureData, theCount)
        elif mtk.SheetMetal_Hole.CompareType(aFeature):
            aHole = mtk.SheetMetal_Hole.Cast(aFeature)
            anAxis = aHole.Axis().Axis()
            aDirection = Direction(anAxis.X(), anAxis.Y(), anAxis.Z())
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Radius", "mm", aHole.Radius(),
                "Depth",  "mm", aHole.Depth(),
                "Axis",    "",  aDirection,
                theShapeIdVector)
            theManager.AddGroupData (MTKConverter_Report.__SheetMetalHoleName(aHole),
                                     MTKConverter_Report.__SheetMetalHoleColor(aHole),
                                     aFeatureData, theCount)
        elif mtk.SheetMetal_Cutout.CompareType(aFeature):
            aCutout = mtk.SheetMetal_Cutout.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString1("Perimeter", "mm", aCutout.Perimeter(), theShapeIdVector)
            theManager.AddGroupData ("Cutout(s)", "(88, 19, 94)", aFeatureData, theCount)
        elif mtk.SheetMetal_Louver.CompareType(aFeature):
            aLouver = mtk.SheetMetal_Louver.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString1(
                "Depth",  "mm", aLouver.Depth(),
                theShapeIdVector)
            theManager.AddGroupData("Louver(s)", "(161, 251, 142)", aFeatureData, theCount)
        elif mtk.SheetMetal_Notch.CompareType(aFeature):
            aNotch = mtk.SheetMetal_Notch.Cast(aFeature)
            if mtk.SheetMetal_StraightNotch.CompareType(aNotch):
                aStraightNotch = mtk.SheetMetal_StraightNotch.Cast(aNotch)
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                    "Length", "mm", aNotch.Length(),
                    "Width",  "mm", aNotch.Width(),
                    "Corner Fillet Radius", "mm", aStraightNotch.CornerFilletRadius(),
                    theShapeIdVector)
                theManager.AddGroupData ("Straight Notch(es)", "(240, 135, 132)", aFeatureData, theCount)
            elif mtk.SheetMetal_VNotch.CompareType(aNotch):
                aVNotch = mtk.SheetMetal_VNotch.Cast(aNotch)
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                    "Length", "mm", aNotch.Length(),
                    "Width",  "mm", aNotch.Width(),
                    "Angle", "deg", aVNotch.Angle() * 180 / math.pi,
                    theShapeIdVector)
                theManager.AddGroupData ("V Notch(es)", "(235, 51, 36)", aFeatureData, theCount)
            else:
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                    "Length", "mm", aNotch.Length(),
                    "Width",  "mm", aNotch.Width(),
                    theShapeIdVector)
                theManager.AddGroupData("Notch(es)", "(239, 136, 190)", aFeatureData, theCount)
        elif mtk.SheetMetal_Tab.CompareType(aFeature):
            aTab = mtk.SheetMetal_Tab.Cast(aFeature)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Length", "mm", aTab.Length(),
                "Width",  "mm", aTab.Width(),
                theShapeIdVector)
            theManager.AddGroupData("Tab(s)", "(127, 130, 187)", aFeatureData, theCount)

    @staticmethod
    def __AddDrillingIssue(theManager: FeatureGroupManager, theIssue: mtk.DFMMachining_DrillingIssue, theCount: int, theShapeIdVector):
        if mtk.DFMMachining_SmallDiameterHoleIssue.CompareType(theIssue):
            aSmallHoleIssue = mtk.DFMMachining_SmallDiameterHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Diameter", "mm", aSmallHoleIssue.ExpectedMinDiameter(),
                "Actual Diameter", "mm", aSmallHoleIssue.ActualDiameter(),
                theShapeIdVector)
            theManager.AddGroupData("Small Diameter Hole(s)", "(115, 251, 253)", aFeatureData, theCount);
        elif mtk.DFMMachining_DeepHoleIssue.CompareType(theIssue):
            aDeepHoleIssue = mtk.DFMMachining_DeepHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Depth", "mm", aDeepHoleIssue.ExpectedMaxDepth(),
                "Actual Depth", "mm", aDeepHoleIssue.ActualDepth(), theShapeIdVector)
            theManager.AddGroupData("Deep Hole(s)", "(0, 35, 245)", aFeatureData, theCount)
        elif mtk.DFMMachining_NonStandardDiameterHoleIssue.CompareType(theIssue):
            aNSDiameterHoleIssue = mtk.DFMMachining_NonStandardDiameterHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Nearest Standard Diameter", "mm", aNSDiameterHoleIssue.NearestStandardDiameter(),
                "Actual Diameter", "mm", aNSDiameterHoleIssue.ActualDiameter(),
                theShapeIdVector)
            theManager.AddGroupData("Non Standard Diameter Hole(s)", "(22, 65, 124)", aFeatureData, theCount)
        elif mtk.DFMMachining_NonStandardDrillPointAngleBlindHoleIssue.CompareType(theIssue):
            aNSDrillPointAngleBlindHoleIssue = mtk.DFMMachining_NonStandardDrillPointAngleBlindHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Nearest Standard Angle", "deg", aNSDrillPointAngleBlindHoleIssue.NearestStandardAngle() * 180 / math.pi,
                "Actual Angle", "deg", aNSDrillPointAngleBlindHoleIssue.ActualAngle() * 180 / math.pi,
                theShapeIdVector)
            theManager.AddGroupData("Non Standard Drill Point Angle Blind Hole(s)", "(88, 13, 78)", aFeatureData, theCount)
        elif mtk.DFMMachining_PartialHoleIssue.CompareType(theIssue):
            aPartialHoleIssue = mtk.DFMMachining_PartialHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Material Percent", "%", aPartialHoleIssue.ExpectedMinMaterialPercent() * 100,
                "Actual Material Percent", "%", aPartialHoleIssue.ActualMaterialPercent() * 100,
                theShapeIdVector)
            theManager.AddGroupData("Partial Hole(s)", "(255, 254, 145)", aFeatureData, theCount)
        elif mtk.DFMMachining_FlatBottomHoleIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Flat Bottom Hole(s)", "(240, 155, 89)", aFeatureData, theCount)
        elif mtk.DFMMachining_NonPerpendicularHoleIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Non Perpendicular Hole(s)", "(129, 127, 38)", aFeatureData, theCount)
        elif mtk.DFMMachining_IntersectingCavityHoleIssue.Cast(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Intersecting Cavity Hole(s)", "(115, 43, 245)", aFeatureData, theCount)

    @staticmethod
    def __AddMillingIssue(theManager: FeatureGroupManager, theIssue: mtk.DFMMachining_MillingIssue, theCount: int, theShapeIdVector):
        if mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.CompareType(theIssue):
            aFloorRadiusIssue = mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Nearest Standard Radius", "mm", aFloorRadiusIssue.NearestStandardRadius(),
                "Actual Radius", "mm", aFloorRadiusIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Non Standard Radius Milled Part Floor Fillet Issue(s)", "(0, 215, 3)", aFeatureData, theCount)
        elif mtk.DFMMachining_DeepPocketIssue.CompareType(theIssue):
            aDeepPocketIssue = mtk.DFMMachining_DeepPocketIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Depth", "mm", aDeepPocketIssue.ExpectedMaxDepth(),
                "Actual Depth", "mm", aDeepPocketIssue.ActualDepth(),
                theShapeIdVector)
            theManager.AddGroupData("Deep Pocket Issue(s)", "(190, 10, 100)", aFeatureData, theCount)
        elif mtk.DFMMachining_HighBossIssue.CompareType(theIssue):
            aHighBossIssue = mtk.DFMMachining_HighBossIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Height", "mm", aHighBossIssue.ExpectedMaxHeight(),
                "Actual Height", "mm", aHighBossIssue.ActualHeight(),
                theShapeIdVector)
            theManager.AddGroupData("High Boss Issue(s)", "(180, 100, 50)", aFeatureData, theCount)
        elif mtk.DFMMachining_LargeMilledPartIssue.CompareType(theIssue):
            aLMPIssue = mtk.DFMMachining_LargeMilledPartIssue.Cast(theIssue)
            anExpectedSize = aLMPIssue.ExpectedMaxMilledPartSize()
            anActualSize = aLMPIssue.ActualMilledPartSize()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Size (LxWxH)", "mm",
                Dimension(anExpectedSize.Length(), anExpectedSize.Width(), anExpectedSize.Height()),
                "Actual Size (LxWxH)", "mm",
                Dimension(anActualSize.Length(), anActualSize.Width(), anActualSize.Height()),
                theShapeIdVector)
            theManager.AddGroupData("Large Milled Part(s)", "(17, 37, 205)", aFeatureData, theCount)
        elif mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.CompareType(theIssue):
            aMSICRIssue = mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Radius", "mm", aMSICRIssue.ExpectedMinRadius(),
                "Actual Radius", "mm", aMSICRIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Small Radius Milled Part Internal Corner(s)", "(10, 10, 200)", aFeatureData, theCount)
        elif mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.CompareType(theIssue):
            aNPMPSIssue = mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString1(
                "Actual Angle", "deg", aNPMPSIssue.ActualAngle() * 180 / math.pi,
                theShapeIdVector)
            theManager.AddGroupData("Non Perpendicular Milled Part Shape(s)", "(129, 227, 138)", aFeatureData, theCount)
        elif mtk.DFMMachining_MilledPartExternalEdgeFilletIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Milled Part External Edge Fillet(s)", "(201, 227, 13)", aFeatureData, theCount)
        elif mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.CompareType(theIssue):
            anInconsistentRadiusIssue = mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Radius", "mm", anInconsistentRadiusIssue.ExpectedRadius(),
                "Actual Radius", "mm", anInconsistentRadiusIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Inconsistent Radius Milled Part Floor Fillet Issue(s)", "(180, 15, 190)", aFeatureData, theCount)
        elif mtk.DFMMachining_NarrowRegionInPocketIssue.CompareType(theIssue):
            aNarrowRegionIssue = mtk.DFMMachining_NarrowRegionInPocketIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Region Size", "mm", aNarrowRegionIssue.ExpectedMinRegionSize(),
                "Actual Region Size", "mm", aNarrowRegionIssue.ActualRegionSize(),
                theShapeIdVector)
            theManager.AddGroupData("Narrow Region In Pocket Issue(s)", "(70, 150, 150)", aFeatureData, theCount)
        elif mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.CompareType(theIssue):
            aLargeRatioIssue = mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Regions Maximum To Minimum Size Ratio", "", aLargeRatioIssue.ExpectedMaxRegionsMaxToMinSizeRatio(),
                "Actual Regions Maximum To Minimum Size Ratio", "", aLargeRatioIssue.ActualMaxRegionsMaxToMinSizeRatio(),
                theShapeIdVector)
            theManager.AddGroupData("Large Difference Regions Size In Pocket Issue(s)", "(100, 150, 150)", aFeatureData, theCount)

    @staticmethod
    def __AddTurningIssue(theManager: FeatureGroupManager, theIssue: mtk.DFMBase_Issue, theCount: int, theShapeIdVector):
        if mtk.DFMMachining_LargeTurnedPartIssue.CompareType(theIssue):
            aLTSIssue = mtk.DFMMachining_LargeTurnedPartIssue.Cast(theIssue)
            anExpectedSize = aLTSIssue.ExpectedMaxTurnedPartSize()
            anActualSize = aLTSIssue.ActualTurnedPartSize()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Size (LxR)", "mm", Pair(anExpectedSize.Length(), anExpectedSize.Radius()),
                "Actual Size (LxR)", "mm", Pair(anActualSize.Length(), anActualSize.Radius()),
                theShapeIdVector)
            theManager.AddGroupData("Large Turned Part(s)", "(195, 195, 195)", aFeatureData, theCount)
        elif mtk.DFMMachining_LongSlenderTurnedPartIssue.CompareType(theIssue):
            aLSTIssue = mtk.DFMMachining_LongSlenderTurnedPartIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Expected Maximum Length", "mm", aLSTIssue.ExpectedMaxLength(),
                "Actual Length", "mm", aLSTIssue.ActualLength(),
                "Actual Minimum Diameter", "mm", aLSTIssue.ActualMinDiameter(),
                theShapeIdVector)
            theManager.AddGroupData("Long-Slender Turned Part(s)", "(195, 195, 195)", aFeatureData, theCount)
        elif mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.CompareType(theIssue):
            aBBHRIssue = mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Expected Minimum Relief Depth", "mm", aBBHRIssue.ExpectedMinReliefDepth(),
                "Actual Relief Depth", "mm", aBBHRIssue.ActualReliefDepth(),
                "Actual Diameter", "mm", aBBHRIssue.ActualDiameter(),
                theShapeIdVector)
            theManager.AddGroupData("Small Depth Blind Bored Hole Relief(s)", "(88, 19, 94)", aFeatureData, theCount)
        elif mtk.DFMMachining_DeepBoredHoleIssue.CompareType(theIssue):
            aISBHIssue = mtk.DFMMachining_DeepBoredHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Expected Maximum Depth", "mm", aISBHIssue.ExpectedMaxDepth(),
                "Actual Depth", "mm", aISBHIssue.ActualDepth(),
                "Actual Diameter", "mm", aISBHIssue.ActualDiameter(),
                theShapeIdVector);
            theManager.AddGroupData("Deep Bored Hole(s)", "(161, 251, 142)", aFeatureData, theCount)
        elif mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.CompareType(theIssue):
            aODPRIssue = mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Face Incline Angle", "deg", aODPRIssue.ExpectedMaxFaceInclineAngle() * 180 / math.pi,
                "Actual Face Incline Angle", "deg", aODPRIssue.ActualFaceInclineAngle() * 180 / math.pi,
                theShapeIdVector)
            theManager.AddGroupData("Irregular Turned Part Outer Diameter Profile Relief(s)", "(239, 136, 190)", aFeatureData, theCount)
        elif mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.CompareType(theIssue):
            aTSICRIssue = mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Radius", "mm", aTSICRIssue.ExpectedMinRadius(),
                "Actual Radius", "mm", aTSICRIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Small Radius Turned Part Internal Corner(s)", "(127, 130, 187)", aFeatureData, theCount)
        elif mtk.DFMMachining_SquareEndKeywayIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Square End Keyway(s)", "(157, 160, 207)", aFeatureData, theCount)
        elif mtk.DFMMachining_NonSymmetricalAxialSlotIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Non Symmetrical Axial Slot(s)", "(130, 170, 200)", aFeatureData, theCount)

    @staticmethod
    def __AddSheetMetalIssue(theManager: FeatureGroupManager, theIssue: mtk.DFMBase_Issue, theCount: int, theShapeIdVector):
        if mtk.DFMSheetMetal_FlatPatternInterferenceIssue.CompareType(theIssue):
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString0(theShapeIdVector)
            theManager.AddGroupData("Flat Pattern Interference(s)", "(115, 251, 253)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularCornerFilletRadiusNotchIssue.CompareType(theIssue):
            aICFRNIssue = mtk.DFMSheetMetal_IrregularCornerFilletRadiusNotchIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Corner Fillet Radius", "mm", aICFRNIssue.ExpectedCornerFilletRadius(),
                "Actual Corner Fillet Radius", "mm", aICFRNIssue.ActualCornerFilletRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Irregular Corner Fillet Radius Notch(es)", "(239, 136, 190)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularDepthExtrudedHoleIssue.CompareType(theIssue):
            aIDEHIssue = mtk.DFMSheetMetal_IrregularDepthExtrudedHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                "Expected Minimum Extruded Height", "mm", aIDEHIssue.ExpectedMinExtrudedHeight(),
                "Expected Maximum Extruded Height", "mm", aIDEHIssue.ExpectedMaxExtrudedHeight(),
                "Actual Extruded Height",           "mm", aIDEHIssue.ActualExtrudedHeight(),
                theShapeIdVector)
            theManager.AddGroupData("Irregular Depth Extruded Hole(s)", "(50, 120, 210)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularRadiusOpenHemBendIssue.CompareType(theIssue):
            aIROHBIssue = mtk.DFMSheetMetal_IrregularRadiusOpenHemBendIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Radius", "mm", aIROHBIssue.ExpectedRadius(),
                "Actual Radius", "mm", aIROHBIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Irregular Radius Open Hem Bend(s)", "(188, 121, 11)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_InconsistentRadiusBendIssue.CompareType(theIssue):
            aIRBIssue = mtk.DFMSheetMetal_InconsistentRadiusBendIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Radius", "mm", aIRBIssue.ExpectedRadius(),
                "Actual Radius",   "mm", aIRBIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Inconsistent Radius Bend(s)", "(0, 35, 245)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularSizeBendReliefIssue.CompareType(theIssue):
            aISBRIssue = mtk.DFMSheetMetal_IrregularSizeBendReliefIssue.Cast(theIssue)
            anExpectedRelief = aISBRIssue.ExpectedMinBendRelief()
            aFirstActualRelief = aISBRIssue.FirstActualRelief()
            aSecondActualRelief = aISBRIssue.SecondActualRelief()
            aFeatureData = ""
            if (not aFirstActualRelief.IsNull()) and (not aSecondActualRelief.IsNull()):
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString3(
                    "Expected Minimum Relief Size (LxW)", "mm", Pair(anExpectedRelief.Length(), anExpectedRelief.Width()),
                    "First Actual Relief Size (LxW)",     "mm", Pair(aFirstActualRelief.Length(), aFirstActualRelief.Width()),
                    "Second Actual Relief Size (LxW)",    "mm", Pair(aSecondActualRelief.Length(), aSecondActualRelief.Width()),
                    theShapeIdVector)
            elif aFirstActualRelief.IsNull():
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                    "Expected Minimum Relief Size (LxW)", "mm", Pair(anExpectedRelief.Length(), anExpectedRelief.Width()),
                    "Actual Relief Size (LxW)",           "mm", Pair(aSecondActualRelief.Length(), aSecondActualRelief.Width()),
                    theShapeIdVector)
            else:
                aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                    "Expected Minimum Relief Size (LxW)", "mm", Pair(anExpectedRelief.Length(), anExpectedRelief.Width()),
                    "Actual Relief Size (LxW)",           "mm", Pair(aFirstActualRelief.Length(), aFirstActualRelief.Width()),
                    theShapeIdVector)
            theManager.AddGroupData("Irregular Size Bend Relief(s)", "(22, 65, 124)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularSizeNotchIssue.CompareType(theIssue):
            aISNIssue = mtk.DFMSheetMetal_IrregularSizeNotchIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Size (LxW)", "mm", Pair(aISNIssue.ExpectedLength(), aISNIssue.ExpectedWidth()),
                "Actual Size (LxW)",   "mm", Pair(aISNIssue.ActualLength(), aISNIssue.ActualWidth()),
                theShapeIdVector)
            theManager.AddGroupData("Irregular Size Notch(s)", "(255, 254, 145)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_IrregularSizeTabIssue.CompareType(theIssue):
            aISTIssue = mtk.DFMSheetMetal_IrregularSizeTabIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Size (LxW)", "mm", Pair(aISTIssue.ExpectedLength(), aISTIssue.ExpectedWidth()),
                "Actual Size (LxW)",   "mm", Pair(aISTIssue.ActualLength(), aISTIssue.ActualWidth()),
                theShapeIdVector)
            theManager.AddGroupData("Irregular Size Tab(s)", "(240, 155, 89)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_LargeDepthBeadIssue.CompareType(theIssue):
            aLDBIssue = mtk.DFMSheetMetal_LargeDepthBeadIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Maximum Depth", "mm", aLDBIssue.ExpectedMaxDepth(),
                "Actual Depth",           "mm", aLDBIssue.ActualDepth(),
                theShapeIdVector)
            theManager.AddGroupData("Large Depth Bead(s)", "(129, 127, 38)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallDepthLouverIssue.CompareType(theIssue):
            aSDLIssue = mtk.DFMSheetMetal_SmallDepthLouverIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Depth", "mm", aSDLIssue.ExpectedMinDepth(),
                "Actual Depth",           "mm", aSDLIssue.ActualDepth(),
                theShapeIdVector)
            theManager.AddGroupData("Small Depth Louver(s)", "(190, 127, 58)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_NonStandardSheetSizeIssue.CompareType(theIssue):
            aNSSSIssue = mtk.DFMSheetMetal_NonStandardSheetSizeIssue.Cast(theIssue)
            aNesrestStandardSize = aNSSSIssue.NearestStandardSheetSize()
            anActualSize = aNSSSIssue.ActualSheetSize()
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Nearest Standard Size (LxW)", "mm", Pair(aNesrestStandardSize.Length(), aNesrestStandardSize.Width()),
                "Actual Size (LxW)",           "mm", Pair(anActualSize.Length(), anActualSize.Width()),
                theShapeIdVector)
            theManager.AddGroupData("Non Standard Sheet Size(s)", "(0, 0, 0)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_NonStandardSheetThicknessIssue.CompareType(theIssue):
            aNSSTIssue = mtk.DFMSheetMetal_NonStandardSheetThicknessIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Nearest Standard Thickness", "mm", aNSSTIssue.NearestStandardSheetThickness(),
                "Actual Thickness",           "mm", aNSSTIssue.ActualSheetThickness(),
                theShapeIdVector)
            theManager.AddGroupData("Non Standard Sheet Thickness(s)", "(0, 0, 0)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallDiameterHoleIssue.CompareType(theIssue):
            aSDHIssue = mtk.DFMSheetMetal_SmallDiameterHoleIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Diameter", "mm", aSDHIssue.ExpectedMinDiameter(),
                "Actual Diameter",           "mm", aSDHIssue.ActualDiameter(),
                theShapeIdVector)
            theManager.AddGroupData("Small Diameter Hole(s)", "(115, 43, 245)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallLengthFlangeIssue.CompareType(theIssue):
            aSLFIssue = mtk.DFMSheetMetal_SmallLengthFlangeIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Length", "mm", aSLFIssue.ExpectedMinLength(),
                "Actual Length",           "mm", aSLFIssue.ActualLength(),
                theShapeIdVector)
            theManager.AddGroupData("Small Length Flange(s)", "(88, 19, 94)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallLengthHemBendFlangeIssue.CompareType(theIssue):
            aSLHBFIssue = mtk.DFMSheetMetal_SmallLengthHemBendFlangeIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Length", "mm", aSLHBFIssue.ExpectedMinLength(),
                "Actual Length",           "mm", aSLHBFIssue.ActualLength(),
                theShapeIdVector)
            theManager.AddGroupData("Small Length Hem Bend Flange(s)", "(70, 139, 51)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallRadiusBendIssue.CompareType(theIssue):
            aSRBIssue = mtk.DFMSheetMetal_SmallRadiusBendIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Radius", "mm", aSRBIssue.ExpectedMinRadius(),
                "Actual Radius",           "mm", aSRBIssue.ActualRadius(),
                theShapeIdVector)
            theManager.AddGroupData("Small Radius Bend(s)", "(161, 251, 142)", aFeatureData, theCount)
        elif mtk.DFMSheetMetal_SmallDistanceBetweenFeaturesIssue.CompareType(theIssue):
            aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenFeaturesIssue.Cast(theIssue)
            aFeatureData = MTKConverter_Report.__WriteFeatureDataToString2(
                "Expected Minimum Distance", "mm", aSDIssue.ExpectedMinDistanceBetweenFeatures(),
                "Actual Distance",           "mm", aSDIssue.ActualDistanceBetweenFeatures(),
                theShapeIdVector)
            theManager.AddGroupData(MTKConverter_Report.__SmallDistanceIssueName(aSDIssue),
                                    MTKConverter_Report.__SmallDistanceIssueColor(aSDIssue),
                                    aFeatureData, theCount)

    @staticmethod
    def __GetShapesId(theShape: cadex.ModelData_Shape, theBRep: cadex.ModelData_BRepRepresentation, theType):
        aShapeIdVector = []
        aShapeIt = cadex.ModelData_Shape_Iterator(theShape, theType)
        for aShape in aShapeIt:
            aShapeIdVector.append(theBRep.ShapeId(aShape))
        return aShapeIdVector

    @staticmethod
    def __AddShapesId(theShape: cadex.ModelData_Shape, theBRep: cadex.ModelData_BRepRepresentation, theType, theShapesIdVec):
        aShapeIt = cadex.ModelData_Shape_Iterator(theShape, theType)
        for aShape in aShapeIt:
            theShapesIdVec.append(theBRep.ShapeId(aShape))

    @staticmethod
    def __SortFeatures(theFeatures: mtk.MTKBase_FeatureList, theBRep: cadex.ModelData_BRepRepresentation,
                       theOrderedFeatureList: OrderedFeatureList):
        for aFeature in theFeatures:
            if mtk.MTKBase_CompositeFeature.CompareType(aFeature):
                aCompositeFeature = mtk.MTKBase_CompositeFeature.Cast(aFeature)
                MTKConverter_Report.__SortFeatures(aCompositeFeature.FeatureList(), theBRep, theOrderedFeatureList);
                continue

            #features
            if mtk.MTKBase_ShapeFeature.CompareType(aFeature):
                aShapeFeature = mtk.MTKBase_ShapeFeature.Cast(aFeature)
                aShapeType = cadex.ModelData_ST_Face
                if (mtk.SheetMetal_Cutout.CompareType(aFeature)
                    or (mtk.SheetMetal_Hole.CompareType(aFeature) and not mtk.SheetMetal_ComplexHole.CompareType(aFeature))
                    or mtk.SheetMetal_Notch.CompareType(aFeature) or mtk.SheetMetal_Tab.CompareType(aFeature)):
                    aShapeType = cadex.ModelData_ST_Edge
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aShapeFeature.Shape(), theBRep, aShapeType)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)

            #dfm machining drilling
            elif mtk.DFMMachining_DrillingIssue.CompareType(aFeature):
                anIssue = mtk.DFMMachining_DrillingIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(anIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)

            #dfm machining milling
            elif mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.CompareType(aFeature):
                aNSRMPFFIssue = mtk.DFMMachining_NonStandardRadiusMilledPartFloorFilletIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aNSRMPFFIssue.FloorFillet(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_DeepPocketIssue.CompareType(aFeature):
                aDCIssue = mtk.DFMMachining_DeepPocketIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aDCIssue.Pocket().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_HighBossIssue.CompareType(aFeature):
                aHBIssue = mtk.DFMMachining_HighBossIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aHBIssue.Boss().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_LargeMilledPartIssue.CompareType(aFeature):
                aShapeIdVector = []
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.CompareType(aFeature):
                aMSICRIssue = mtk.DFMMachining_SmallRadiusMilledPartInternalCornerIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aMSICRIssue.Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.CompareType(aFeature):
                aNPMPSIssue = mtk.DFMMachining_NonPerpendicularMilledPartShapeIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aNPMPSIssue.Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_MilledPartExternalEdgeFilletIssue.CompareType(aFeature):
                aMPEEFIssue = mtk.DFMMachining_MilledPartExternalEdgeFilletIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aMPEEFIssue.Fillet(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.CompareType(aFeature):
                aIRMPFFIssue = mtk.DFMMachining_InconsistentRadiusMilledPartFloorFilletIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aIRMPFFIssue.FloorFillet(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_NarrowRegionInPocketIssue.CompareType(aFeature):
                aNRIPIssue = mtk.DFMMachining_NarrowRegionInPocketIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aNRIPIssue.InnerFeature(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aNRIPIssue.NarrowRegionSidewall(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.CompareType(aFeature):
                aLDRSIPIssue = mtk.DFMMachining_LargeDifferenceRegionsSizeInPocketIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aLDRSIPIssue.InnerFeature(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector);
                MTKConverter_Report.__AddShapesId(aLDRSIPIssue.MinRegionPocketSidewall(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aLDRSIPIssue.MaxRegionPocketSidewall(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)

            #dfm machining turning
            elif mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.CompareType(aFeature):
                aBBHRIssue = mtk.DFMMachining_SmallDepthBlindBoredHoleReliefIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aBBHRIssue.BlindBoredHole(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_DeepBoredHoleIssue.CompareType(aFeature):
                aISBHIssue = mtk.DFMMachining_DeepBoredHoleIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aISBHIssue.Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.CompareType(aFeature):
                aODPRIssue = mtk.DFMMachining_IrregularTurnedPartOuterDiameterProfileReliefIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aODPRIssue.Face(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.CompareType(aFeature):
                aTSICRIssue = mtk.DFMMachining_SmallRadiusTurnedPartInternalCornerIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aTSICRIssue.Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_SquareEndKeywayIssue.CompareType(aFeature):
                aSEKIssue = mtk.DFMMachining_SquareEndKeywayIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aSEKIssue.Keyway().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_NonSymmetricalAxialSlotIssue.CompareType(aFeature):
                aNSASIssue = mtk.DFMMachining_NonSymmetricalAxialSlotIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aNSASIssue.AxialSlot().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_LargeTurnedPartIssue.CompareType(aFeature):
                aShapeIdVector = []
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMMachining_LongSlenderTurnedPartIssue.CompareType(aFeature):
                aShapeIdVector = []
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)

            #dfm sheet metal
            elif mtk.DFMSheetMetal_FlatPatternInterferenceIssue.CompareType(aFeature):
                aFPIIssue = mtk.DFMSheetMetal_FlatPatternInterferenceIssue.Cast(aFeature)
                aShapeIdVector = [theBRep.ShapeId(aFPIIssue.FirstFace()), theBRep.ShapeId(aFPIIssue.SecondFace())]
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularCornerFilletRadiusNotchIssue.CompareType(aFeature):
                aICFRNIssue = mtk.DFMSheetMetal_IrregularCornerFilletRadiusNotchIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aICFRNIssue.Notch().Shape(), theBRep, cadex.ModelData_ST_Edge)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularDepthExtrudedHoleIssue.CompareType(aFeature):
                aIDEHIssue = mtk.DFMSheetMetal_IrregularDepthExtrudedHoleIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aIDEHIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularRadiusOpenHemBendIssue.CompareType(aFeature):
                aIROHBIssue = mtk.DFMSheetMetal_IrregularRadiusOpenHemBendIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aIROHBIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_InconsistentRadiusBendIssue.CompareType(aFeature):
                aIRBIssue = mtk.DFMSheetMetal_InconsistentRadiusBendIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aIRBIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularSizeBendReliefIssue.CompareType(aFeature):
                aISBRIssue = mtk.DFMSheetMetal_IrregularSizeBendReliefIssue.Cast(aFeature)
                aFirstActualRelief = aISBRIssue.FirstActualRelief()
                aSecondActualRelief = aISBRIssue.SecondActualRelief()
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aISBRIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                if not aFirstActualRelief.IsNull():
                    MTKConverter_Report.__AddShapesId(aFirstActualRelief.Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                if not aSecondActualRelief.IsNull():
                    MTKConverter_Report.__AddShapesId(aSecondActualRelief.Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularSizeNotchIssue.CompareType(aFeature):
                aISNIssue = mtk.DFMSheetMetal_IrregularSizeNotchIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aISNIssue.Notch().Shape(), theBRep, cadex.ModelData_ST_Edge)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_IrregularSizeTabIssue.CompareType(aFeature):
                aISTIssue = mtk.DFMSheetMetal_IrregularSizeTabIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aISTIssue.Tab().Shape(), theBRep, cadex.ModelData_ST_Edge)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_LargeDepthBeadIssue.CompareType(aFeature):
                aLDBIssue = mtk.DFMSheetMetal_LargeDepthBeadIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aLDBIssue.Bead().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDepthLouverIssue.CompareType(aFeature):
                aSDLIssue = mtk.DFMSheetMetal_SmallDepthLouverIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aSDLIssue.Louver().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_NonStandardSheetSizeIssue.CompareType(aFeature):
                aShapeIdVector = []
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_NonStandardSheetThicknessIssue.CompareType(aFeature):
                aShapeIdVector = []
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDiameterHoleIssue.CompareType(aFeature):
                aSDHIssue = mtk.DFMSheetMetal_SmallDiameterHoleIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aSDHIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallLengthFlangeIssue.CompareType(aFeature):
                aSLFIssue = mtk.DFMSheetMetal_SmallLengthFlangeIssue.Cast(aFeature)
                aFlange = aSLFIssue.Flange().FeatureList()
                aShapeIdVector = []
                for aFlangeFace in aFlange:
                    if mtk.MTKBase_ShapeFeature.CompareType(aFlangeFace):
                        aShapeFeature = mtk.MTKBase_ShapeFeature.Cast(aFlangeFace)
                        MTKConverter_Report.__AddShapesId(aShapeFeature.Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallLengthHemBendFlangeIssue.CompareType(aFeature):
                aSLHBFIssue = mtk.DFMSheetMetal_SmallLengthHemBendFlangeIssue.Cast(aFeature)
                aFlange = aSLHBFIssue.Flange().FeatureList()
                aShapeIdVector = []
                for aFlangeFace in aFlange:
                    if mtk.MTKBase_ShapeFeature.CompareType(aFlangeFace):
                        aShapeFeature = mtk.MTKBase_ShapeFeature.Cast(aFlangeFace)
                        MTKConverter_Report.__AddShapesId(aShapeFeature.Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallRadiusBendIssue.CompareType(aFeature):
                aSRBIssue = mtk.DFMSheetMetal_SmallRadiusBendIssue.Cast(aFeature)
                aShapeIdVector = MTKConverter_Report.__GetShapesId(aSRBIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenBendAndLouverIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenBendAndLouverIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Louver().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndBendIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndBendIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndEdgeIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHoleAndEdgeIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                aShapeIdVector.append(theBRep.ShapeId(aSDIssue.Edge()))
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHolesIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenExtrudedHolesIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.FirstHole().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.SecondHole().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndBendIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndBendIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndCutoutIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndCutoutIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Cutout().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndEdgeIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndEdgeIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                aShapeIdVector.append(theBRep.ShapeId(aSDIssue.Edge()))
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndLouverIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndNotchIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Louver().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)    
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndNotchIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHoleAndNotchIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Hole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Notch().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenHolesIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenHolesIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.FirstHole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.SecondHole().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchAndBendIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenNotchAndBendIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.Notch().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.Bend().Shape(), theBRep, cadex.ModelData_ST_Face, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenNotchesIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenNotchesIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.FirstNotch().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.SecondNotch().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)
            elif mtk.DFMSheetMetal_SmallDistanceBetweenTabsIssue.CompareType(aFeature):
                aSDIssue = mtk.DFMSheetMetal_SmallDistanceBetweenTabsIssue.Cast(aFeature)
                aShapeIdVector = []
                MTKConverter_Report.__AddShapesId(aSDIssue.FirstTab().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                MTKConverter_Report.__AddShapesId(aSDIssue.SecondTab().Shape(), theBRep, cadex.ModelData_ST_Edge, aShapeIdVector)
                theOrderedFeatureList.Append(aFeature, aShapeIdVector)

    @staticmethod
    def __WriteFeatures(theWriter: JSONWriter, theGroupName: str, theSubgroupName: str, theFeatures: mtk.MTKBase_FeatureList,
                        theBRep: cadex.ModelData_BRepRepresentation, theMessageForEmptyList: str):
        theWriter.OpenSection(theSubgroupName)
        theWriter.WriteData("name", theGroupName)

        if theFeatures.IsEmpty():
            theWriter.WriteData("message", theMessageForEmptyList);
        else:
            aSortedFeatures = OrderedFeatureList()
            MTKConverter_Report.__SortFeatures(theFeatures, theBRep, aSortedFeatures)

            aFGManager = FeatureGroupManager()
            for i in range(aSortedFeatures.Size()):
                aFeature = aSortedFeatures.GetFeature(i)
                aCount = aSortedFeatures.GetFeatureCount(i)
                aShapeIDVec = aSortedFeatures.GetFeatureShapeIDs(i)

                if mtk.MTKBase_ShapeFeature.CompareType(aFeature):
                    MTKConverter_Report.__AddShapeFeature(aFGManager, mtk.MTKBase_ShapeFeature.Cast(aFeature),
                                                          aCount, aShapeIDVec)
                elif mtk.DFMMachining_DrillingIssue.CompareType(aFeature):
                    MTKConverter_Report.__AddDrillingIssue(aFGManager, mtk.DFMMachining_DrillingIssue.Cast(aFeature),
                                                           aCount, aShapeIDVec)
                elif mtk.DFMMachining_MillingIssue.CompareType(aFeature):
                    MTKConverter_Report.__AddMillingIssue(aFGManager, mtk.DFMMachining_MillingIssue.Cast(aFeature),
                                                          aCount, aShapeIDVec)
                elif (mtk.DFMSheetMetal_BendIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_FlatPatternInterferenceIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_HoleIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_IrregularCornerFilletRadiusNotchIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_IrregularDepthExtrudedHoleIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_IrregularSizeNotchIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_IrregularSizeTabIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_LargeDepthBeadIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_SmallDepthLouverIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_NonStandardSheetSizeIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_NonStandardSheetThicknessIssue.CompareType(aFeature)
                      or mtk.DFMSheetMetal_SmallDistanceBetweenFeaturesIssue.CompareType(aFeature)):
                    MTKConverter_Report.__AddSheetMetalIssue(aFGManager, mtk.DFMBase_Issue.Cast(aFeature),
                                                             aCount, aShapeIDVec)
                elif mtk.DFMBase_Issue.CompareType(aFeature):
                    MTKConverter_Report.__AddTurningIssue(aFGManager, mtk.DFMBase_Issue.Cast(aFeature),
                                                          aCount, aShapeIDVec)

            theWriter.WriteData("totalFeatureCount", aFGManager.TotalFeatureCount())
            theWriter.OpenArraySection("featureGroups")
            aFGManager.Write(theWriter)
            theWriter.CloseArraySection()

        theWriter.CloseSection()

        return True

    @staticmethod
    def __MachiningProcessName(theOperation):
        aProcessMap = {
            mtk.Machining_OT_Milling:      "CNC Machining Milling",
            mtk.Machining_OT_LatheMilling: "CNC Machining Lathe+Milling"
        }

        if theOperation in aProcessMap:
            return aProcessMap[theOperation]
        else:
            return "CNC Machining"

    @staticmethod
    def __HasShapes(theBRep: cadex.ModelData_BRepRepresentation, theType):
        aBodyList = theBRep.Get()
        for aBody in aBodyList:
            aShapeIt = cadex.ModelData_Shape_Iterator(aBody, theType)
            if aShapeIt.HasNext():
                return True
        return False

    @staticmethod
    def __WriteThicknessNode(theWriter: JSONWriter, theParamName: str, theParamValue: int,
                             thePoints: wt_proc.PointPair, theNodeName: str):
        aFirstPoint = thePoints.First
        aSecondPoint = thePoints.Second
        theWriter.OpenSection(theNodeName)
        theWriter.WriteData("name", theParamName)
        theWriter.WriteData("units", "mm")
        theWriter.WriteData("value", theParamValue)
        theWriter.WriteData("firstPoint",  Point(aFirstPoint.X(), aFirstPoint.Y(), aFirstPoint.Z()))
        theWriter.WriteData("secondPoint", Point(aSecondPoint.X(), aSecondPoint.Y(), aSecondPoint.Z()))
        theWriter.CloseSection()

    @staticmethod
    def __WriteUnfoldedPartFeatures(theWriter: JSONWriter, theData: sm_proc.MTKConverter_UnfoldedPartData):
        theWriter.OpenSection("featureRecognitionUnfolded")
        theWriter.WriteData("name", "Feature Recognition")

        if theData.myIsInit:
            aStream = io.StringIO()
            aWriter = JSONWriter(aStream, 4)

            aWriter.WriteData("parametersCount", 3)
            aWriter.OpenArraySection("parameters")
            MTKConverter_Report.__WriteParameter(aWriter, "Length",    "mm", theData.myLength)
            MTKConverter_Report.__WriteParameter(aWriter, "Width",     "mm", theData.myWidth)
            MTKConverter_Report.__WriteParameter(aWriter, "Thickness", "mm", theData.myThickness)
            MTKConverter_Report.__WriteParameter(aWriter, "Perimeter", "mm", theData.myPerimeter)
            aWriter.CloseArraySection()

            theWriter.WriteRawData(aStream.getvalue())
            aStream.close()
        else:
            theWriter.WriteData("message", "Unfolded part wasn't generated.")

        theWriter.CloseSection()

    @staticmethod
    def __WritePartProcessData(theWriter: JSONWriter, theProcessData):
        aRes = False
        theWriter.WriteData("partId", theProcessData.myPart.Uuid())

        anErrorMsg = "An error occurred while processing the part."
        if type(theProcessData) is mach_proc.MTKConverter_MachiningData:
            theWriter.WriteData("process", MTKConverter_Report.__MachiningProcessName(theProcessData.myOperation))
            aBRep = theProcessData.myPart.BRepRepresentation()
            if not theProcessData.myFeatureList.IsEmpty():
                MTKConverter_Report.__WriteFeatures(theWriter, "Feature Recognition", "featureRecognition",
                                                    theProcessData.myFeatureList, aBRep, "")
                MTKConverter_Report.__WriteFeatures(theWriter, "Design for Manufacturing", "dfm", theProcessData.myIssueList, aBRep,
                                                    "Part contains no DFM improvement suggestions.")
                aRes = True
            elif (not aBRep) or (not MTKConverter_Report.__HasShapes(aBRep, cadex.ModelData_ST_Solid)):
                anErrorMsg = "The part can't be analyzed due to lack of: BRep representation or solids in BRep representation."
        elif type(theProcessData) is wt_proc.MTKConverter_WallThicknessData:
            theWriter.WriteData("process", "Wall Thickness Analysis")
            aBRep = theProcessData.myPart.BRepRepresentation()
            aPoly = theProcessData.myPart.PolyRepresentation(cadex.ModelData_RM_Any)
            if theProcessData.myIsInit:
                MTKConverter_Report.__WriteThicknessNode (theWriter, "Minimum Thickness", theProcessData.myMinThickness,
                                                          theProcessData.myMinThicknessPoints, "minThickness")
                MTKConverter_Report.__WriteThicknessNode (theWriter, "Maximum Thickness", theProcessData.myMaxThickness,
                                                          theProcessData.myMaxThicknessPoints, "maxThickness")
                aRes = True
            elif ((not aBRep) or (not MTKConverter_Report.__HasShapes (aBRep, cadex.ModelData_ST_Solid))) and (aPoly.IsNull()):
                anErrorMsg = "The part can't be analyzed due to lack of: BRep representation, solids in BRep representation or Poly representations."
        elif type(theProcessData) is sm_proc.MTKConverter_SheetMetalData:
            theWriter.WriteData("process", "Sheet Metal")
            aBRep = theProcessData.myPart.BRepRepresentation()
            if theProcessData.myIsSheetMetalPart:
                MTKConverter_Report.__WriteFeatures(theWriter, "Feature Recognition", "featureRecognition",
                                                    theProcessData.myFeatureList, aBRep, "Part contains no features.")
                MTKConverter_Report.__WriteFeatures(theWriter, "Design for Manufacturing", "dfm", theProcessData.myIssueList, aBRep,
                                                    "Part contains no DFM improvement suggestions.")

                anUnfoldedPartData = theProcessData.myUnfoldedPartData
                MTKConverter_Report.__WriteUnfoldedPartFeatures(theWriter, anUnfoldedPartData)
                if anUnfoldedPartData.myIsInit:
                    MTKConverter_Report.__WriteFeatures(theWriter, "Design for Manufacturing", "dfmUnfolded",
                                                        anUnfoldedPartData.myIssueList, anUnfoldedPartData.myBRep,
                                                        "Unfolded part contains no DFM improvement suggestions.")
                aRes = True
            elif ((not aBRep) or ((not MTKConverter_Report.__HasShapes (aBRep, cadex.ModelData_ST_Solid))
                                  and (not MTKConverter_Report.__HasShapes (aBRep, cadex.ModelData_ST_Shell)))):
                anErrorMsg = "The part can't be analyzed due to lack of: BRep representation, solids and shells in BRep representation."
            else:
                anErrorMsg = "The part wasn't recognized as a sheet metal part."
        else:
            anErrorMsg = "Unrecognized process"

        if not aRes:
            theWriter.WriteData("error", anErrorMsg)

