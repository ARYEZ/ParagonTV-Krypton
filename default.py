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

import os
import sys

import xbmc
import xbmcaddon
import xbmcgui

# Script constants
ADDON = xbmcaddon.Addon(id="script.paragontv")
ADDON_NAME = ADDON.getAddonInfo("name")
CWD = ADDON.getAddonInfo("path").decode("utf-8")
RESOURCE = xbmc.translatePath(
    os.path.join(CWD, "resources", "lib").encode("utf-8")
).decode("utf-8")

sys.path.append(RESOURCE)

# Check for command line arguments
if len(sys.argv) > 1:
    arg = sys.argv[1].upper()
    
    if arg == 'TEST_AUTOPILOT':
        # Test Autopilot connection
        import autopilot_service
        tester = autopilot_service.AutopilotTester()
        tester.test()
        sys.exit(0)
        
    elif arg == 'MANAGE_FAVORITES':
        # Launch favorite shows manager
        from favorites_manager import FavoritesManager
        manager = FavoritesManager()
        manager.show()
        sys.exit(0)
        
    elif arg == 'RESET':
        # Handle force channel reset
        xbmc.log("Paragon TV - Force reset requested", xbmc.LOGNOTICE)
        # This will be handled when the overlay starts
        
    # Add other command handlers as needed
    else:
        xbmc.log("Paragon TV - Unknown argument: {}".format(arg), xbmc.LOGWARNING)


# Font setup for non-Confluence/Estuary skins
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


def Start():
    """Start Paragon TV main interface"""
    # Check if we're in Autopilot Mode
    if ADDON.getSetting("AutopilotEnabled") == "true":
        xbmc.log("Paragon TV - Running in Autopilot Mode (satellite)", xbmc.LOGNOTICE)
        
        # Show status notification
        master_ip = ADDON.getSetting("AutopilotMasterIP")
        sync_status = ADDON.getSetting("AutopilotSyncStatus")
        last_sync = ADDON.getSetting("AutopilotLastSync")
        
        if sync_status == "Connected":
            message = "Connected to master: {}\nLast sync: {}".format(master_ip, last_sync)
            icon = xbmcgui.NOTIFICATION_INFO
        else:
            message = "Status: {}\nMaster: {}".format(sync_status, master_ip)
            icon = xbmcgui.NOTIFICATION_WARNING
            
        xbmcgui.Dialog().notification(
            "Paragon TV - Autopilot Mode",
            message,
            icon,
            5000
        )
    
    # Stop any playing media
    if xbmc.Player().isPlaying():
        xbmc.Player().stop()
    
    # Import and start the overlay
    import Overlay as Overlay
    
    # Pass command line argument if present
    reset_flag = len(sys.argv) > 1 and sys.argv[1].upper() == 'RESET'
    
    MyOverlayWindow = Overlay.TVOverlay(
        "script.paragontv.TVOverlay.xml", 
        CWD, 
        "default",
        forceReset=reset_flag
    )
    
    # Clean up
    del MyOverlayWindow
    xbmcgui.Window(10000).setProperty("ParagonTVRunning", "")


def CheckMultiInstance():
    """Check if Paragon TV is already running"""
    if xbmcgui.Window(10000).getProperty("ParagonTVRunning") != "True":
        xbmcgui.Window(10000).setProperty("ParagonTVRunning", "True")
        return False
    else:
        xbmc.log("script.ParagonTV - Already running, exiting", xbmc.LOGERROR)
        
        # Show user notification
        xbmcgui.Dialog().notification(
            ADDON_NAME,
            "Already running",
            xbmcgui.NOTIFICATION_WARNING,
            2000
        )
        return True


# Main entry point
if __name__ == "__main__":
    # Check for multiple instances
    if not CheckMultiInstance():
        try:
            Start()
        except Exception as e:
            xbmc.log("Paragon TV - Fatal error: {}".format(str(e)), xbmc.LOGERROR)
            xbmcgui.Window(10000).setProperty("ParagonTVRunning", "")
            
            # Show error to user
            xbmcgui.Dialog().notification(
                ADDON_NAME,
                "Error starting - check logs",
                xbmcgui.NOTIFICATION_ERROR,
                5000
            )