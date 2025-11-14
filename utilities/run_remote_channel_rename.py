#!/usr/bin/env python
# Try to import Kodi modules, but provide fallbacks for CLI usage
try:
    import xbmc
    import xbmcgui

    IN_KODI = True
except ImportError:
    IN_KODI = False

    # Define fallback functions for CLI usage
    class xbmc:
        LOGINFO = 1
        LOGERROR = 3

        @staticmethod
        def log(msg, level=1):
            print(msg)

        @staticmethod
        def sleep(ms):
            import time

            time.sleep(ms / 1000.0)

    class xbmcgui:
        NOTIFICATION_INFO = "INFO"

        class Dialog:
            @staticmethod
            def ok(*args):
                print(" ".join(str(arg) for arg in args[1:]))

            @staticmethod
            def notification(heading, message, icon):
                print(heading + ": " + message)

        class DialogProgress:
            def __init__(self):
                self.canceled = False

            def create(self, heading, message=""):
                print(heading + ": " + message)

            def update(self, percent, message=""):
                print(str(percent) + "% - " + message)

            def iscanceled(self):
                return self.canceled

            def close(self):
                print("Progress completed")


import os
import subprocess


def run_remote_channel_rename():
    # Show a progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create("PTV Channel Image Renaming", "Connecting to remote Paragon TV...")

    # Remote Paragon TV details
    remote_ip = "10.0.0.91"  # Updated to match your other scripts
    remote_user = "root"  # Default LibreELEC username
    remote_script_path = "/storage/.kodi/addons/script.remoteartwork/resources/media/flags/numbers/rename_channel_images.py"

    try:
        # Log the operation
        xbmc.log(
            "PTV Remote Channel Rename: Starting remote operation", level=xbmc.LOGINFO
        )

        # Make sure the script is executable on the remote system
        chmod_cmd = [
            "ssh",
            remote_user + "@" + remote_ip,
            "chmod +x " + remote_script_path,
        ]
        xbmc.log(
            "PTV Remote Channel Rename: Setting execute permissions", level=xbmc.LOGINFO
        )
        subprocess.call(chmod_cmd)

        progress.update(30, "Connected. Running remote script...")

        # Run the script on the remote system
        ssh_cmd = ["ssh", remote_user + "@" + remote_ip, "python " + remote_script_path]
        xbmc.log(
            "PTV Remote Channel Rename: Executing remote script", level=xbmc.LOGINFO
        )
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        # Read output line by line to update progress
        line_count = 0
        for line in process.stdout:
            line_count += 1
            progress.update(30 + min(60, line_count), "Processing: " + line.strip())
            xbmc.log("PTV Remote script: " + line.strip(), level=xbmc.LOGINFO)

            # Check if the user cancelled
            if progress.iscanceled():
                process.terminate()
                progress.close()
                xbmcgui.Dialog().notification(
                    "PTV Channel Rename",
                    "Operation cancelled by user",
                    xbmcgui.NOTIFICATION_INFO,
                )
                xbmc.log(
                    "PTV Remote Channel Rename: Cancelled by user", level=xbmc.LOGINFO
                )
                return

        # Wait for the process to complete
        returncode = process.wait()

        progress.update(100, "Complete!")
        xbmc.sleep(1000)  # Short pause to show completion
        progress.close()

        if returncode == 0:
            xbmcgui.Dialog().notification(
                "PTV Channel Rename",
                "Channel images renamed successfully!",
                xbmcgui.NOTIFICATION_INFO,
            )
            xbmc.log(
                "PTV Remote Channel Rename: Completed successfully", level=xbmc.LOGINFO
            )
        else:
            stderr = process.stderr.read()
            xbmc.log("PTV Remote Channel Rename Error: " + stderr, level=xbmc.LOGERROR)
            xbmcgui.Dialog().ok(
                "Error",
                "Failed to rename channel images on remote PTV.",
                "Error: " + stderr,
            )

    except Exception as e:
        progress.close()
        xbmc.log("PTV Remote Channel Rename Error: " + str(e), level=xbmc.LOGERROR)
        xbmcgui.Dialog().ok("Error", "Failed to run remote script:", str(e))


# If run as a standalone script
if __name__ == "__main__":
    # Add header when running standalone
    if not IN_KODI:
        print("=" * 50)
        print("PTV Remote Channel Image Rename Tool")
        print("=" * 50)
        print("This script connects to a remote Paragon TV system")
        print("and renames channel image files.")
        print("=" * 50 + "\n")

    run_remote_channel_rename()

    if not IN_KODI:
        print("\nOperation completed.")
