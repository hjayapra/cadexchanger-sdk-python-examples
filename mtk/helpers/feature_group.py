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

from functools import cmp_to_key

import cadexchanger.CadExMTK as mtk

class Pair:
    def __init__(self, theFirst: float, theSecond: float):
        self.First = theFirst
        self.Second = theSecond

    def __repr__(self):
        return f"Pair({self.First}, {self.Second})"

    def __str__(self):
        return f"{self.First:.5f} x {self.Second:.5f}"

class Dimension:
    def __init__(self, theX: float, theY: float, theZ: float):
        self.X = theX
        self.Y = theY
        self.Z = theZ

    def __repr__(self):
        return f"Dimension({self.X}, {self.Y}, {self.Z})"

    def __str__(self):
        return f"{self.X:.5f} x {self.Y:.5f} x {self.Z:.5f}"

class Direction:
    def __init__(self, theX: float, theY: float, theZ: float):
        self.X = theX
        self.Y = theY
        self.Z = theZ

    def __repr__(self):
        return f"Direction({self.X}, {self.Y}, {self.Z})"

    def __str__(self):
        return f"({self.X:.2f}, {self.Y:.2f}, {self.Z:.2f})"

def CompareFeatures(theA: mtk.MTKBase_Feature, theB: mtk.MTKBase_Feature):
    aComparator = mtk.MTKBase_FeatureComparator()
    anALessThanB = aComparator(theA, theB)
    if anALessThanB:
        return -1

    aBLessThanA = aComparator(theB, theA)
    if aBLessThanA:
        return 1

    return 0

class FeatureGroupManager:
    def __init__(self):
        self.__myGroups = []

    def AddFeature(self, theGroupName: str, theSubgroupName: str, theHasParameters: bool, theFeature: mtk.MTKBase_Feature):
        #find or create
        aRes = -1
        for i in range(len(self.__myGroups)):
            aGroup = self.__myGroups[i]
            if aGroup.myName == theGroupName:
                aRes = i
                break

        if aRes == -1:
            self.__myGroups.append(self.FeatureGroup(theGroupName, theSubgroupName, theHasParameters))
            aRes = len(self.__myGroups) - 1

        #update
        aGroup = self.__myGroups[aRes]
        aSubgroups = aGroup.myFeatureSubgroups
        aSubgroups.Append(theFeature)

    def Print(self, theFeatureType: str, thePrintFeatureParameters):
        self.__myGroups.sort(key=cmp_to_key(self.__compare))

        aTotalCount = 0
        for i in self.__myGroups:
            aFeatureCount = i.FeatureCount()
            aTotalCount += aFeatureCount

            print("    ", i.myName, ": ", aFeatureCount, sep="")

            if not i.myHasParameters:
                continue

            aSubgroupName = i.mySubgroupName
            for j in range(i.myFeatureSubgroups.Size()):
                print("        ", i.myFeatureSubgroups.GetFeatureCount(j), " ", aSubgroupName, " with", sep="")
                thePrintFeatureParameters(i.myFeatureSubgroups.GetFeature(j))

        print("\n    Total ", theFeatureType, ": ", aTotalCount, "\n", sep="")

    @staticmethod
    def PrintFeatureParameter(theName: str, theValue, theUnits: str):
        print("          ", theName, ": ", theValue, " ", theUnits, sep = "")

    class OrderedFeatureList:
        def __init__(self):
            self.__myList = []

        def Append(self, theFeature: mtk.MTKBase_Feature):
            anInsertIndex = 0
            for i in self.__myList:
                aRes = CompareFeatures(theFeature, i.Feature)
                if aRes == 0:
                    i.Count += 1
                    anInsertIndex = -1
                    break
                elif aRes < 0:
                    break

                anInsertIndex += 1

            if anInsertIndex >= 0:
                self.__myList.insert(anInsertIndex, self.FeatureAndCountPair(theFeature))

        def Size(self):
            return len(self.__myList)

        def GetFeature(self, theIndex: int):
            return self.__GetFeatureAndCountPair(theIndex).Feature

        def GetFeatureCount(self, theIndex: int):
            return self.__GetFeatureAndCountPair(theIndex).Count

        def __GetFeatureAndCountPair(self, theIndex: int):
            return self.__myList[theIndex]

        class FeatureAndCountPair:
            def __init__(self, theFeature: mtk.MTKBase_Feature):
                self.Feature = theFeature
                self.Count = 1

    class FeatureGroup:
        def __init__(self, theName: str, theSubgroupName: str, theHasParameters: bool):
            self.myName = theName
            self.mySubgroupName = theSubgroupName
            self.myHasParameters = theHasParameters
            self.myFeatureSubgroups = FeatureGroupManager.OrderedFeatureList()

        def FeatureCount(self):
            aCount = 0
            for i in range(self.myFeatureSubgroups.Size()):
                aCount += self.myFeatureSubgroups.GetFeatureCount(i)
            return aCount

    @staticmethod
    def __compare(theA: FeatureGroup, theB: FeatureGroup):
        anAName = theA.myName
        aBName = theB.myName
        if anAName == aBName:
            return 0

        anAFeatureSubgroups = theA.myFeatureSubgroups
        aBFeatureSubgroups = theB.myFeatureSubgroups
        if (not anAFeatureSubgroups) or (not aBFeatureSubgroups):
            if anAName < aBName:
                return -1
            else:
                return 1

        anAFeature = anAFeatureSubgroups.GetFeature(0)
        aBFeature = aBFeatureSubgroups.GetFeature(0)
        return CompareFeatures(anAFeature, aBFeature)
