#   Copyright (C) 2025 Aryez
#
#
# This file is part of Paragon TV.
#
# Paragon TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Paragon TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Paragon TV.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import os
import random
import re
import subprocess
import sys
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui
from Globals import *
from Playlist import PlaylistItem


class RulesList:
    def __init__(self):
        # Updated rule list for simplified channel types
        self.ruleList = [
            BaseRule(),
            RenameRule(),
            DontAddChannel(),
            NoShowRule(),  # TV/Movie genres only
            OnlyUnWatchedRule(),  # TV/Movie genres only
            OnlyWatchedRule(),  # TV/Movie genres only
            InterleaveChannel(),  # Reinstated
            PlayShowInOrder(),  # TV genre only
            LimitMediaDuration(),  # New rule for all types
            PlotFilterRule(),  # New plot keyword filter
        ]

    def getRuleCount(self):
        return len(self.ruleList)

    def getRule(self, index):
        while index < 0:
            index += len(self.ruleList)

        while index >= len(self.ruleList):
            index -= len(self.ruleList)

        return self.ruleList[index]


class BaseRule:
    def __init__(self):
        self.name = ""
        self.description = ""
        self.optionLabels = []
        self.optionValues = []
        self.myId = 0
        self.actions = 0
        self.channelTypes = [0, 3, 4, 12]  # Compatible channel types

    def getName(self):
        return self.name

    def getTitle(self):
        return self.name

    def getOptionCount(self):
        return len(self.optionLabels)

    def onAction(self, act, optionindex):
        return ""

    def getOptionLabel(self, index):
        if index >= 0 and index < self.getOptionCount():
            return self.optionLabels[index]

        return ""

    def getOptionValue(self, index):
        if index >= 0 and index < len(self.optionValues):
            return self.optionValues[index]

        return ""

    def getRuleIndex(self, channeldata):
        index = 0

        for rule in channeldata.ruleList:
            if rule == self:
                return index

            index += 1

        return -1

    def getId(self):
        return self.myId

    def runAction(self, actionid, channelList, param):
        return param

    def copy(self):
        return BaseRule()

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("Rule " + self.getTitle() + ": " + msg, level)

    def validate(self):
        pass

    def reset(self):
        self.__init__()

    def isCompatible(self, channelType):
        return channelType in self.channelTypes

    def validateTextBox(self, optionindex, length):
        if len(self.optionValues[optionindex]) > length:
            self.optionValues[optionindex] = self.optionValues[optionindex][:length]

    def onActionTextBox(self, act, optionindex):
        action = act.getId()

        if act.getId() == ACTION_SELECT_ITEM:
            keyb = xbmc.Keyboard(self.optionValues[optionindex], self.name, False)
            keyb.doModal()

            if keyb.isConfirmed():
                self.optionValues[optionindex] = keyb.getText()

        button = act.getButtonCode()

        # Upper-case values
        if button >= 0x2F041 and button <= 0x2F05B:
            self.optionValues[optionindex] += chr(button - 0x2F000)

        # Lower-case values
        if button >= 0xF041 and button <= 0xF05B:
            self.optionValues[optionindex] += chr(button - 0xEFE0)

        # Numbers
        if action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            self.optionValues[optionindex] += chr(action - ACTION_NUMBER_0 + 48)

        # Backspace
        if button == 0xF008:
            if len(self.optionValues[optionindex]) >= 1:
                self.optionValues[optionindex] = self.optionValues[optionindex][:-1]

        # Delete
        if button == 0xF02E:
            self.optionValues[optionindex] = ""

        # Space
        if button == 0xF020:
            self.optionValues[optionindex] += " "

        if xbmc.getCondVisibility("Window.IsVisible(10111)"):
            self.log("shutdown window is visible")
            xbmc.executebuiltin("Dialog.close(10111)")

    def onActionSelectBox(self, act, optionindex):
        if act.getId() == ACTION_SELECT_ITEM:
            optioncount = len(self.selectBoxOptions[optionindex])
            cursel = -1

            for i in range(optioncount):
                if (
                    self.selectBoxOptions[optionindex][i]
                    == self.optionValues[optionindex]
                ):
                    cursel = i
                    break

            cursel += 1

            if cursel >= optioncount:
                cursel = 0

            self.optionValues[optionindex] = self.selectBoxOptions[optionindex][cursel]

    def validateDigitBox(self, optionindex, minimum, maximum, default):
        if len(self.optionValues[optionindex]) == 0:
            return

        try:
            val = int(self.optionValues[optionindex])

            if val >= minimum and val <= maximum:
                self.optionValues[optionindex] = str(val)

            return
        except:
            pass

        self.optionValues[optionindex] = str(default)

    def onActionDigitBox(self, act, optionindex):
        action = act.getId()

        if action == ACTION_SELECT_ITEM:
            dlg = xbmcgui.Dialog()
            value = dlg.numeric(
                0, self.optionLabels[optionindex], self.optionValues[optionindex]
            )

            if value != None:
                self.optionValues[optionindex] = value

        button = act.getButtonCode()

        # Numbers
        if action >= ACTION_NUMBER_0 and action <= ACTION_NUMBER_9:
            self.optionValues[optionindex] += chr(action - ACTION_NUMBER_0 + 48)

        # Backspace
        if button == 0xF008:
            if len(self.optionValues[optionindex]) >= 1:
                self.optionValues[optionindex] = self.optionValues[optionindex][:-1]

        # Delete
        if button == 0xF02E:
            self.optionValues[optionindex] = ""


class RenameRule(BaseRule):
    def __init__(self):
        self.name = "Set Channel Name"
        self.optionLabels = ["New Channel Name"]
        self.optionValues = [""]
        self.myId = 1
        self.actions = RULES_ACTION_FINAL_MADE | RULES_ACTION_FINAL_LOADED
        self.channelTypes = [0, 3, 4, 12]  # All channel types

    def copy(self):
        return RenameRule()

    def getTitle(self):
        if len(self.optionValues[0]) > 0:
            return "Rename Channel to " + self.optionValues[0]

        return self.name

    def onAction(self, act, optionindex):
        self.onActionTextBox(act, optionindex)
        self.validate()
        return self.optionValues[optionindex]

    def validate(self):
        self.validateTextBox(0, 18)

    def runAction(self, actionid, channelList, channeldata):
        if actionid == RULES_ACTION_FINAL_MADE or actionid == RULES_ACTION_FINAL_LOADED:
            self.validate()
            channeldata.name = self.optionValues[0]

        return channeldata


class NoShowRule(BaseRule):
    def __init__(self):
        self.name = "Don't Include a Show/Artist"
        self.optionLabels = ["Name to Exclude"]
        self.optionValues = [""]
        self.myId = 2
        self.actions = RULES_ACTION_LIST
        self.channelTypes = [3, 4, 12]  # Genre channels only

    def copy(self):
        return NoShowRule()

    def getTitle(self):
        if len(self.optionValues[0]) > 0:
            return "Don't Include '" + self.optionValues[0] + "'"

        return self.name

    def onAction(self, act, optionindex):
        self.onActionTextBox(act, optionindex)
        self.validate()
        return self.optionValues[optionindex]

    def validate(self):
        self.validateTextBox(0, 20)

    def runAction(self, actionid, channelList, filelist):
        if actionid == RULES_ACTION_LIST:
            self.validate()
            opt = self.optionValues[0].lower()
            realindex = 0

            for index in range(len(filelist)):
                item = filelist[realindex]
                loc = item.find(",")

                if loc > -1:
                    loc2 = item.find("//")

                    if loc2 > -1:
                        showname = item[loc + 1 : loc2]
                        showname = showname.lower()

                        if showname.find(opt) > -1:
                            filelist.pop(realindex)
                            realindex -= 1

                realindex += 1

        return filelist


class OnlyUnWatchedRule(BaseRule):
    def __init__(self):
        self.name = "Only Play Unwatched Items"
        self.optionLabels = []
        self.optionValues = []
        self.myId = 11
        self.actions = RULES_ACTION_JSON
        self.channelTypes = [3, 4]  # TV and Movie genres only

    def copy(self):
        return OnlyUnWatchedRule()

    def runAction(self, actionid, channelList, filedata):
        if actionid == RULES_ACTION_JSON:
            playcount = re.search('"playcount" *: *([0-9]*?),', filedata)
            pc = 0

            try:
                pc = int(playcount.group(1))
            except:
                pc = 0

            if pc > 0:
                return ""

        return filedata


class OnlyWatchedRule(BaseRule):
    def __init__(self):
        self.name = "Only Play Watched Items"
        self.optionLabels = []
        self.optionValues = []
        self.myId = 4
        self.actions = RULES_ACTION_JSON
        self.channelTypes = [3, 4]  # TV and Movie genres only

    def copy(self):
        return OnlyWatchedRule()

    def runAction(self, actionid, channelList, filedata):
        if actionid == RULES_ACTION_JSON:
            playcount = re.search('"playcount" *: *([0-9]*?),', filedata)
            pc = 0

            try:
                pc = int(playcount.group(1))
            except:
                pc = 0

            if pc == 0:
                return ""

        return filedata


class DontAddChannel(BaseRule):
    def __init__(self):
        self.name = "Don't Play This Channel"
        self.optionLabels = []
        self.optionValues = []
        self.myId = 5
        self.actions = RULES_ACTION_FINAL_MADE | RULES_ACTION_FINAL_LOADED
        self.channelTypes = [0, 3, 4, 12]  # All channel types

    def copy(self):
        return DontAddChannel()

    def runAction(self, actionid, channelList, channeldata):
        if actionid == RULES_ACTION_FINAL_MADE or actionid == RULES_ACTION_FINAL_LOADED:
            channeldata.isValid = False

        return channeldata


class InterleaveChannel(BaseRule):
    def __init__(self):
        self.name = "Interleave Another Channel"
        self.optionLabels = [
            "Channel Number",
            "Min Interleave Count",
            "Max Interleave Count",
        ]
        self.optionValues = ["0", "1", "1"]
        self.myId = 6
        self.actions = RULES_ACTION_LIST
        self.channelTypes = [0, 3, 4, 12]  # All channel types

    def copy(self):
        return InterleaveChannel()

    def getTitle(self):
        if len(self.optionValues[0]) > 0:
            return "Interleave Channel " + self.optionValues[0]

        return self.name

    def onAction(self, act, optionindex):
        self.onActionDigitBox(act, optionindex)
        self.validate()
        return self.optionValues[optionindex]

    def validate(self):
        self.validateDigitBox(0, 1, 1000, 0)
        self.validateDigitBox(1, 1, 100, 1)
        self.validateDigitBox(2, 1, 100, 1)

    def runAction(self, actionid, channelList, filelist):
        if actionid == RULES_ACTION_LIST:
            self.log("runAction")
            chan = 0
            minint = 0
            maxint = 0
            startingep = 1  # Hardcoded to always start from the beginning
            curchan = channelList.runningActionChannel
            curruleid = channelList.runningActionId
            self.validate()

            try:
                chan = int(self.optionValues[0])
                minint = int(self.optionValues[1])
                maxint = int(self.optionValues[2])
            except:
                self.log("Except when reading params")

            if chan > channelList.maxChannels or chan < 1 or minint < 1 or maxint < 1:
                return filelist

            if minint > maxint:
                v = minint
                minint = maxint
                maxint = v

            if (
                len(channelList.channels) < chan
                or channelList.channels[chan - 1].isSetup == False
            ):
                if channelList.myOverlay.isMaster:
                    channelList.setupChannel(chan, True, True, False)
                else:
                    channelList.setupChannel(chan, True, False, False)

            if channelList.channels[chan - 1].Playlist.size() < 1:
                self.log("The target channel is empty")
                return filelist

            realindex = random.randint(minint, maxint)
            startindex = 0
            # Use more memory, but greatly speed up the process by just putting everything into a new list
            newfilelist = []
            self.log("Length of original list: " + str(len(filelist)))

            while realindex < len(filelist):
                if channelList.threadPause() == False:
                    return filelist

                while startindex < realindex:
                    newfilelist.append(filelist[startindex])
                    startindex += 1

                newstr = (
                    str(channelList.channels[chan - 1].getItemDuration(startingep - 1))
                    + ","
                    + channelList.channels[chan - 1].getItemTitle(startingep - 1)
                )
                newstr += "//" + channelList.channels[chan - 1].getItemEpisodeTitle(
                    startingep - 1
                )
                newstr += (
                    "//"
                    + channelList.channels[chan - 1].getItemDescription(startingep - 1)
                    + "\n"
                    + channelList.channels[chan - 1].getItemFilename(startingep - 1)
                )
                newfilelist.append(newstr)
                realindex += random.randint(minint, maxint)
                startingep += 1

            while startindex < len(filelist):
                newfilelist.append(filelist[startindex])
                startindex += 1

            # No longer saving the starting episode since it's always 1
            self.log("Done interleaving, new length is " + str(len(newfilelist)))
            return newfilelist

        return filelist


class PlayShowInOrder(BaseRule):
    def __init__(self):
        self.name = "Play TV Shows In Order"
        self.optionLabels = []
        self.optionValues = []
        self.showInfo = []
        self.myId = 12
        self.actions = RULES_ACTION_START | RULES_ACTION_JSON | RULES_ACTION_LIST
        self.channelTypes = [3]  # TV genre only

    def copy(self):
        return PlayShowInOrder()

    def runAction(self, actionid, channelList, param):
        if actionid == RULES_ACTION_START:
            del self.showInfo[:]

        if actionid == RULES_ACTION_JSON:
            self.storeShowInfo(channelList, param)

        if actionid == RULES_ACTION_LIST:
            return self.sortShows(channelList, param)

        return param

    def storeShowInfo(self, channelList, filedata):
        # Store the filename, season, and episode number
        match = re.search('"file" *: *"(.*?)",', filedata)

        if match:
            showtitle = re.search('"showtitle" *: *"(.*?)"', filedata)
            season = re.search('"season" *: *(.*?),', filedata)
            episode = re.search('"episode" *: *(.*?),', filedata)

            try:
                seasonval = int(season.group(1))
                epval = int(episode.group(1))
                self.showInfo.append(
                    [
                        showtitle.group(1),
                        match.group(1).replace("\\\\", "\\"),
                        seasonval,
                        epval,
                    ]
                )
            except:
                pass

    def sortShows(self, channelList, filelist):
        if len(self.showInfo) == 0:
            return filelist

        newfilelist = []
        self.showInfo.sort(key=lambda seep: seep[3])
        self.showInfo.sort(key=lambda seep: seep[2])
        self.showInfo.sort(key=lambda seep: seep[0])

        # Create a new array. It will have 2 dimensions.  The first dimension is a certain show.  This show
        # name is in index 0 of the second dimension.  The currently used index is in index 1.  The other
        # items are the file names in season / episode order.
        showlist = []
        curshow = self.showInfo[0][0]
        showlist.append([])
        showlist[0].append(curshow.lower())
        showlist[0].append(0)

        for item in self.showInfo:
            if channelList.threadPause() == False:
                return filelist

            if item[0] != curshow:
                curshow = item[0]
                showlist.append([])
                showlist[-1].append(curshow.lower())
                showlist[-1].append(0)

            showstr = self.findInFileList(filelist, item[1])

            if len(showstr) > 0:
                showlist[-1].append(showstr)

        curindex = 0

        for item in filelist:
            if channelList.threadPause() == False:
                return filelist

            # First, get the current show for the entry
            pasttime = item.find(",")

            if pasttime > -1:
                endofshow = item.find("//")

                if endofshow > -1:
                    show = item[pasttime + 1 : endofshow].lower()

                    for entry in showlist:
                        if entry[0] == show:
                            if len(entry) == 2:
                                break

                            filelist[curindex] = entry[entry[1] + 2]
                            entry[1] += 1

                            if entry[1] > (len(entry) - 3):
                                entry[1] = 0

                            break

            curindex += 1

        return filelist

    def findInFileList(self, filelist, text):
        text = text.lower()

        for item in filelist:
            tmpitem = item.lower()

            if tmpitem.find(text) > -1:
                return item

        return ""


class LimitMediaDuration(BaseRule):
    def __init__(self):
        self.name = "Limit Media Duration"
        self.optionLabels = ["Maximum Duration (minutes)", "Minimum Duration (minutes)"]
        self.optionValues = ["60", "0"]
        self.myId = 17
        self.actions = RULES_ACTION_LIST
        self.channelTypes = [0, 3, 4, 12]  # All channel types

    def copy(self):
        return LimitMediaDuration()

    def getTitle(self):
        if len(self.optionValues[0]) > 0 or len(self.optionValues[1]) > 0:
            return (
                "Limit Duration: "
                + self.optionValues[1]
                + "-"
                + self.optionValues[0]
                + " min"
            )
        return self.name

    def onAction(self, act, optionindex):
        self.onActionDigitBox(act, optionindex)
        self.validate()
        return self.optionValues[optionindex]

    def validate(self):
        self.validateDigitBox(0, 0, 999, 60)
        self.validateDigitBox(1, 0, 999, 0)

    def runAction(self, actionid, channelList, filelist):
        if actionid == RULES_ACTION_LIST:
            self.validate()

            try:
                maxdur = int(self.optionValues[0]) * 60  # Convert to seconds
                mindur = int(self.optionValues[1]) * 60

                newfilelist = []

                for item in filelist:
                    loc = item.find(",")

                    if loc > -1:
                        try:
                            duration = int(item[:loc])

                            if mindur <= duration <= maxdur:
                                newfilelist.append(item)
                        except:
                            # If duration parsing fails, include the item
                            newfilelist.append(item)
                    else:
                        # If format is wrong, include the item
                        newfilelist.append(item)

                return newfilelist
            except:
                return filelist

        return filelist


class PlotFilterRule(BaseRule):
    def __init__(self):
        self.name = "Plot Keyword Filter"
        self.optionLabels = ["Keywords to Exclude (comma-separated)"]
        self.optionValues = ["Christmas,Santa,Thanksgiving,Pilgrims,Halloween"]
        self.myId = 26  # Unique ID
        self.actions = RULES_ACTION_JSON
        self.channelTypes = [0, 3, 4, 12]  # All channel types

    def copy(self):
        return PlotFilterRule()

    def getTitle(self):
        if len(self.optionValues[0]) > 0:
            keywords = self.optionValues[0]
            if len(keywords) > 30:
                keywords = keywords[:27] + "..."
            return "Exclude Plot Keywords: " + keywords
        return self.name

    def onAction(self, act, optionindex):
        self.onActionTextBox(act, optionindex)
        self.validate()
        return self.optionValues[optionindex]

    def validate(self):
        # Clean up the keyword list
        keywords = self.optionValues[0].strip()
        if keywords:
            # Remove extra spaces and empty entries
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
            self.optionValues[0] = ",".join(keyword_list)

    def runAction(self, actionid, channelList, filedata):
        if actionid == RULES_ACTION_JSON:
            if len(self.optionValues[0]) == 0:
                return filedata

            # Extract the plot/description from the JSON data
            plot_match = re.search(
                '"plot" *: *"(.*?)"', filedata, re.IGNORECASE | re.DOTALL
            )

            if plot_match:
                plot = plot_match.group(1).lower()
                keywords = self.optionValues[0].lower().split(",")

                for keyword in keywords:
                    keyword = keyword.strip()
                    if not keyword:
                        continue

                    # Always match whole words only using word boundaries
                    pattern = r"\b" + re.escape(keyword) + r"\b"
                    if re.search(pattern, plot):
                        self.log("Plot contains excluded keyword: " + keyword)
                        return ""  # Exclude this item

            # If we get here, the item passes the filter
            return filedata

        return filedata
