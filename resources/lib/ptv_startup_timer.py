#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# PTV Startup Timer - Standalone startup timer for Paragon TV
#

import os
import time
import traceback
from datetime import datetime

import xbmc
import xbmcaddon
import xbmcgui

# Get addon info
ADDON_ID = "script.paragontv"
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")


def log(msg, level=xbmc.LOGNOTICE):
    message = "[PTV Startup Timer] {}".format(msg)
    xbmc.log(message, level)


def notify(message, heading="PTV Scheduler", icon="", time=5000, sound=True):
    """Display a more visually appealing notification with custom icon"""

    # Use a specific icon for scheduler notifications
    if icon == "":
        # Custom scheduler icon (you'll need to create this file)
        icon = os.path.join(ADDON_PATH, "scheduler_icon.png")

        # Fallback to default icons if the custom one doesn't exist
        if not os.path.exists(icon):
            # Try common PTV icons
            icon = os.path.join(ADDON_PATH, "resources", "images", "icon.png")

        # Final fallback to Kodi's info icon
        if not os.path.exists(icon):
            icon = xbmcgui.NOTIFICATION_INFO

    # Display the notification with our custom icon
    xbmcgui.Dialog().notification(heading, message, icon, time, sound)


def get_startup_settings():
    """Read all startup settings from addon"""
    settings = []

    # Check each of the 10 startup schedulers
    for i in range(1, 11):
        enabled = ADDON.getSetting("EnableScheduler{}".format(i)) == "true"

        if enabled:
            setting = {
                "enabled": True,
                "label": ADDON.getSetting("ScheduleLabel{}".format(i)),
                "time": ADDON.getSetting("ScheduleTime{}".format(i)),
                "days_type": int(ADDON.getSetting("ScheduleDays{}".format(i))),
                "custom_days": ADDON.getSetting("CustomDays{}".format(i)).split(","),
                "start_channel": ADDON.getSetting("StartChannel{}".format(i)),
                "enable_start_channel": ADDON.getSetting(
                    "EnableStartChannel{}".format(i)
                )
                == "true",
                "volume_level": ADDON.getSetting("VolumeLevel{}".format(i)),
                "index": i,
            }
            settings.append(setting)

    # Add global settings
    global_settings = {"notification": True}  # Always show startup notifications

    return settings, global_settings


def check_day_match(settings, current_day_idx):
    """Check if today matches the days setting"""
    day_match = False

    if settings["days_type"] == 0:  # Every day
        day_match = True
    elif settings["days_type"] == 1 and current_day_idx < 5:  # Weekdays
        day_match = True
    elif settings["days_type"] == 2 and current_day_idx >= 5:  # Weekends
        day_match = True
    elif settings["days_type"] == 3:  # Custom days
        day_nums = [
            int(d.strip()) for d in settings["custom_days"] if d.strip().isdigit()
        ]
        day_indices = [d - 1 for d in day_nums if 1 <= d <= 7]  # Convert to 0-6
        day_match = current_day_idx in day_indices

    return day_match


def should_startup_now(settings):
    """Determine if it's time to start up based on settings and current time"""
    # Parse startup time
    hour, minute = settings["time"].split(":")
    hour = int(hour)
    minute = int(minute)

    # Get current time
    now = datetime.now()
    current_day_idx = now.weekday()  # 0=Monday, 6=Sunday

    # Convert to minutes since midnight for comparison
    current_minutes = now.hour * 60 + now.minute
    startup_minutes = hour * 60 + minute

    # Check if within the startup window (current time equals target time)
    # Only trigger at exact minute to prevent multiple triggers
    time_match = current_minutes == startup_minutes

    # Check if today matches the days setting
    day_match = check_day_match(settings, current_day_idx)

    # Log detailed info
    log("Checking schedule '{}'".format(settings["label"]), xbmc.LOGERROR)
    log("Current time: {}:{:02d}".format(now.hour, now.minute), xbmc.LOGERROR)
    log("Startup time: {}:{:02d}".format(hour, minute), xbmc.LOGERROR)
    log(
        "Minutes from midnight - Current: {}, Startup: {}".format(
            current_minutes, startup_minutes
        ),
        xbmc.LOGERROR,
    )
    log("Time match (exact minute): {}".format(time_match), xbmc.LOGERROR)
    log("Current day index: {}".format(current_day_idx), xbmc.LOGERROR)
    log("Day match: {}".format(day_match), xbmc.LOGERROR)

    # Return true if startup should trigger, along with details
    should_trigger = settings["enabled"] and time_match and day_match
    log("Startup should trigger: {}".format(should_trigger), xbmc.LOGERROR)
    return (
        should_trigger,
        hour,
        minute,
        settings["label"],
        settings["start_channel"],
        settings["enable_start_channel"],
        settings["volume_level"],
    )


def execute_startup(label, start_channel, enable_start_channel, volume_level):
    """Execute the startup - launch PTV with channel tuning"""
    log("EXECUTING STARTUP SEQUENCE FOR: {}".format(label), xbmc.LOGERROR)

    # Check if PTV is already running
    if xbmc.getCondVisibility("Window.IsActive(script-paragontv-TVOverlay.xml)"):
        log("PTV is already running", xbmc.LOGERROR)

        # If channel tuning is requested, just change the channel
        if enable_start_channel and start_channel and start_channel.strip():
            log(
                "PTV already running, just changing to channel {}".format(
                    start_channel
                ),
                xbmc.LOGERROR,
            )
            notify("Changing to channel {}".format(start_channel), "PTV Scheduler")
            xbmc.sleep(2000)

            # Send channel digits directly without waiting
            channel_num = start_channel.strip()
            for digit in channel_num:
                if digit == "0":
                    xbmc.executebuiltin("Action(Number0)")
                elif digit == "1":
                    xbmc.executebuiltin("Action(Number1)")
                elif digit == "2":
                    xbmc.executebuiltin("Action(Number2)")
                elif digit == "3":
                    xbmc.executebuiltin("Action(Number3)")
                elif digit == "4":
                    xbmc.executebuiltin("Action(Number4)")
                elif digit == "5":
                    xbmc.executebuiltin("Action(Number5)")
                elif digit == "6":
                    xbmc.executebuiltin("Action(Number6)")
                elif digit == "7":
                    xbmc.executebuiltin("Action(Number7)")
                elif digit == "8":
                    xbmc.executebuiltin("Action(Number8)")
                elif digit == "9":
                    xbmc.executebuiltin("Action(Number9)")

                log("Sent digit: {}".format(digit), xbmc.LOGERROR)
                xbmc.sleep(500)  # 0.5 seconds between digits

            # Press OK/Select to confirm
            xbmc.sleep(1000)
            log("Sending Select/OK to confirm channel", xbmc.LOGERROR)
            xbmc.executebuiltin("Action(Select)")
        else:
            notify("PTV is already running", "PTV Scheduler")

        return

    # Show notification
    _, global_settings = get_startup_settings()
    if global_settings["notification"]:
        notify("Launching PTV: " + label, "PTV Scheduler")

    # Wait a moment to ensure notification shows
    xbmc.sleep(2000)

    # Set volume if needed
    if volume_level:
        try:
            vol_percent = int(volume_level)
            xbmc.executebuiltin("SetVolume({})".format(vol_percent))
            log("Set volume to {}%".format(vol_percent), xbmc.LOGERROR)
        except Exception as e:
            log("Error setting volume: {}".format(e), xbmc.LOGERROR)

    # Launch PTV first
    try:
        # Launch PTV without parameters
        command = "RunScript(script.paragontv)"
        log("Executing: {}".format(command), xbmc.LOGERROR)
        xbmc.executebuiltin(command)

        # Check if ForceChannelReset is enabled or if we're in preset rebuild mode
        force_reset = ADDON.getSetting("ForceChannelReset")
        preset_rebuild = ADDON.getSetting("PresetRebuildMode")

        if force_reset == "true" or preset_rebuild == "true":
            log("Channel rebuild in progress - skipping channel tuning", xbmc.LOGERROR)
            if global_settings["notification"]:
                notify("Channel rebuild in progress", "PTV Scheduler")
            # Still wait for PTV to initialize
            log(
                "Waiting 30 seconds for PTV to complete channel rebuild...",
                xbmc.LOGERROR,
            )
            xbmc.sleep(30000)
        else:
            # Check for temporary start channel from preset system
            temp_channel = ADDON.getSetting("TempStartChannel")
            if temp_channel and temp_channel.isdigit():
                start_channel = temp_channel
                enable_start_channel = True
                # Clear the temporary channel
                ADDON.setSetting("TempStartChannel", "")
                log(
                    "Using temporary start channel from preset: {}".format(
                        start_channel
                    ),
                    xbmc.LOGERROR,
                )

            # Channel tuning only if a specific channel is requested AND enable_start_channel is True
            if start_channel and start_channel.strip() and enable_start_channel:
                channel_num = start_channel.strip()
                log(
                    "Will attempt to tune to channel: {}".format(channel_num),
                    xbmc.LOGERROR,
                )

                # Step 1: Wait for PTV to fully initialize (reduced for PTV)
                log("Waiting 15 seconds for PTV to fully initialize...", xbmc.LOGERROR)
                xbmc.sleep(15000)  # 15 seconds for simpler PTV

                # Step 2: Ensure stable playback before changing channels
                log("Ensuring PTV is stable before changing channels...", xbmc.LOGERROR)
                xbmc.sleep(3000)  # Extra 3 seconds of stability

                # Step 3: Send the channel digits with pauses between them
                log("Sending channel digits for: {}".format(channel_num), xbmc.LOGERROR)
                for digit in channel_num:
                    if digit == "0":
                        xbmc.executebuiltin("Action(Number0)")
                    elif digit == "1":
                        xbmc.executebuiltin("Action(Number1)")
                    elif digit == "2":
                        xbmc.executebuiltin("Action(Number2)")
                    elif digit == "3":
                        xbmc.executebuiltin("Action(Number3)")
                    elif digit == "4":
                        xbmc.executebuiltin("Action(Number4)")
                    elif digit == "5":
                        xbmc.executebuiltin("Action(Number5)")
                    elif digit == "6":
                        xbmc.executebuiltin("Action(Number6)")
                    elif digit == "7":
                        xbmc.executebuiltin("Action(Number7)")
                    elif digit == "8":
                        xbmc.executebuiltin("Action(Number8)")
                    elif digit == "9":
                        xbmc.executebuiltin("Action(Number9)")

                    log("Sent digit: {}".format(digit), xbmc.LOGERROR)
                    xbmc.sleep(1000)  # 1 second between digits (reduced from 2)

                # Step 4: Wait a moment after entering digits
                log(
                    "Waiting for channel number entry to be processed...", xbmc.LOGERROR
                )
                xbmc.sleep(2000)  # 2 seconds (reduced from 3)

                # Step 5: Press OK/Select to confirm channel change
                log("Sending Select/OK to confirm channel", xbmc.LOGERROR)
                xbmc.executebuiltin("Action(Select)")

                # Step 6: Wait for channel change to complete
                log("Waiting for channel change to complete...", xbmc.LOGERROR)
                xbmc.sleep(5000)  # 5 seconds (reduced from 10)

                log(
                    "Channel tuning sequence completed for channel: {}".format(
                        channel_num
                    ),
                    xbmc.LOGERROR,
                )
            else:
                if not enable_start_channel:
                    log(
                        "Start Channel is disabled for this schedule, using PTV default",
                        xbmc.LOGERROR,
                    )
                else:
                    log(
                        "No specific channel requested, using PTV default",
                        xbmc.LOGERROR,
                    )

        log("PTV startup sequence completed", xbmc.LOGERROR)
    except Exception as e:
        log("Error in PTV startup sequence: {}".format(e), xbmc.LOGERROR)
        log(traceback.format_exc(), xbmc.LOGERROR)


def main():
    """Main function - runs the startup timer"""
    log("Starting PTV Startup Timer", xbmc.LOGERROR)

    # Show startup notification
    notify("Startup scheduling service started", "PTV Scheduler")

    # Variables to track state - we'll track the last triggered times with cooldown
    # Format: {schedule_id: last_trigger_time}
    last_triggered = {}
    cooldown_minutes = 2  # 2 minute cooldown period

    # Main loop
    while not xbmc.abortRequested:
        try:
            # Get current time
            now = datetime.now()

            # Get fresh settings
            startup_settings, _ = get_startup_settings()

            # Check all enabled startup schedulers
            for settings in startup_settings:
                # Check if this scheduler should trigger startup
                (
                    should_trigger,
                    hour,
                    minute,
                    label,
                    start_channel,
                    enable_start_channel,
                    volume_level,
                ) = should_startup_now(settings)

                if should_trigger:
                    schedule_id = settings["index"]

                    # Check cooldown
                    if schedule_id in last_triggered:
                        time_since_last = (
                            now - last_triggered[schedule_id]
                        ).total_seconds()
                        if time_since_last < (cooldown_minutes * 60):
                            log(
                                "Schedule {} still in cooldown period ({:.1f} seconds remaining)".format(
                                    schedule_id,
                                    (cooldown_minutes * 60) - time_since_last,
                                ),
                                xbmc.LOGERROR,
                            )
                            continue

                    log(
                        "Triggering startup for {} (Schedule {})".format(
                            label, schedule_id
                        ),
                        xbmc.LOGERROR,
                    )
                    execute_startup(
                        label, start_channel, enable_start_channel, volume_level
                    )

                    # Update last triggered time for this schedule
                    last_triggered[schedule_id] = now

        except Exception as e:
            log("Error in startup timer: {}".format(e), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)

        # Sleep for a short time before checking again (10 seconds)
        xbmc.sleep(10000)

    log("Startup timer ended")


# Run the timer
if __name__ == "__main__":
    main()
