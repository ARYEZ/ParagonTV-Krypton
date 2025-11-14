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

import xbmc
import xbmcgui
from Globals import *


class BrowseWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.log("__init__")

        # The selected browse option
        self.selectedAction = None

        # Window property for tracking state
        self.propertyWindow = xbmcgui.Window(10000)

    def onInit(self):
        self.log("onInit")

        # Set property to indicate this window is open
        self.propertyWindow.setProperty("PTV.BrowseWindow", "true")

        # Window is ready, controls are available
        self.setFocusId(9001)  # Focus on Movies by default

    def onClick(self, controlId):
        """Handle button clicks"""
        self.log("onClick " + str(controlId))

        if controlId == 9001:  # Movies
            self.selectedAction = "movies"
            # Set property for video browsing
            self.propertyWindow.setProperty("PTV.Browsing", "true")
            self.close()
        elif controlId == 9002:  # TV Shows
            self.selectedAction = "tvshows"
            # Set property for video browsing
            self.propertyWindow.setProperty("PTV.Browsing", "true")
            self.close()
        elif controlId == 9003:  # Music Videos
            self.selectedAction = "musicvideos"
            # Set property for video browsing
            self.propertyWindow.setProperty("PTV.Browsing", "true")
            self.close()
        elif controlId == 9004:  # Video Add-ons
            self.selectedAction = "addons"
            # Set property for video browsing
            self.propertyWindow.setProperty("PTV.Browsing", "true")
            self.close()
        elif controlId == 9005:  # Files
            self.selectedAction = "files"
            # Set property for video browsing
            self.propertyWindow.setProperty("PTV.Browsing", "true")
            self.close()
        elif controlId == 9006:  # Cancel
            self.close()

    def onAction(self, action):
        """Handle key presses"""
        actionId = action.getId()
        self.log("onAction " + str(actionId))

        # Close on back or escape
        if actionId in ACTION_PREVIOUS_MENU:
            self.close()

    def close(self):
        """Clean up properties when closing"""
        self.log("close")

        # Clear the browse window property
        self.propertyWindow.clearProperty("PTV.BrowseWindow")

        # If user didn't select anything that opens another window, clear browsing too
        if not self.selectedAction:
            self.propertyWindow.clearProperty("PTV.Browsing")

        # Call parent close
        xbmcgui.WindowXMLDialog.close(self)

    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log a message"""
        log("BrowseWindow: " + msg, level)
