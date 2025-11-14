#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (C) 2025
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import sys
import traceback
from datetime import datetime, timedelta

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

# Get addon info
ADDON_ID = "script.pseudotv"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_VERSION = ADDON.getAddonInfo("version")
ADDON_USERDATA_PATH = xbmc.translatePath(ADDON.getAddonInfo("profile"))


# Log function
def log(msg, level=xbmc.LOGNOTICE):
    """Log message to Kodi log with proper formatting"""
    try:
        if isinstance(msg, unicode):
            msg = msg.encode("utf-8")
    except NameError:
        # Python 3 case - unicode is undefined
        pass

    message = "[{}] {}".format(ADDON_NAME, msg)
    xbmc.log(message, level)


# Dialog helpers
def infoDialog(message, heading=ADDON_NAME, icon="", time=5000, sound=False):
    """Show a notification dialog"""
    if icon == "":
        icon = xbmcgui.NOTIFICATION_INFO
    xbmcgui.Dialog().notification(heading, message, icon, time, sound)


def yesnoDialog(
    line1, line2="", line3="", heading=ADDON_NAME, nolabel="No", yeslabel="Yes"
):
    """Show a Yes/No dialog"""
    return xbmcgui.Dialog().yesno(heading, line1, line2, line3, nolabel, yeslabel)


# Create scheduler class
class PSTVScheduler:
    def __init__(self):
        self.enabled = ADDON.getSetting("EnableScheduler") == "true"
        self.schedule_type = int(ADDON.getSetting("ScheduleDays"))
        self.custom_days = ADDON.getSetting("CustomDays").split(",")
        self.schedule_time = ADDON.getSetting("ScheduleTime")

        # Convert custom days to integers
        try:
            self.custom_days = [
                int(day.strip()) for day in self.custom_days if day.strip().isdigit()
            ]
        except:
            log("Error parsing custom days - defaulting to weekdays", xbmc.LOGERROR)
            self.custom_days = [1, 2, 3, 4, 5]  # Default to weekdays

        log("PSTVScheduler initialized - Enabled: {}".format(self.enabled))
        log("Schedule Type: {}".format(self.schedule_type))
        log("Custom Days: {}".format(self.custom_days))
        log("Schedule Time: {}".format(self.schedule_time))

    def get_days_of_week(self):
        """Return list of days (1-7) when PSTV should launch based on settings"""
        if self.schedule_type == 0:  # Every day
            return [1, 2, 3, 4, 5, 6, 7]
        elif self.schedule_type == 1:  # Weekdays
            return [1, 2, 3, 4, 5]
        elif self.schedule_type == 2:  # Weekends
            return [6, 7]
        elif self.schedule_type == 3:  # Custom
            return self.custom_days
        return []

    def setup_task(self):
        """Set up the scheduled task based on platform"""
        if not self.enabled:
            log("Scheduler is disabled - not setting up task")
            return False

        # Get days and time
        days = self.get_days_of_week()
        if not days:
            log("No valid days selected", xbmc.LOGERROR)
            return False

        # Parse time
        try:
            hour, minute = self.schedule_time.split(":")
            hour = int(hour)
            minute = int(minute)
        except:
            log("Error parsing time: {}".format(self.schedule_time), xbmc.LOGERROR)
            return False

        log("Setting up scheduled task for days {} at {}:{}".format(days, hour, minute))

        # Detect platform
        platform = sys.platform.lower()

        if xbmc.getCondVisibility("System.Platform.Windows"):
            return self._setup_windows_task(days, hour, minute)
        elif xbmc.getCondVisibility("System.Platform.Linux"):
            return self._setup_linux_task(days, hour, minute)
        elif xbmc.getCondVisibility("System.Platform.OSX") or xbmc.getCondVisibility(
            "System.Platform.Darwin"
        ):
            return self._setup_osx_task(days, hour, minute)
        else:
            log("Unsupported platform: {}".format(platform), xbmc.LOGERROR)
            infoDialog("Scheduler not supported on this platform")
            return False

    def _setup_windows_task(self, days, hour, minute):
        """Set up Windows Task Scheduler task"""
        try:
            import subprocess

            # Build day of week string for schtasks
            dow_map = {
                1: "MON",
                2: "TUE",
                3: "WED",
                4: "THU",
                5: "FRI",
                6: "SAT",
                7: "SUN",
            }
            dow_str = ",".join([dow_map[d] for d in days if d in dow_map])

            # Get Kodi executable path
            kodi_exe = xbmc.translatePath("special://xbmc/")
            if kodi_exe.endswith("\\"):
                kodi_exe = kodi_exe[:-1]
            if not os.path.exists(kodi_exe):
                kodi_exe = os.path.join(kodi_exe, "kodi.exe")
            if not os.path.exists(kodi_exe):
                kodi_exe = os.path.join(kodi_exe, "Kodi.exe")

            if not os.path.exists(kodi_exe):
                log(
                    "Could not find Kodi executable at: {}".format(kodi_exe),
                    xbmc.LOGERROR,
                )
                infoDialog("Could not find Kodi executable path")
                return False

            log("Using Kodi executable: {}".format(kodi_exe))

            # Build PSTV startup command
            # Using RunScript builtin to launch PSTV
            kodi_args = '-u "RunScript(script.pseudotv)"'

            # Create batch file with the launch command
            batch_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.bat")
            batch_content = '@echo off\r\n"{}" {}'.format(kodi_exe, kodi_args)

            with open(batch_path, "w") as f:
                f.write(batch_content)

            log("Created launcher batch file: {}".format(batch_path))

            # Create/update the task
            task_name = "PSTV_AutoLaunch"

            # Delete existing task if present
            del_cmd = 'schtasks /Delete /TN "{}" /F'.format(task_name)
            try:
                subprocess.call(del_cmd, shell=True)
            except:
                pass  # Ignore errors if task doesn't exist

            # Create new task
            cmd = 'schtasks /Create /SC WEEKLY /D "{}" /TN "{}" /TR "{}" /ST {:02d}:{:02d} /F'.format(
                dow_str, task_name, batch_path, hour, minute
            )

            log("Running command: {}".format(cmd))
            result = subprocess.call(cmd, shell=True)

            if result == 0:
                log("Successfully created Windows scheduled task")
                infoDialog("PSTV schedule created successfully")
                return True
            else:
                log(
                    "Failed to create Windows scheduled task. Return code: {}".format(
                        result
                    ),
                    xbmc.LOGERROR,
                )
                infoDialog("Failed to create scheduled task. Check log.")
                return False

        except Exception as e:
            log("Error setting up Windows task: {}".format(e), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)
            infoDialog("Error creating Windows task: {}".format(str(e)))
            return False

    def _setup_linux_task(self, days, hour, minute):
        """Set up Linux crontab entry"""
        try:
            import subprocess

            # Build day of week string for crontab (0-6, where 0 is Sunday)
            # Convert our 1-7 (Mon-Sun) to 1-7 (Mon-Sun) needed for crontab
            # Note: crontab can use both 0 and 7 for Sunday
            cron_days = []
            for d in days:
                if d == 7:  # Convert Sunday to 0
                    cron_days.append(0)
                else:
                    cron_days.append(d)

            dow_str = ",".join([str(d) for d in cron_days])

            # Get Kodi executable path - might be kodi, kodi-standalone, etc.
            kodi_exe = "kodi"  # Default

            # Create a launcher script
            launcher_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.sh")

            # Get user's home directory
            home_dir = os.path.expanduser("~")

            launcher_content = "#!/bin/bash\n\n"
            launcher_content += "export DISPLAY=:0\n"  # For GUI applications
            launcher_content += '{}  --action="RunScript(script.pseudotv)"\n'.format(
                kodi_exe
            )

            # Write and make executable
            with open(launcher_path, "w") as f:
                f.write(launcher_content)

            os.chmod(launcher_path, 0o755)  # Make executable

            log("Created launcher script: {}".format(launcher_path))

            # Create temporary file for crontab modification
            cron_file = os.path.join(ADDON_USERDATA_PATH, "pstv_crontab.txt")

            # Get existing crontab
            subprocess.call(
                'crontab -l > "{}" 2>/dev/null'.format(cron_file), shell=True
            )

            # Read existing crontab
            with open(cron_file, "r") as f:
                cron_content = f.read()

            # Remove any existing PSTV entries
            new_lines = []
            for line in cron_content.splitlines():
                if "launch_pstv.sh" not in line and "PSTV_SCHEDULE" not in line:
                    new_lines.append(line)

            # Add our new entry
            new_lines.append("# PSTV_SCHEDULE")
            new_lines.append(
                "{} {} * * {} {}".format(minute, hour, dow_str, launcher_path)
            )

            # Write new crontab file
            with open(cron_file, "w") as f:
                f.write("\n".join(new_lines) + "\n")

            # Install new crontab
            result = subprocess.call('crontab "{}"'.format(cron_file), shell=True)

            # Clean up
            try:
                os.remove(cron_file)
            except:
                pass

            if result == 0:
                log("Successfully created Linux crontab entry")
                infoDialog("PSTV schedule created successfully")
                return True
            else:
                log(
                    "Failed to create Linux crontab entry. Return code: {}".format(
                        result
                    ),
                    xbmc.LOGERROR,
                )
                infoDialog("Failed to create schedule. Check log.")
                return False

        except Exception as e:
            log("Error setting up Linux task: {}".format(e), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)
            infoDialog("Error creating Linux crontab: {}".format(str(e)))
            return False

    def _setup_osx_task(self, days, hour, minute):
        """Set up macOS launchd plist"""
        try:
            import subprocess

            # Get weekday numbers for launchd (1-7, Mon-Sun)
            # LaunchAgent uses same numbering as our internal system

            # LaunchAgent plist file path
            plist_dir = os.path.expanduser("~/Library/LaunchAgents")
            if not os.path.exists(plist_dir):
                os.makedirs(plist_dir)

            plist_path = os.path.join(plist_dir, "com.pstv.autolaunch.plist")

            # Get Kodi executable path
            kodi_exe = "/Applications/Kodi.app/Contents/MacOS/Kodi"
            if not os.path.exists(kodi_exe):
                log(
                    "Could not find Kodi executable at: {}".format(kodi_exe),
                    xbmc.LOGERROR,
                )
                infoDialog("Could not find Kodi executable path")
                return False

            # Create a launcher script
            launcher_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.sh")

            launcher_content = "#!/bin/bash\n\n"
            launcher_content += "sleep 5\n"  # Give system time
            launcher_content += '"{}" --action="RunScript(script.pseudotv)"\n'.format(
                kodi_exe
            )

            # Write and make executable
            with open(launcher_path, "w") as f:
                f.write(launcher_content)

            os.chmod(launcher_path, 0o755)  # Make executable

            log("Created launcher script: {}".format(launcher_path))

            # Create plist XML content
            plist_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            plist_content += '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
            plist_content += '<plist version="1.0">\n'
            plist_content += "<dict>\n"
            plist_content += "    <key>Label</key>\n"
            plist_content += "    <string>com.pstv.autolaunch</string>\n"
            plist_content += "    <key>ProgramArguments</key>\n"
            plist_content += "    <array>\n"
            plist_content += "        <string>{}</string>\n".format(launcher_path)
            plist_content += "    </array>\n"
            plist_content += "    <key>StartCalendarInterval</key>\n"
            plist_content += "    <array>\n"

            # Add entry for each day
            for day in days:
                plist_content += "        <dict>\n"
                plist_content += "            <key>Hour</key>\n"
                plist_content += "            <integer>{}</integer>\n".format(hour)
                plist_content += "            <key>Minute</key>\n"
                plist_content += "            <integer>{}</integer>\n".format(minute)
                plist_content += "            <key>Weekday</key>\n"
                plist_content += "            <integer>{}</integer>\n".format(day)
                plist_content += "        </dict>\n"

            plist_content += "    </array>\n"
            plist_content += "    <key>RunAtLoad</key>\n"
            plist_content += "    <false/>\n"
            plist_content += "</dict>\n"
            plist_content += "</plist>\n"

            # Write plist file
            with open(plist_path, "w") as f:
                f.write(plist_content)

            log("Created plist file: {}".format(plist_path))

            # Unload existing plist if it exists
            subprocess.call(
                'launchctl unload "{}" 2>/dev/null'.format(plist_path), shell=True
            )

            # Load the plist
            result = subprocess.call(
                'launchctl load "{}"'.format(plist_path), shell=True
            )

            if result == 0:
                log("Successfully created macOS LaunchAgent")
                infoDialog("PSTV schedule created successfully")
                return True
            else:
                log(
                    "Failed to create macOS LaunchAgent. Return code: {}".format(
                        result
                    ),
                    xbmc.LOGERROR,
                )
                infoDialog("Failed to create schedule. Check log.")
                return False

        except Exception as e:
            log("Error setting up macOS task: {}".format(e), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)
            infoDialog("Error creating macOS LaunchAgent: {}".format(str(e)))
            return False

    def clear_tasks(self):
        """Remove all scheduled tasks"""
        log("Clearing all scheduled tasks")

        try:
            platform = sys.platform.lower()

            if xbmc.getCondVisibility("System.Platform.Windows"):
                import subprocess

                task_name = "PSTV_AutoLaunch"
                subprocess.call(
                    'schtasks /Delete /TN "{}" /F'.format(task_name), shell=True
                )

                # Also clean up batch file
                batch_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.bat")
                if os.path.exists(batch_path):
                    os.remove(batch_path)

            elif xbmc.getCondVisibility("System.Platform.Linux"):
                import subprocess

                # Clean up launcher script
                launcher_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.sh")
                if os.path.exists(launcher_path):
                    os.remove(launcher_path)

                # Create temporary file for crontab modification
                cron_file = os.path.join(ADDON_USERDATA_PATH, "pstv_crontab.txt")

                # Get existing crontab
                subprocess.call(
                    'crontab -l > "{}" 2>/dev/null'.format(cron_file), shell=True
                )

                # Read existing crontab
                with open(cron_file, "r") as f:
                    cron_content = f.read()

                # Remove any existing PSTV entries
                new_lines = []
                for line in cron_content.splitlines():
                    if "launch_pstv.sh" not in line and "PSTV_SCHEDULE" not in line:
                        new_lines.append(line)

                # Write new crontab file
                with open(cron_file, "w") as f:
                    f.write("\n".join(new_lines) + "\n")

                # Install new crontab
                subprocess.call('crontab "{}"'.format(cron_file), shell=True)

                # Clean up
                try:
                    os.remove(cron_file)
                except:
                    pass

            elif xbmc.getCondVisibility(
                "System.Platform.OSX"
            ) or xbmc.getCondVisibility("System.Platform.Darwin"):
                import subprocess

                # LaunchAgent plist file path
                plist_path = os.path.expanduser(
                    "~/Library/LaunchAgents/com.pstv.autolaunch.plist"
                )

                # Unload plist if it exists
                if os.path.exists(plist_path):
                    subprocess.call(
                        'launchctl unload "{}"'.format(plist_path), shell=True
                    )
                    os.remove(plist_path)

                # Clean up launcher script
                launcher_path = os.path.join(ADDON_USERDATA_PATH, "launch_pstv.sh")
                if os.path.exists(launcher_path):
                    os.remove(launcher_path)

            infoDialog("Successfully cleared all schedules")
            return True

        except Exception as e:
            log("Error clearing tasks: {}".format(e), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)
            infoDialog("Error clearing schedules: {}".format(str(e)))
            return False


# Main execution
if __name__ == "__main__":
    log("PSTV Scheduler starting...")

    # Parse command-line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1]

        scheduler = PSTVScheduler()

        if action == "setup":
            scheduler.setup_task()
        elif action == "clear":
            scheduler.clear_tasks()
        else:
            log("Unknown command: {}".format(action), xbmc.LOGERROR)
            infoDialog("Unknown scheduler command")
    else:
        log("No command specified", xbmc.LOGERROR)
        infoDialog("No scheduler command specified")
