#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# KODI Restart Files Monitor
# Checks for and removes potentially problematic restart files
#

import os
import time
from datetime import datetime

import xbmc
import xbmcaddon
import xbmcgui

# Get addon info
ADDON_ID = "script.paragontv"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")

# File paths to check
MARKER_FILE = "/storage/.kodi/addons/script.paragontv/.kodi_restart_marker"
KILL_SCRIPT = "/storage/.kodi/addons/script.paragontv/.kill_kodi.sh"


def log(msg, level=xbmc.LOGNOTICE):
    message = "[KODI Restart Files Monitor] {}".format(msg)
    xbmc.log(message, level)


def notify(message, heading="File Monitor", icon="", time=5000, sound=True):
    """Display a notification with custom icon"""

    # Use the addon icon or Kodi's info icon
    if icon == "":
        icon = os.path.join(ADDON_PATH, "resources", "images", "icon.png")
        if not os.path.exists(icon):
            icon = xbmcgui.NOTIFICATION_INFO

    # Display the notification
    xbmcgui.Dialog().notification(heading, message, icon, time, sound)


def check_files():
    """Check if the monitored files exist"""
    marker_exists = os.path.exists(MARKER_FILE)
    kill_script_exists = os.path.exists(KILL_SCRIPT)

    return marker_exists or kill_script_exists, marker_exists, kill_script_exists


def delete_files():
    """Delete the monitored files if they exist"""
    files_deleted = False

    if os.path.exists(MARKER_FILE):
        try:
            os.remove(MARKER_FILE)
            log("Deleted {}".format(MARKER_FILE), xbmc.LOGERROR)
            files_deleted = True
        except Exception as e:
            log("Error deleting {}: {}".format(MARKER_FILE, e), xbmc.LOGERROR)

    if os.path.exists(KILL_SCRIPT):
        try:
            os.remove(KILL_SCRIPT)
            log("Deleted {}".format(KILL_SCRIPT), xbmc.LOGERROR)
            files_deleted = True
        except Exception as e:
            log("Error deleting {}: {}".format(KILL_SCRIPT, e), xbmc.LOGERROR)

    return files_deleted


def main():
    """Main function - runs the file monitor"""
    log("Starting KODI Restart Files Monitor", xbmc.LOGERROR)

    # Show startup notification
    notify("Restart files monitoring service started", "File Monitor")

    # Variables to track state
    files_found_time = None

    # Main loop
    while not xbmc.abortRequested:
        try:
            # Check for files
            files_exist, marker_exists, kill_script_exists = check_files()

            if files_exist:
                # If this is the first time we've found the files, record the time
                if files_found_time is None:
                    files_found_time = datetime.now()
                    log(
                        "Suspicious files found at {}. Will check again in 10 minutes.".format(
                            files_found_time.strftime("%Y-%m-%d %H:%M:%S")
                        ),
                        xbmc.LOGERROR,
                    )
                else:
                    # Check if it's been 10 minutes since we first found the files
                    time_diff = (datetime.now() - files_found_time).total_seconds()

                    if time_diff >= 600:  # 10 minutes = 600 seconds
                        log(
                            "Suspicious files still present after 10 minutes. Deleting...",
                            xbmc.LOGERROR,
                        )
                        files_deleted = delete_files()

                        if files_deleted:
                            notify("Removed restart marker files", "File Monitor")

                        # Reset the timer
                        files_found_time = None
            else:
                # Files don't exist, reset the timer
                if files_found_time is not None:
                    log(
                        "Suspicious files no longer present. Resetting timer.",
                        xbmc.LOGERROR,
                    )
                    files_found_time = None

        except Exception as e:
            log("Error in file monitor: {}".format(e), xbmc.LOGERROR)

        # Check every 30 minutes (1800000 ms) if no files are found
        # Check every 1 minute (60000 ms) if files are found to be more responsive
        if files_found_time is None:
            xbmc.sleep(1800000)  # 30 minutes
        else:
            xbmc.sleep(60000)  # 1 minute

    log("File monitor ended")


# Run the monitor
if __name__ == "__main__":
    main()
