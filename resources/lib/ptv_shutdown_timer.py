#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# PTV Shutdown Timer - Standalone shutdown timer for Paragon TV
#

import xbmc
import xbmcaddon
import xbmcgui
from datetime import datetime
import time
import os

# Get addon info
ADDON_ID = 'script.paragontv'
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_NAME = ADDON.getAddonInfo('name')

def log(msg, level=xbmc.LOGNOTICE):
    message = '[PTV Shutdown Timer] {}'.format(msg)
    xbmc.log(message, level)

def notify(message, heading="PTV Scheduler", icon='', time=5000, sound=True):
    """Display a more visually appealing notification with custom icon"""
    
    # Use a specific icon for scheduler notifications
    if icon == '':
        # Custom scheduler icon
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

def get_shutdown_settings():
    """Read all shutdown settings from addon"""
    settings = []
    
    # Check each of the 10 shutdown schedulers
    for i in range(1, 11):
        enabled = ADDON.getSetting('EnableShutdownScheduler{}'.format(i)) == 'true'
        
        if enabled:
            setting = {
                'enabled': True,
                'label': ADDON.getSetting('ShutdownScheduleLabel{}'.format(i)),
                'time': ADDON.getSetting('ShutdownScheduleTime{}'.format(i)),
                'days_type': int(ADDON.getSetting('ShutdownScheduleDays{}'.format(i))),
                'custom_days': ADDON.getSetting('ShutdownCustomDays{}'.format(i)).split(','),
                'action': int(ADDON.getSetting('ShutdownAction{}'.format(i)) or "0"),
                'index': i
            }
            settings.append(setting)
    
    # Add global settings
    global_settings = {
        'notification': ADDON.getSetting('ShowShutdownNotification') == 'true'
    }
    
    return settings, global_settings

def check_day_match(settings, current_day_idx):
    """Check if today matches the days setting"""
    day_match = False
    
    if settings['days_type'] == 0:  # Every day
        day_match = True
    elif settings['days_type'] == 1 and current_day_idx < 5:  # Weekdays
        day_match = True
    elif settings['days_type'] == 2 and current_day_idx >= 5:  # Weekends
        day_match = True
    elif settings['days_type'] == 3:  # Custom days
        day_nums = [int(d.strip()) for d in settings['custom_days'] if d.strip().isdigit()]
        day_indices = [d-1 for d in day_nums if 1 <= d <= 7]  # Convert to 0-6
        day_match = current_day_idx in day_indices
    
    return day_match

def should_shutdown_now(settings):
    """Determine if it's time to shut down based on settings and current time"""
    # Parse shutdown time
    hour, minute = settings['time'].split(':')
    hour = int(hour)
    minute = int(minute)
    
    # Get current time
    now = datetime.now()
    current_day_idx = now.weekday()  # 0=Monday, 6=Sunday
    
    # Convert to minutes since midnight for comparison
    current_minutes = now.hour * 60 + now.minute
    shutdown_minutes = hour * 60 + minute
    
    # Check if within the shutdown window (current time equals target time)
    # Only trigger at exact minute to prevent multiple triggers
    time_match = (current_minutes == shutdown_minutes)
    
    # Check if today matches the days setting
    day_match = check_day_match(settings, current_day_idx)
    
    # Log detailed info
    log("Checking schedule '{}'".format(settings['label']), xbmc.LOGERROR)
    log("Current time: {}:{:02d}".format(now.hour, now.minute), xbmc.LOGERROR)
    log("Shutdown time: {}:{:02d}".format(hour, minute), xbmc.LOGERROR)
    log("Minutes from midnight - Current: {}, Shutdown: {}".format(current_minutes, shutdown_minutes), xbmc.LOGERROR)
    log("Time match (within window): {}".format(time_match), xbmc.LOGERROR)
    log("Current day index: {}".format(current_day_idx), xbmc.LOGERROR)
    log("Day match: {}".format(day_match), xbmc.LOGERROR)
    
    # Return true if shutdown should trigger, along with hour, minute, label, and action
    should_trigger = settings['enabled'] and time_match and day_match
    log("Shutdown should trigger: {} (Action: {})".format(should_trigger, settings.get('action', 0)), xbmc.LOGERROR)
    return should_trigger, hour, minute, settings['label'], settings.get('action', 0)

def execute_shutdown(label, action):
    """Execute the shutdown action script with specific action parameter"""
    log("EXECUTING SHUTDOWN SEQUENCE FOR: {} (Action: {})".format(label, action), xbmc.LOGERROR)
    
    # Show notification
    _, global_settings = get_shutdown_settings()
    if global_settings['notification']:
        # Enhanced notification with the schedule name
        notify("Executing scheduled shutdown: " + label, "PTV Scheduler")
    
    # Execute the shutdown action script with the specific action
    # FIXED PATH: Changed from 'schedulers' to 'resources/lib'
    shutdown_script = os.path.join(ADDON_PATH, 'resources', 'lib', 'ptv_shutdown_action.py')
    log("Executing shutdown script: {} with action {}".format(shutdown_script, action), xbmc.LOGERROR)
    
    # Wait a moment to ensure notification shows
    xbmc.sleep(2000)
    
    # Execute the script with the action parameter
    xbmc.executebuiltin('RunScript("{}", {})'.format(shutdown_script, action))
    
    # Log completion
    log("Shutdown script execution request sent", xbmc.LOGERROR)

def main():
    """Main function - runs the shutdown timer"""
    log("Starting PTV Shutdown Timer", xbmc.LOGERROR)
    
    # Show startup notification with enhanced message
    notify("Shutdown scheduling service started", "PTV Scheduler")
    
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
            shutdown_settings, _ = get_shutdown_settings()
            
            # Check all enabled shutdown schedulers
            for settings in shutdown_settings:
                # Check if this scheduler should trigger shutdown
                should_trigger, hour, minute, label, action = should_shutdown_now(settings)
                
                if should_trigger:
                    schedule_id = settings['index']
                    
                    # Check cooldown
                    if schedule_id in last_triggered:
                        time_since_last = (now - last_triggered[schedule_id]).total_seconds()
                        if time_since_last < (cooldown_minutes * 60):
                            log("Schedule {} still in cooldown period ({:.1f} seconds remaining)".format(
                                schedule_id, (cooldown_minutes * 60) - time_since_last), xbmc.LOGERROR)
                            continue
                    
                    log("Triggering shutdown for {} (Schedule {}) with action {}".format(label, schedule_id, action), xbmc.LOGERROR)
                    execute_shutdown(label, action)
                    
                    # Update last triggered time for this schedule
                    last_triggered[schedule_id] = now
        
        except Exception as e:
            log("Error in shutdown timer: {}".format(e), xbmc.LOGERROR)
        
        # Sleep for a short time before checking again (10 seconds)
        xbmc.sleep(10000)
    
    log("Shutdown timer ended")

# Run the timer
if __name__ == "__main__":
    main()