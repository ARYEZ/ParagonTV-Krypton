#   Copyright (C) 2025 Aryez
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

import os

import xbmc
import xbmcaddon
import xbmcgui

# Constants
ADDON = xbmcaddon.Addon("script.paragontv")
ADDON_NAME = ADDON.getAddonInfo("name")
ICON = ADDON.getAddonInfo("icon")

ACTION_PREVIOUS_MENU = [9, 10, 92, 216, 247, 257, 275, 61467, 61448]
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4
ACTION_SELECT_ITEM = 7
ACTION_CONTEXT_MENU = 117  # Long press/right click


class SpeedDialWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.overlayWindow = None
        self.selectedAction = None
        self.speedDialShows = {}  # Dictionary for show speed dials
        self.speedDialChannels = {}  # Dictionary for channel speed dials

    def onInit(self):
        self.log("SpeedDialWindow onInit")

        # Load current speed dial settings
        self.loadSpeedDialSettings()

        # Update window properties for images and labels
        self.updateWindowProperties()

    def loadSpeedDialSettings(self):
        """Load saved speed dial settings from addon settings"""
        # Load show speed dials
        for i in range(1, 4):  # Only 3 shows now
            showInfo = ADDON.getSetting("SpeedDialShow%d" % i)
            if showInfo:
                try:
                    # Try to parse as dictionary (new format)
                    import ast

                    self.speedDialShows[str(i)] = ast.literal_eval(showInfo)
                except:
                    # Fall back to old format and convert
                    parts = showInfo.split("|")
                    if len(parts) >= 3:
                        self.speedDialShows[str(i)] = {
                            "title": parts[0],
                            "channel": int(parts[1]) if parts[1].isdigit() else 0,
                            "path": parts[2],
                        }
        
        # Load channel speed dials - THIS WAS MISSING!
        for i in range(1, 5):  # 4 channels in the window
            channelNum = ADDON.getSetting("SpeedDialChannel%d" % i)
            if channelNum and channelNum != "0":
                try:
                    self.speedDialChannels[i] = int(channelNum)
                except ValueError:
                    pass

    def updateWindowProperties(self):
        """Update window properties for all speed dial slots"""
        # Update show properties
        for i in range(1, 4):
            if str(i) in self.speedDialShows:
                self.updateShowProperties(i, self.speedDialShows[str(i)])
            else:
                # Clear properties for empty slots
                self.setProperty("SpeedDial.Show%d.Image" % i, "")
                self.setProperty("SpeedDial.Show%d.Name" % i, "")

        # Update channel properties
        for i in range(1, 5):
            if i in self.speedDialChannels:
                self.updateChannelProperties(i, self.speedDialChannels[i])
            else:
                # Clear properties for empty slots
                self.setProperty("SpeedDial.Channel%d.Image" % i, "")
                self.setProperty("SpeedDial.Channel%d.Name" % i, "")

    def updateShowProperties(self, slot, showInfo):
        """Update window properties for a show slot"""
        try:
            # Handle new dictionary format
            if isinstance(showInfo, dict):
                showName = showInfo.get("title", "")
                showPath = showInfo.get("path", "")
            else:
                # Handle old string format for backward compatibility
                parts = showInfo.split("|")
                showName = parts[0]
                showPath = parts[2] if len(parts) > 2 else None

            # Try to find landscape image for the show
            showImage = self.findShowLandscape(showName, showPath)

            self.setProperty("SpeedDial.Show%d.Name" % slot, showName)
            self.setProperty("SpeedDial.Show%d.Image" % slot, showImage or "")

        except Exception as e:
            self.log("Error updating show properties: " + str(e))

    def updateChannelProperties(self, slot, channelNum):
        """Update window properties for a channel slot"""
        if self.overlayWindow and channelNum <= self.overlayWindow.maxChannels:
            channel = self.overlayWindow.channels[channelNum - 1]
            channelName = channel.name

            # Look for channel landscape image
            channelImage = self.findChannelLandscape(channelName)

            self.setProperty(
                "SpeedDial.Channel%d.Name" % slot,
                "Ch %d: %s" % (channelNum, channelName),
            )
            self.setProperty("SpeedDial.Channel%d.Image" % slot, channelImage or "")

    def findShowLandscape(self, showName, showPath=None):
        """Find landscape image for a TV show"""
        # If we have a specific path, check there first
        if showPath and os.path.exists(showPath):
            # Look in the show folder
            artworkFiles = [
                "landscape.jpg",
                "landscape.png",
                "fanart.jpg",
                "fanart.png",
                "banner.jpg",
                "banner.png",
            ]
            for artFile in artworkFiles:
                artPath = os.path.join(showPath, artFile)
                if os.path.exists(artPath):
                    return artPath

        # Try to find in the library using JSON-RPC
        try:
            import json

            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "filter": {
                        "field": "title",
                        "operator": "contains",
                        "value": showName,
                    },
                    "properties": ["art"],
                },
                "id": 1,
            }
            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)

            if (
                "result" in result
                and "tvshows" in result["result"]
                and result["result"]["tvshows"]
            ):
                show = result["result"]["tvshows"][0]
                if "art" in show:
                    # Priority order for artwork
                    if "landscape" in show["art"]:
                        return show["art"]["landscape"]
                    elif "fanart" in show["art"]:
                        return show["art"]["fanart"]
                    elif "banner" in show["art"]:
                        return show["art"]["banner"]

        except Exception as e:
            self.log("Error searching library for show artwork: " + str(e))

        return None

    def findChannelLandscape(self, channelName):
        """Find landscape image for a channel"""
        if not self.overlayWindow:
            return None

        # Check for landscape version in channel logos folder
        landscapePath = self.overlayWindow.channelLogos + channelName + "_landscape.png"
        if os.path.exists(landscapePath):
            return landscapePath

        # Check for genre landscape (if channel name indicates genre)
        genreLandscapePath = (
            self.overlayWindow.channelLogos
            + "genre_"
            + channelName.lower()
            + "_landscape.png"
        )
        if os.path.exists(genreLandscapePath):
            return genreLandscapePath

        # Fallback to regular logo
        logoPath = self.overlayWindow.channelLogos + channelName + ".png"
        if os.path.exists(logoPath):
            return logoPath

        return None

    def onClick(self, controlId):
        """Handle button clicks"""
        self.log("SpeedDialWindow onClick: " + str(controlId))

        if controlId >= 9201 and controlId <= 9203:  # Show buttons
            showSlot = controlId - 9200
            self.handleShowButton(showSlot)

        elif controlId >= 9301 and controlId <= 9304:  # Channel buttons
            channelSlot = controlId - 9300
            self.handleChannelButton(channelSlot)

    def handleShowButton(self, slot):
        """Handle show button selection"""
        if str(slot) in self.speedDialShows:
            # Get default action setting
            defaultAction = int(ADDON.getSetting("SpeedDialDefaultAction"))
            
            if defaultAction == 0:  # Direct Jump/Play
                # Play show immediately
                self.selectedAction = ("playshow", self.speedDialShows[str(slot)])
                self.close()
            else:  # Show Menu
                # Show is assigned - offer full menu
                self.showShowMenu(slot)
        else:
            # Not assigned - offer to assign
            self.assignShow(slot)

    def handleChannelButton(self, slot):
        """Handle channel button selection"""
        if slot in self.speedDialChannels:
            # Get default action setting
            defaultAction = int(ADDON.getSetting("SpeedDialDefaultAction"))
            channel = self.speedDialChannels[slot]
            
            if defaultAction == 0:  # Direct Jump
                # Jump to channel immediately
                self.selectedAction = ("channel", channel)
                self.close()
            else:  # Show Menu
                # Channel is assigned - offer full menu
                self.showChannelMenu(slot)
        else:
            # Not assigned - offer to assign
            self.assignChannel(slot)

    def showShowMenu(self, slot):
        """Show menu for a show slot"""
        if str(slot) in self.speedDialShows:
            options = ["Play Show", "Change Assignment", "Remove Assignment"]
            select = xbmcgui.Dialog().select("Show %d Action" % slot, options)

            if select == 0:  # Play show
                self.selectedAction = ("playshow", self.speedDialShows[str(slot)])
                self.close()
            elif select == 1:  # Change assignment
                self.assignShow(slot)
            elif select == 2:  # Remove assignment
                del self.speedDialShows[str(slot)]
                ADDON.setSetting("SpeedDialShow%d" % slot, "")
                self.updateWindowProperties()

    def showChannelMenu(self, slot):
        """Show menu for a channel slot"""
        if slot in self.speedDialChannels:
            channel = self.speedDialChannels[slot]
            channelName = "Unknown"
            
            # Get channel name if possible
            if self.overlayWindow and channel <= self.overlayWindow.maxChannels:
                channelName = self.overlayWindow.channels[channel - 1].name
            
            options = [
                "Jump to Channel %d (%s)" % (channel, channelName),
                "Change Assignment", 
                "Remove Assignment"
            ]
            select = xbmcgui.Dialog().select("Channel %d Action" % slot, options)
            
            if select == 0:  # Jump to channel
                self.selectedAction = ("channel", channel)
                self.close()
            elif select == 1:  # Change assignment
                self.assignChannel(slot)
            elif select == 2:  # Remove assignment
                del self.speedDialChannels[slot]
                ADDON.setSetting("SpeedDialChannel%d" % slot, "0")
                self.updateWindowProperties()

    def assignShow(self, slot):
        """Assign a show to a speed dial slot"""
        if not self.overlayWindow:
            return

        # Get list of all available shows
        showList = self.getAllShows()

        if not showList:
            xbmcgui.Dialog().ok("No Shows", "No shows found in your channels.")
            return

        # Show selection dialog
        showNames = [show["name"] for show in showList]
        select = xbmcgui.Dialog().select("Select Show for Slot %d" % slot, showNames)

        if select >= 0:
            selectedShow = showList[select]
            # Store show info as a dictionary for the preemption system
            showInfo = {
                "title": selectedShow["name"],
                "path": selectedShow.get("path", ""),
                "channel": selectedShow.get("channel", 0),
            }
            self.speedDialShows[str(slot)] = showInfo
            ADDON.setSetting("SpeedDialShow%d" % slot, str(showInfo))
            self.updateWindowProperties()

    def assignChannel(self, slot):
        """Assign a channel to a speed dial slot"""
        if not self.overlayWindow:
            return

        # Option 1: Assign current channel
        # Option 2: Select from list
        options = [
            "Current Channel (%d)" % self.overlayWindow.currentChannel,
            "Select from List",
        ]
        select = xbmcgui.Dialog().select("Assign Channel", options)

        if select == 0:  # Current channel
            channel = self.overlayWindow.currentChannel
            self.speedDialChannels[slot] = channel
            ADDON.setSetting("SpeedDialChannel%d" % slot, str(channel))
            self.updateWindowProperties()

        elif select == 1:  # Select from list
            # Build channel list
            channelList = []
            for i in range(1, self.overlayWindow.maxChannels + 1):
                if self.overlayWindow.channels[i - 1].isValid:
                    channelName = self.overlayWindow.channels[i - 1].name
                    channelList.append("%d - %s" % (i, channelName))

            if channelList:
                channelSelect = xbmcgui.Dialog().select("Select Channel", channelList)
                if channelSelect >= 0:
                    # Extract channel number
                    channel = int(channelList[channelSelect].split(" - ")[0])
                    self.speedDialChannels[slot] = channel
                    ADDON.setSetting("SpeedDialChannel%d" % slot, str(channel))
                    self.updateWindowProperties()

    def getAllShows(self):
        """Get list of all unique shows from all channels"""
        shows = []

        if not self.overlayWindow:
            return []

        # For now, let's allow manual show assignment from library
        # Query the video library for all TV shows
        try:
            import json

            json_query = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.GetTVShows",
                "params": {
                    "properties": ["title", "file"],
                    "sort": {"order": "ascending", "method": "label"},
                },
                "id": 1,
            }
            result = xbmc.executeJSONRPC(json.dumps(json_query))
            result = json.loads(result)

            if "result" in result and "tvshows" in result["result"]:
                for show in result["result"]["tvshows"]:
                    shows.append(
                        {
                            "name": show["title"],
                            "channel": 0,  # Not channel specific
                            "path": "videodb://tvshows/titles/%d/" % show["tvshowid"],
                        }
                    )

        except Exception as e:
            self.log("Error getting shows from library: " + str(e))

        return shows

    def onAction(self, action):
        """Handle actions"""
        actionId = action.getId()
        self.log("SpeedDialWindow onAction: " + str(actionId))

        # Close on back, escape
        if actionId in ACTION_PREVIOUS_MENU:
            self.close()
        
        # Check for long press (context menu action)
        elif actionId == ACTION_CONTEXT_MENU:  # Context menu action (long press)
            # Get focused control
            focusId = self.getFocusId()
            
            # If we're in direct mode and user long-pressed, show menu instead
            if int(ADDON.getSetting("SpeedDialDefaultAction")) == 0 and bool(ADDON.getSetting("SpeedDialHoldForMenu")):
                if focusId >= 9201 and focusId <= 9203:  # Show buttons
                    self.showShowMenu(focusId - 9200)
                elif focusId >= 9301 and focusId <= 9304:  # Channel buttons
                    self.showChannelMenu(focusId - 9300)

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log messages"""
        xbmc.log(ADDON_NAME + " SpeedDialWindow: " + msg, level)