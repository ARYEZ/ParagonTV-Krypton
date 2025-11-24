#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# PTV Maintenance Timer - Standalone maintenance timer for Paragon TV
# Supports multiple independent maintenance schedules
#

import os
import time
from datetime import datetime, timedelta

import xbmc
import xbmcaddon
import xbmcgui

# Get addon info
ADDON_ID = "script.paragontv"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")


def log(msg, level=xbmc.LOGNOTICE):
    message = "[PTV Maintenance Timer] {}".format(msg)
    xbmc.log(message, level)


def notify(message, heading="PTV Maintenance", icon="", time=5000, sound=True):
    """Display a notification with custom icon"""

    # Use a specific icon for maintenance notifications
    if icon == "":
        # First try to use the maintenance icon
        maintenance_icon = os.path.join(
            ADDON_PATH, "resources", "images", "Maintenance.png"
        )
        if os.path.exists(maintenance_icon):
            icon = maintenance_icon
        else:
            # Fallback to regular PTV icon
            icon = os.path.join(ADDON_PATH, "resources", "images", "icon.png")

            # Final fallback to Kodi's info icon
            if not os.path.exists(icon):
                icon = xbmcgui.NOTIFICATION_INFO

    # Display the notification with our custom icon
    xbmcgui.Dialog().notification(heading, message, icon, time, sound)


def get_maintenance_settings_by_schedule(schedule_id):
    """Read maintenance settings for a specific schedule from addon"""

    enabled = (
        ADDON.getSetting("EnableMaintenanceScheduler{}".format(schedule_id)) == "true"
    )

    if not enabled:
        return None, {}

    settings = {
        "schedule_id": schedule_id,
        "enabled": True,
        "label": ADDON.getSetting("MaintenanceLabel{}".format(schedule_id)),
        "time": ADDON.getSetting("MaintenanceTime{}".format(schedule_id)),
        "days_type": int(ADDON.getSetting("MaintenanceDays{}".format(schedule_id))),
        "weekday": int(
            ADDON.getSetting("MaintenanceWeekday{}".format(schedule_id)) or "0"
        ),
        "day_of_month": int(
            ADDON.getSetting("MaintenanceDayOfMonth{}".format(schedule_id)) or "1"
        ),
        "custom_days": (
            ADDON.getSetting("MaintenanceCustomDays{}".format(schedule_id)).split(",")
            if ADDON.getSetting("MaintenanceCustomDays{}".format(schedule_id))
            else []
        ),
        "tasks": {
            "video_library": ADDON.getSetting(
                "MaintenanceVideoLibrary{}".format(schedule_id)
            )
            == "true",
            "clean_video": ADDON.getSetting(
                "MaintenanceCleanVideo{}".format(schedule_id)
            )
            == "true",
            "music_library": ADDON.getSetting(
                "MaintenanceMusicLibrary{}".format(schedule_id)
            )
            == "true",
            "clean_music": ADDON.getSetting(
                "MaintenanceCleanMusic{}".format(schedule_id)
            )
            == "true",
            "force_reset": ADDON.getSetting(
                "MaintenanceForceReset{}".format(schedule_id)
            )
            == "true",
            "organize_channels": ADDON.getSetting(
                "MaintenanceOrganizeChannels{}".format(schedule_id)
            )
            == "true",
            "reload_config": ADDON.getSetting(
                "MaintenanceReloadConfig{}".format(schedule_id)
            )
            == "true",
        },
    }

    # Global settings
    global_settings = {
        "notification": ADDON.getSetting("MaintenanceNotification") == "true",
        "last_run": ADDON.getSetting("LastMaintenanceRun{}".format(schedule_id)),
        "time_window": int(ADDON.getSetting("MaintenanceTimeWindow") or "5")
        * 2,  # Convert to total window
    }

    return settings, global_settings


def get_all_maintenance_settings():
    """Get all maintenance schedules"""
    schedules = []

    for i in range(1, 11):  # Check schedules 1-10
        settings, global_settings = get_maintenance_settings_by_schedule(i)
        if settings:
            schedules.append((settings, global_settings))

    return schedules


def check_day_match(settings):
    """Check if today matches the days setting"""
    now = datetime.now()
    current_day_idx = now.weekday()  # 0=Monday, 6=Sunday
    day_match = False

    if settings["days_type"] == 0:  # Every day
        day_match = True
    elif settings["days_type"] == 1:  # Weekdays
        day_match = current_day_idx < 5
    elif settings["days_type"] == 2:  # Weekends
        day_match = current_day_idx >= 5
    elif settings["days_type"] == 3:  # Weekly
        day_match = current_day_idx == settings["weekday"]
    elif settings["days_type"] == 4:  # Monthly
        day_match = now.day == settings["day_of_month"]
    elif settings["days_type"] == 5:  # Custom days
        # Convert weekday to 1-7 format (Monday=1, Sunday=7)
        current_day_num = str(current_day_idx + 1)
        day_match = current_day_num in settings["custom_days"]

    return day_match


def should_run_maintenance(settings, global_settings):
    """Determine if it's time to run maintenance based on settings and current time"""
    # Parse maintenance time
    hour, minute = settings["time"].split(":")
    hour = int(hour)
    minute = int(minute)

    # Get current time
    now = datetime.now()

    # Create scheduled time for today
    scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Create time window
    window_minutes = global_settings.get("time_window", 10) / 2
    window_start = scheduled_time - timedelta(minutes=window_minutes)
    window_end = scheduled_time + timedelta(minutes=window_minutes)

    # Check if we're within the window
    time_match = window_start <= now <= window_end

    # Check if today matches the days setting
    day_match = check_day_match(settings)

    # Check cooldown (don't run if we've run in the last 10 minutes)
    cooldown_ok = True
    last_run_str = global_settings.get("last_run", "Never")
    if last_run_str and last_run_str != "Never":
        try:
            last_run_time = datetime.strptime(last_run_str, "%Y-%m-%d %H:%M:%S")
            time_since_last = (now - last_run_time).total_seconds()
            cooldown_ok = time_since_last >= 600  # 10 minute cooldown
        except Exception as e:
            pass

    # Log detailed info
    log(
        "Checking maintenance schedule '{}' (ID: {})".format(
            settings["label"], settings["schedule_id"]
        )
    )
    log("Current time: {}:{:02d}".format(now.hour, now.minute))
    log(
        "Scheduled time: {}:{:02d} (window: {}:{:02d} - {}:{:02d})".format(
            hour,
            minute,
            window_start.hour,
            window_start.minute,
            window_end.hour,
            window_end.minute,
        )
    )
    log("Time match (within window): {}".format(time_match))
    log("Day match: {}".format(day_match))
    log("Cooldown OK: {} (last run: {})".format(cooldown_ok, last_run_str))

    # Return true if maintenance should run
    should_trigger = settings["enabled"] and time_match and day_match and cooldown_ok
    log("Maintenance should trigger: {}".format(should_trigger))
    return should_trigger, settings["label"], settings["tasks"]


def execute_maintenance(label, tasks, schedule_id):
    """Execute the maintenance action script for a specific schedule"""
    log(
        "EXECUTING MAINTENANCE SEQUENCE FOR: {} (Schedule {})".format(
            label, schedule_id
        ),
        xbmc.LOGERROR,
    )

    # Show notification
    _, global_settings = get_maintenance_settings_by_schedule(schedule_id)
    if global_settings["notification"]:
        notify("Starting maintenance: " + label, "PTV Maintenance")

    # Execute the maintenance action script with schedule ID
    # FIXED PATH: Changed from 'schedulers' to 'resources/lib'
    maintenance_script = os.path.join(
        ADDON_PATH, "resources", "lib", "ptv_maintenance_action.py"
    )
    log(
        "Executing maintenance script: {} with schedule ID: {}".format(
            maintenance_script, schedule_id
        ),
        xbmc.LOGERROR,
    )

    # Log which tasks are enabled
    for task, enabled in tasks.items():
        log("Task {}: {}".format(task, "ENABLED" if enabled else "DISABLED"))

    # Execute the script with schedule ID as parameter
    xbmc.executebuiltin('RunScript("{}", {})'.format(maintenance_script, schedule_id))

    # Log completion
    log(
        "Maintenance script execution request sent for schedule {}".format(schedule_id),
        xbmc.LOGERROR,
    )


def main():
    """Main function - runs the maintenance timer"""
    log("Starting PTV Maintenance Timer", xbmc.LOGERROR)

    # Show startup notification
    notify("Maintenance scheduling service started", "PTV Maintenance")

    # Variables to track state
    last_triggered = {}

    # Main loop
    while not xbmc.abortRequested:
        try:
            # Get current time and date
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")

            # Initialize tracking for today if not exists
            if current_date not in last_triggered:
                last_triggered = {current_date: {}}

            # Get all maintenance schedules
            all_schedules = get_all_maintenance_settings()

            # Check each schedule
            for settings, global_settings in all_schedules:
                # Check if maintenance should run
                should_trigger, label, tasks = should_run_maintenance(
                    settings, global_settings
                )

                if should_trigger:
                    # Create a unique key for this schedule and time
                    schedule_key = "schedule{}_{}_{}".format(
                        settings["schedule_id"], settings["time"], settings["days_type"]
                    )

                    # Check if we've already triggered this schedule today
                    if schedule_key not in last_triggered[current_date]:
                        log(
                            "Triggering maintenance for {} (Schedule {}) at {}".format(
                                label, settings["schedule_id"], settings["time"]
                            ),
                            xbmc.LOGERROR,
                        )
                        execute_maintenance(label, tasks, settings["schedule_id"])

                        # Mark that we've triggered this schedule today
                        last_triggered[current_date][schedule_key] = True

                        # Update last run time for this schedule
                        ADDON.setSetting(
                            "LastMaintenanceRun{}".format(settings["schedule_id"]),
                            now.strftime("%Y-%m-%d %H:%M:%S"),
                        )
                    else:
                        log(
                            "Already triggered maintenance for {} today".format(
                                schedule_key
                            )
                        )

        except Exception as e:
            log("Error in maintenance timer: {}".format(e), xbmc.LOGERROR)

        # Sleep for 30 seconds before checking again
        xbmc.sleep(30000)

    log("Maintenance timer ended")


# Run the timer
if __name__ == "__main__":
    main()
