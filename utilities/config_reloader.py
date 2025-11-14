#!/usr/bin/python
#   Configuration Reloader for Paragon TV
#
# This script replaces settings2.xml with settings3.xml while preserving both files.

import os
import shutil
import sys
from datetime import datetime

# Try to import Kodi modules, but provide fallbacks for CLI usage
try:
    import xbmc
    import xbmcgui

    IN_KODI = True
except ImportError:
    IN_KODI = False

    # Define fallback functions for CLI usage
    class xbmc:
        LOGNOTICE = 1

        @staticmethod
        def log(msg, level=1):
            print(msg)

    class xbmcgui:
        class Dialog:
            @staticmethod
            def ok(*args):
                print(" ".join(str(arg) for arg in args[1:]))

            @staticmethod
            def yesno(*args):
                return True


# Get the path to settings files
# This works whether run as standalone or from PTVL
def get_settings_path(filename):
    # Hardcoded path to addon_data directory
    return "/storage/.kodi/userdata/addon_data/script.paragontv/{}".format(filename)


def log(message):
    """Log message to Kodi log or print to console"""
    if IN_KODI:
        xbmc.log("PTV Config Reloader: " + str(message), level=xbmc.LOGNOTICE)
    else:
        print("PTV Config Reloader: " + str(message))


def reload_configurations():
    """
    Reloads channel configurations by:
    1. Creating a backup of the current settings2.xml
    2. Replacing settings2.xml with a copy of settings3.xml
    3. Preserving the original settings3.xml
    """
    log("Starting configuration reload")

    try:
        # Define paths using the new function
        settings2_path = get_settings_path("settings2.xml")
        settings3_path = get_settings_path("settings3.xml")

        log("Using settings2 path: {0}".format(settings2_path))
        log("Using settings3 path: {0}".format(settings3_path))

        # Check if settings3.xml exists
        if not os.path.exists(settings3_path):
            log("ERROR: settings3.xml not found at {0}".format(settings3_path))
            if IN_KODI:
                xbmcgui.Dialog().ok(
                    "Error",
                    "settings3.xml not found!",
                    "Could not find settings3.xml at:",
                    settings3_path,
                )
            return False

        log("Found settings3.xml at: {0}".format(settings3_path))

        # Create backup of current settings2.xml
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = "{0}.backup_{1}".format(settings2_path, timestamp)

        # Copy current settings2.xml to backup
        if os.path.exists(settings2_path):
            shutil.copy2(settings2_path, backup_path)
            log("Created backup: {0}".format(backup_path))
        else:
            log("Note: No existing settings2.xml found to backup")

        # Copy settings3.xml to settings2.xml
        shutil.copy2(settings3_path, settings2_path)
        log("Copied settings3.xml to settings2.xml")

        # Now add the remote backup functionality
        try:
            # Remote Paragon TV details
            remote_ip = "10.0.0.91"
            remote_user = "root"  # Default LibreELEC username
            remote_path = "/storage/.kodi/addons/script.remoteartwork/resources/media/flags/numbers/"

            # Use scp to copy the file to the remote system
            import subprocess

            scp_cmd = [
                "scp",
                settings2_path,
                "{0}@{1}:{2}settings2.xml".format(remote_user, remote_ip, remote_path),
            ]
            log("Executing remote sync command: {0}".format(" ".join(scp_cmd)))

            result = subprocess.call(scp_cmd)

            if result == 0:
                log("Successfully synchronized settings2.xml to remote Paragon TV")
                if IN_KODI:
                    xbmcgui.Dialog().notification(
                        "Remote Sync", "Settings synchronized to secondary Paragon TV"
                    )
            else:
                log(
                    "Failed to synchronize with remote Paragon TV, return code: {0}".format(
                        result
                    )
                )

        except Exception as e:
            log("Error synchronizing with remote Paragon TV: {0}".format(str(e)))
            # Continue with the main function - remote sync is optional

        if IN_KODI:
            xbmcgui.Dialog().ok(
                "Success",
                "Configuration reloaded successfully!",
                "A backup of your previous settings was created.",
                "Restart PTV to see the changes.",
            )
        else:
            print("\nSuccess! Configuration reloaded successfully!")
            print("A backup of your previous settings was created.")
            print("Restart PTV to see the changes.")

        return True

    except Exception as e:
        log("Error reloading configurations: {0}".format(str(e)))
        import traceback

        log("Traceback: {0}".format(traceback.format_exc()))

        if IN_KODI:
            xbmcgui.Dialog().ok("Error", "Failed to reload configurations:", str(e))
        else:
            print("\nError: Failed to reload configurations: {0}".format(str(e)))

        return False


# If run as a standalone script
if __name__ == "__main__":
    reload_configurations()
