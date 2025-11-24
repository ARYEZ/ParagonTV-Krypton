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

ADDON = xbmcaddon.Addon(id="script.paragontv")
CWD = ADDON.getAddonInfo("path").decode("utf-8")
RESOURCE = xbmc.translatePath(
    os.path.join(CWD, "resources", "lib").encode("utf-8")
).decode("utf-8")

sys.path.append(RESOURCE)

SkinID = xbmc.getSkinDir()
if not SkinID in ("skin.confluence", "skin.estuary"):
    import MyFont

    if MyFont.getSkinRes() == "1080i":
        MyFont.addFont("ParagonTv10", "Lato-Regular.ttf", "24")
        MyFont.addFont("ParagonTv12", "Lato-Regular.ttf", "25")
        MyFont.addFont("ParagonTv13", "Lato-Regular.ttf", "30")
        MyFont.addFont("ParagonTv14", "Lato-Regular.ttf", "33")
    else:
        MyFont.addFont("ParagonTv10", "Lato-Regular.ttf", "14")
        MyFont.addFont("ParagonTv12", "Lato-Regular.ttf", "16")
        MyFont.addFont("ParagonTv13", "Lato-Regular.ttf", "20")
        MyFont.addFont("ParagonTv14", "Lato-Regular.ttf", "22")

from xml.dom.minidom import parse, parseString

from AdvancedConfig import AdvancedConfig
from ChannelList import ChannelList
from FileAccess import FileAccess
from Globals import *
from Migrate import Migrate

NUMBER_CHANNEL_TYPES = 4


class ConfigWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.log("__init__")
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.madeChanges = 0
        self.showingList = True
        self.channel = 0
        self.channel_type = 9999
        self.setting1 = ""
        self.setting2 = ""
        self.savedRules = False

        if CHANNEL_SHARING:
            realloc = ADDON.getSetting("SettingsFolder")
            FileAccess.copy(realloc + "/settings2.xml", SETTINGS_LOC + "/settings2.xml")

        ADDON_SETTINGS.loadSettings()
        ADDON_SETTINGS.disableWriteOnSave()
        self.doModal()
        self.log("__init__ return")

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("ChannelConfig: " + msg, level)

    def onInit(self):
        self.log("onInit")

        # Hide all channel type controls first
        for i in range(8):  # Hide controls 120-127
            try:
                self.getControl(120 + i).setVisible(False)
            except (RuntimeError, AttributeError) as e:
                # Control doesn't exist in this skin - expected, ignore
                pass

        # Also hide Music Genre control
        try:
            self.getControl(128).setVisible(False)
        except (RuntimeError, AttributeError) as e:
            # Control doesn't exist in this skin - expected, ignore
            pass

        migratemaster = Migrate()
        migratemaster.migrate()
        self.prepareConfig()
        self.myRules = AdvancedConfig(
            "script.paragontv.AdvancedConfig.xml", CWD, "default"
        )

        # IMPORTANT: Make sure we start in list view
        self.getControl(106).setVisible(False)  # Hide channel details
        self.getControl(105).setVisible(True)  # Show channel list
        self.showingList = True
        self.setFocusId(102)  # Set focus to the list control

        self.log("onInit return")

    def onFocus(self, controlId):
        pass

    def onAction(self, act):
        action = act.getId()

        if action in ACTION_PREVIOUS_MENU:
            if not self.showingList:
                self.cancelChan()
                self.hideChanDetails()
            else:
                if self.madeChanges == 1:
                    dlg = xbmcgui.Dialog()

                    if dlg.yesno(xbmc.getLocalizedString(190), LANGUAGE(30032)):
                        ADDON_SETTINGS.writeSettings()

                        if CHANNEL_SHARING:
                            realloc = ADDON.getSetting("SettingsFolder")
                            FileAccess.copy(
                                SETTINGS_LOC + "/settings2.xml",
                                realloc + "/settings2.xml",
                            )

                self.close()
        elif act.getButtonCode() == 61575:  # Delete button
            curchan = self.listcontrol.getSelectedPosition() + 1

            if (self.showingList) and (
                ADDON_SETTINGS.getSetting("Channel_" + str(curchan) + "_type") != "9999"
            ):
                dlg = xbmcgui.Dialog()

                if dlg.yesno(xbmc.getLocalizedString(190), LANGUAGE(30033)):
                    ADDON_SETTINGS.setSetting(
                        "Channel_" + str(curchan) + "_type", "9999"
                    )
                    self.updateListing(curchan)
                    self.madeChanges = 1

    def saveSettings(self):
        self.log("saveSettings channel " + str(self.channel))
        chantype = 9999
        chan = str(self.channel)
        set1 = ""
        set2 = ""

        try:
            chantype = int(ADDON_SETTINGS.getSetting("Channel_" + chan + "_type"))
        except (ValueError, TypeError) as e:
            self.log("Unable to get channel type: {}".format(str(e)))

        setting1 = "Channel_" + chan + "_1"
        setting2 = "Channel_" + chan + "_2"

        if chantype == 0:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(130).getLabel2())
        elif chantype == 3:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(162).getLabel())
        elif chantype == 4:
            ADDON_SETTINGS.setSetting(setting1, self.getControl(172).getLabel())
        elif chantype == 12:  # Music Genre
            ADDON_SETTINGS.setSetting(setting1, self.getControl(212).getLabel())
        elif chantype == 9999:
            ADDON_SETTINGS.setSetting(setting1, "")
            ADDON_SETTINGS.setSetting(setting2, "")

        if self.savedRules:
            self.saveRules(self.channel)

        # Check to see if the user changed anything
        set1 = ""
        set2 = ""

        try:
            set1 = ADDON_SETTINGS.getSetting(setting1)
            set2 = ADDON_SETTINGS.getSetting(setting2)
        except Exception as e:
            self.log("Unable to get settings {}/{}: {}".format(setting1, setting2, str(e)), xbmc.LOGWARNING)

        if (
            chantype != self.channel_type
            or set1 != self.setting1
            or set2 != self.setting2
            or self.savedRules
        ):
            self.madeChanges = 1
            ADDON_SETTINGS.setSetting("Channel_" + chan + "_changed", "True")

        self.log("saveSettings return")

    def cancelChan(self):
        ADDON_SETTINGS.setSetting(
            "Channel_" + str(self.channel) + "_type", str(self.channel_type)
        )
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_1", self.setting1)
        ADDON_SETTINGS.setSetting("Channel_" + str(self.channel) + "_2", self.setting2)

    def hideChanDetails(self):
        self.getControl(106).setVisible(False)

        for i in range(NUMBER_CHANNEL_TYPES):
            try:
                self.getControl(120 + i).setVisible(False)
            except (RuntimeError, AttributeError):
                # Control doesn't exist in this skin - expected, ignore
                pass

        # Special handling for Music Genre control
        try:
            self.getControl(128).setVisible(False)
        except (RuntimeError, AttributeError):
            # Control doesn't exist in this skin - expected, ignore
            pass

        self.setFocusId(102)
        self.getControl(105).setVisible(True)
        self.showingList = True
        self.updateListing(self.channel)
        self.listcontrol.selectItem(self.channel - 1)

    def onClick(self, controlId):
        self.log("onClick " + str(controlId))

        if controlId == 102:  # Channel list entry selected
            self.getControl(105).setVisible(False)
            self.getControl(106).setVisible(True)
            self.channel = self.listcontrol.getSelectedPosition() + 1
            self.changeChanType(self.channel, 0)
            self.setFocusId(110)
            self.showingList = False
            self.savedRules = False
        elif controlId == 110:  # Change channel type left
            self.changeChanType(self.channel, -1)
        elif controlId == 111:  # Change channel type right
            self.changeChanType(self.channel, 1)
        elif controlId == 112:  # Ok button
            if not self.showingList:
                self.saveSettings()
                self.hideChanDetails()
            else:
                if self.madeChanges == 1:
                    ADDON_SETTINGS.writeSettings()
                    if CHANNEL_SHARING:
                        realloc = ADDON.getSetting("SettingsFolder")
                        FileAccess.copy(
                            SETTINGS_LOC + "/settings2.xml", realloc + "/settings2.xml"
                        )
                self.close()
        elif controlId == 113:  # Cancel button
            if not self.showingList:
                self.cancelChan()
                self.hideChanDetails()
            else:
                self.close()
        elif controlId == 114:  # Rules button
            self.myRules.ruleList = self.ruleList
            self.myRules.doModal()

            if self.myRules.wasSaved:
                self.ruleList = self.myRules.ruleList
                self.savedRules = True
        elif controlId == 130:  # Playlist-type channel, playlist button
            dlg = xbmcgui.Dialog()
            retval = dlg.browse(
                1,
                "Channel " + str(self.channel) + " Playlist",
                "files",
                ".xsp",
                False,
                False,
                "special://videoplaylists/",
            )

            if retval != "special://videoplaylists/":
                self.getControl(130).setLabel(
                    self.getSmartPlaylistName(retval), label2=retval
                )
        elif controlId == 160:  # TV Genre channel, left
            self.changeListData(self.showGenreList, 162, -1)
        elif controlId == 161:  # TV Genre channel, right
            self.changeListData(self.showGenreList, 162, 1)
        elif controlId == 170:  # Movie Genre channel, left
            self.changeListData(self.movieGenreList, 172, -1)
        elif controlId == 171:  # Movie Genre channel, right
            self.changeListData(self.movieGenreList, 172, 1)
        elif controlId == 210:  # Music Genre channel, left
            self.changeListData(self.musicGenreList, 212, -1)
        elif controlId == 211:  # Music Genre channel, right
            self.changeListData(self.musicGenreList, 212, 1)

        self.log("onClick return")

    def changeListData(self, thelist, controlid, val):
        self.log("changeListData " + str(controlid) + ", " + str(val))
        curval = self.getControl(controlid).getLabel()
        found = False
        index = 0

        if not thelist:
            self.getControl(controlid).setLabel("")
            self.log("changeListData return Empty list")
            return

        for item in thelist:
            if item == curval:
                found = True
                break

            index += 1

        if found:
            index += val

        while index < 0:
            index += len(thelist)

        while index >= len(thelist):
            index -= len(thelist)

        self.getControl(controlid).setLabel(thelist[index])
        self.log("changeListData return")

    def getSmartPlaylistName(self, fle):
        self.log("getSmartPlaylistName " + fle)
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except IOError as e:
            self.log("Unable to open smart playlist: {}".format(str(e)))
            return ""

        try:
            dom = parse(xml)
        except Exception as e:
            xml.close()
            self.log("getSmartPlaylistName return unable to parse: {}".format(str(e)))
            return ""

        xml.close()

        try:
            plname = dom.getElementsByTagName("name")
            self.log("getSmartPlaylistName return " + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except (IndexError, AttributeError) as e:
            self.log("Unable to find element name: {}".format(str(e)))

        self.log("getSmartPlaylistName return")

    def changeChanType(self, channel, val):
        self.log("changeChanType " + str(channel) + ", " + str(val))
        chantype = 9999

        try:
            chantype = int(
                ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type")
            )
        except Exception as e:
            self.log("Unable to get channel type: {}".format(str(e)))

        if val != 0:
            chantype += val

            # New channel type rotation: 0 -> 3 -> 4 -> 12 -> 9999
            if chantype < 0:
                chantype = 9999
            elif chantype == 1 or chantype == 2:
                chantype = 3  # Skip to TV Genre
            elif chantype == 5 or chantype == 6 or chantype == 7:
                chantype = 12  # Skip to Music Genre
            elif chantype == 8 or chantype == 9 or chantype == 10 or chantype == 11:
                chantype = 12  # Skip to Music Genre
            elif chantype == 13:
                chantype = 9999  # After Music Genre, go to None
            elif chantype > 12 and chantype < 9999:
                chantype = 9999
            elif chantype == 10000:
                chantype = 0

            ADDON_SETTINGS.setSetting(
                "Channel_" + str(channel) + "_type", str(chantype)
            )
        else:
            self.channel_type = chantype
            self.setting1 = ""
            self.setting2 = ""

            try:
                self.setting1 = ADDON_SETTINGS.getSetting(
                    "Channel_" + str(channel) + "_1"
                )
                self.setting2 = ADDON_SETTINGS.getSetting(
                    "Channel_" + str(channel) + "_2"
                )
            except Exception as e:
                self.log("Error getting channel settings: {}".format(str(e)), xbmc.LOGWARNING)

        # Hide all channel type controls first
        for i in range(8):  # Normal channel types (0-7)
            try:
                self.getControl(120 + i).setVisible(False)
            except Exception:
                # Control doesn't exist in this skin
                pass

        # Also hide Music Genre control
        try:
            self.getControl(128).setVisible(False)
        except Exception:
            # Control doesn't exist in this skin
            pass

        # Now show the appropriate control
        if chantype < 8:
            # Normal channel types (0-7)
            try:
                self.getControl(120 + chantype).setVisible(True)
                self.getControl(110).controlDown(
                    self.getControl(120 + ((chantype + 1) * 10))
                )
                try:
                    self.getControl(111).controlDown(
                        self.getControl(120 + ((chantype + 1) * 10 + 1))
                    )
                except Exception:
                    self.getControl(111).controlDown(
                        self.getControl(120 + ((chantype + 1) * 10))
                    )
            except Exception as e:
                self.log("Error setting control visibility: {}".format(str(e)), xbmc.LOGWARNING)
        elif chantype == 12:
            # Music Genre
            try:
                self.getControl(128).setVisible(True)
                self.getControl(110).controlDown(self.getControl(210))
                self.getControl(111).controlDown(self.getControl(211))
            except Exception as e:
                self.log("Error setting music genre control: {}".format(str(e)), xbmc.LOGWARNING)

        self.fillInDetails(channel)
        self.log("changeChanType return")

    def fillInDetails(self, channel):
        self.log("fillInDetails " + str(channel))
        self.getControl(104).setLabel("Channel " + str(channel))
        chantype = 9999
        chansetting1 = ""
        chansetting2 = ""

        try:
            chantype = int(
                ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_type")
            )
            chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_1")
            chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_2")
        except Exception as e:
            self.log("Unable to get some setting: {}".format(str(e)))

        self.getControl(109).setLabel(self.getChanTypeLabel(chantype))

        if chantype == 0:
            plname = self.getSmartPlaylistName(chansetting1)
            if not plname:
                chansetting1 = ""
            self.getControl(130).setLabel(
                self.getSmartPlaylistName(chansetting1), label2=chansetting1
            )
        elif chantype == 3:
            self.getControl(162).setLabel(
                self.findItemInList(self.showGenreList, chansetting1)
            )
        elif chantype == 4:
            self.getControl(172).setLabel(
                self.findItemInList(self.movieGenreList, chansetting1)
            )
        elif chantype == 12:
            self.getControl(212).setLabel(
                self.findItemInList(self.musicGenreList, chansetting1)
            )

        self.loadRules(channel)
        self.log("fillInDetails return")

    def loadRules(self, channel):
        self.log("loadRules")
        self.ruleList = []
        self.myRules.allRules

        try:
            rulecount = int(
                ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rulecount")
            )

            for i in range(rulecount):
                ruleid = int(
                    ADDON_SETTINGS.getSetting(
                        "Channel_" + str(channel) + "_rule_" + str(i + 1) + "_id"
                    )
                )

                for rule in self.myRules.allRules.ruleList:
                    if rule.getId() == ruleid:
                        self.ruleList.append(rule.copy())

                        for x in range(rule.getOptionCount()):
                            self.ruleList[-1].optionValues[x] = (
                                ADDON_SETTINGS.getSetting(
                                    "Channel_"
                                    + str(channel)
                                    + "_rule_"
                                    + str(i + 1)
                                    + "_opt_"
                                    + str(x + 1)
                                )
                            )

                        foundrule = True
                        break
        except Exception as e:
            self.log("Error loading rules: {}".format(str(e)), xbmc.LOGWARNING)
            self.ruleList = []

    def saveRules(self, channel):
        self.log("saveRules")
        rulecount = len(self.ruleList)
        ADDON_SETTINGS.setSetting(
            "Channel_" + str(channel) + "_rulecount", str(rulecount)
        )
        index = 1

        for rule in self.ruleList:
            ADDON_SETTINGS.setSetting(
                "Channel_" + str(channel) + "_rule_" + str(index) + "_id",
                str(rule.getId()),
            )

            for x in range(rule.getOptionCount()):
                ADDON_SETTINGS.setSetting(
                    "Channel_"
                    + str(channel)
                    + "_rule_"
                    + str(index)
                    + "_opt_"
                    + str(x + 1),
                    rule.getOptionValue(x),
                )

            index += 1

    def findItemInList(self, thelist, item):
        loitem = item.lower()

        for i in thelist:
            if loitem == i.lower():
                return item

        if thelist:
            return thelist[0]

        return ""

    def getChanTypeLabel(self, chantype):
        if chantype == 0:
            return "Custom Playlist"
        elif chantype == 3:
            return "TV Genre"
        elif chantype == 4:
            return "Movie Genre"
        elif chantype == 12:
            return "Music Genre"
        elif chantype == 9999:
            return "None"
        return ""

    def prepareConfig(self):
        self.log("prepareConfig")
        self.musicGenreList = []  # Initialize music genre list
        self.getControl(105).setVisible(False)
        self.getControl(106).setVisible(False)
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        chnlst = ChannelList()
        chnlst.fillTVInfo()
        chnlst.fillMovieInfo()
        self.log("prepareConfig calling fillMusicInfo")
        chnlst.fillMusicInfo()  # Fill music genres
        self.log(
            "prepareConfig musicGenreList length: " + str(len(chnlst.musicGenreList))
        )
        self.log("prepareConfig musicGenreList content: " + str(chnlst.musicGenreList))
        self.showGenreList = chnlst.showGenreList
        self.movieGenreList = chnlst.movieGenreList
        self.musicGenreList = chnlst.musicGenreList  # Get music genre list

        self.listcontrol = self.getControl(102)

        for i in range(999):
            theitem = xbmcgui.ListItem()
            theitem.setLabel(str(i + 1))
            self.listcontrol.addItem(theitem)

        self.updateListing()
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        self.getControl(105).setVisible(True)
        self.getControl(106).setVisible(False)
        self.setFocusId(102)
        self.log("prepareConfig return")

    def updateListing(self, channel=-1):
        self.log("updateListing")
        start = 0
        end = 999

        if channel > -1:
            start = channel - 1
            end = channel

        for i in range(start, end):
            theitem = self.listcontrol.getListItem(i)
            chantype = 9999
            chansetting1 = ""
            chansetting2 = ""
            newlabel = ""

            try:
                chantype = int(
                    ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type")
                )
                chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_1")
                chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2")
            except Exception as e:
                self.log("Error getting channel {} settings: {}".format(i+1, str(e)), xbmc.LOGWARNING)

            if chantype == 0:
                newlabel = self.getSmartPlaylistName(chansetting1)
            elif chantype == 3:
                newlabel = chansetting1 + " TV"
            elif chantype == 4:
                newlabel = chansetting1 + " Movies"
            elif chantype == 12:
                newlabel = chansetting1 + " Music"

            theitem.setLabel2(newlabel)

        self.log("updateListing return")


mydialog = ConfigWindow("script.paragontv.ChannelConfig.xml", CWD, "default")
del mydialog
