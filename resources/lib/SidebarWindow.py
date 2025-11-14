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

import time

import xbmc
import xbmcaddon
import xbmcgui
from Globals import *


class SidebarWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log("__init__")

        # Reference to overlay window
        self.overlayWindow = None

        # Control IDs (matching what we'll define in the XML)
        self.CONTROL_MENU_LIST = 6000
        self.CONTROL_CHANNEL_LOGO = 6001
        self.CONTROL_CHANNEL_NAME = 6002
        self.CONTROL_CURRENT_SHOW = 6003
        self.CONTROL_CURRENT_TIME = 6004
        self.CONTROL_BACKGROUND = 6005

        # Menu items
        self.menuItems = [
            ("EPG Guide", "epg"),
            ("Speed Dial", "speeddial"),
            ("Favorites", "favorites"),
            ("On Demand", "browse"),
            ("Playback", "settings"),
            ("Forecast", "weather"),
            ("Blackout", "blackout"),
            ("Flashback", "lastchannel"),
            ("Silence", "mute"),
        ]

        # Track selected action
        self.selectedAction = None

    def onInit(self):
        self.log("onInit")

        # Get controls
        self.menuList = self.getControl(self.CONTROL_MENU_LIST)
        self.channelLogo = self.getControl(self.CONTROL_CHANNEL_LOGO)
        self.channelName = self.getControl(self.CONTROL_CHANNEL_NAME)
        self.currentShow = self.getControl(self.CONTROL_CURRENT_SHOW)
        self.currentTime = self.getControl(self.CONTROL_CURRENT_TIME)

        # Populate menu
        self.populateMenu()

        # Update channel info
        self.updateChannelInfo()

        # Set focus to menu
        self.setFocus(self.menuList)

        self.log("onInit return")

    def populateMenu(self):
        """Populate the menu list"""
        self.log("populateMenu")

        # Clear existing items
        self.menuList.reset()

        # Add menu items
        for label, action in self.menuItems:
            item = xbmcgui.ListItem(label)
            # You can add icons here if desired
            # item.setArt({'icon': icon_path})
            self.menuList.addItem(item)

        # Select first item
        self.menuList.selectItem(0)

    def updateChannelInfo(self):
        """Update the channel information display"""
        if not self.overlayWindow:
            return

        try:
            # Get current channel info
            currentChannel = self.overlayWindow.currentChannel
            channel = self.overlayWindow.channels[currentChannel - 1]

            # Set channel name
            self.channelName.setLabel(
                "Channel " + str(currentChannel) + " - " + channel.name
            )

            # Set channel logo
            logoPath = self.overlayWindow.channelLogos + ascii(channel.name) + ".png"
            if not FileAccess.exists(logoPath):
                logoPath = IMAGES_LOC + "Default.png"
            self.channelLogo.setImage(logoPath)

            # Set current show info
            if self.overlayWindow.Player.isPlaying():
                position = xbmc.PlayList(xbmc.PLAYLIST_MUSIC).getposition()
                showTitle = channel.getItemTitle(position)
                episode = channel.getItemEpisodeTitle(position)

                if episode and episode != showTitle:
                    showInfo = showTitle + " - " + episode
                else:
                    showInfo = showTitle

                self.currentShow.setLabel(showInfo)

                # Set time info
                try:
                    currentTime = self.overlayWindow.Player.getTime()
                    totalTime = channel.getItemDuration(position)
                    timeStr = (
                        self.formatTime(currentTime)
                        + " / "
                        + self.formatTime(totalTime)
                    )
                    self.currentTime.setLabel(timeStr)
                except:
                    self.currentTime.setLabel("")
            else:
                self.currentShow.setLabel("Not Playing")
                self.currentTime.setLabel("")

        except Exception as e:
            self.log("Error updating channel info: " + str(e))

    def formatTime(self, seconds):
        """Format seconds to MM:SS or HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return "%d:%02d:%02d" % (hours, minutes, secs)
        else:
            return "%d:%02d" % (minutes, secs)

    def onClick(self, controlId):
        self.log("onClick " + str(controlId))

        if controlId == self.CONTROL_MENU_LIST:
            # Get selected position
            position = self.menuList.getSelectedPosition()

            if position >= 0 and position < len(self.menuItems):
                label, action = self.menuItems[position]
                self.selectedAction = action
                self.close()

    def onAction(self, act):
        action = act.getId()
        self.log("onAction " + str(action))

        # Handle back/escape
        if action in ACTION_PREVIOUS_MENU:
            self.selectedAction = None
            self.close()
        # Handle right arrow to close and return to video
        elif action == ACTION_MOVE_RIGHT:
            self.selectedAction = None
            self.close()

    def onFocus(self, controlId):
        pass

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("SidebarWindow: " + msg, level)
