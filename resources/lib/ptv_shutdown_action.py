#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# PTV Shutdown Action Script
# Handles PTV shutdown using button sequences or nuclear option
#

import xbmc
import xbmcaddon
import xbmcgui
import os
import sys
import json
import time

# Get addon info
ADDON_ID = 'script.paragontv'
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = ADDON.getAddonInfo('path')

# Define file paths
RESTART_MARKER = os.path.join(ADDON_PATH, ".kodi_restart_marker")  # Hidden file
if sys.platform.startswith('win'):
    KILL_SCRIPT = os.path.join(ADDON_PATH, "kill_kodi.bat")
else:
    KILL_SCRIPT = os.path.join(ADDON_PATH, ".kill_kodi.sh")  # Hidden file

def log(msg):
    """Log messages to Kodi log"""
    xbmc.log('[PTV Shutdown Action] {}'.format(msg), xbmc.LOGERROR)

def notify(message, heading="PTV Scheduler"):
    """Display a notification"""
    xbmcgui.Dialog().notification(heading, message, xbmcgui.NOTIFICATION_INFO, 5000, True)

def execute_blackout_sequence():
    """Execute the Blackout sequence for PTV"""
    log("Executing Blackout sequence for PTV")
    
    # For PTV, we might need to adjust this sequence
    # This is a placeholder - you'll need to test what works for PTV
    
    # Press Back to bring up the PTV exit confirmation dialog
    log("Pressing Back to show exit dialog")
    xbmc.executebuiltin("Action(Back)")
    xbmc.sleep(1000)
       
    # Press Select/Enter to confirm exit
    log("Pressing Select to confirm exit")
    xbmc.executebuiltin("Action(Select)")
    xbmc.sleep(1000)  # Give it time to process the exit

def execute_normal_sequence():
    """Execute the Normal exit sequence for PTV"""
    log("Executing Normal exit sequence for PTV")
    
    # Press Back to bring up the PTV exit confirmation dialog
    log("Pressing Back to show exit dialog")
    xbmc.executebuiltin("Action(Back)")
    xbmc.sleep(1000)
       
    # Press Select/Enter to confirm exit
    log("Pressing Select to confirm exit")
    xbmc.executebuiltin("Action(Select)")
    xbmc.sleep(1000)  # Give it time to process the exit

def is_ptv_running():
    """Check if PTV is still running or if any video is playing"""
    log("Checking if PTV is still running")
    
    try:
        # Check 1: Is there an active player?
        request = {
            "jsonrpc": "2.0",
            "method": "Player.GetActivePlayers",
            "id": 1
        }
        
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        
        # If there are active players, check if it's video
        if "result" in response and len(response["result"]) > 0:
            log("Active player detected")
            
            # Check what type of player is active
            for player in response["result"]:
                if player.get("type") == "video":
                    log("Video player is active - PTV or video still playing")
                    return True
            
            # Also check for PTV overlay specifically
            if xbmc.getCondVisibility('Window.IsActive(script-paragontv-TVOverlay.xml)'):
                log("PTV overlay window is active")
                return True
            
            # Alternative: check if PTV property is set
            if xbmc.getInfoLabel('Window(Home).Property(PTV.Running)') == 'True':
                log("PTV property indicates it's running")
                return True
        
        log("No video playing and PTV not detected as running")
        return False
    except Exception as e:
        log("Error checking if PTV is running: {}".format(e))
        # If we can't determine, assume it's not running to avoid killall
        return False

def cleanup_old_files():
    """Clean up any old temp files that might be present"""
    log("Checking for old temporary files to clean up")
    
    # Check restart marker
    if os.path.exists(RESTART_MARKER):
        try:
            with open(RESTART_MARKER, 'r') as f:
                timestamp = int(f.read().strip())
            
            # If marker is older than 2 minutes, remove it
            current_time = int(time.time())
            if (current_time - timestamp) > 120:
                log("Removing old restart marker")
                os.remove(RESTART_MARKER)
        except Exception as e:
            log("Error checking old restart marker: {}".format(e))
            try:
                os.remove(RESTART_MARKER)
            except:
                pass
    
    # Check for kill script
    if os.path.exists(KILL_SCRIPT):
        try:
            # Get file modification time
            mtime = os.path.getmtime(KILL_SCRIPT)
            current_time = time.time()
            
            # If script is older than 2 minutes, remove it
            if (current_time - mtime) > 120:
                log("Removing old kill script")
                os.remove(KILL_SCRIPT)
        except Exception as e:
            log("Error removing old kill script: {}".format(e))
            try:
                os.remove(KILL_SCRIPT)
            except:
                pass

def check_recently_restarted():
    """Check if Kodi was recently restarted by this script"""
    if os.path.exists(RESTART_MARKER):
        try:
            with open(RESTART_MARKER, 'r') as f:
                timestamp = int(f.read().strip())
            
            # Check if restart was recent (within last 60 seconds)
            current_time = int(time.time())
            if (current_time - timestamp) < 60:
                log("Kodi was recently restarted by this script, avoiding nuclear option")
                return True
        except Exception as e:
            log("Error checking restart marker: {}".format(e))
    
    return False

def create_restart_marker():
    """Create a marker file to indicate Kodi was restarted by this script"""
    try:
        with open(RESTART_MARKER, 'w') as f:
            f.write(str(int(time.time())))
        log("Created restart marker file")
        
        # Add auto-cleanup to the kill script
        return True
    except Exception as e:
        log("Error creating restart marker: {}".format(e))
        return False

def create_nuclear_script():
    """Create a script that will execute the nuclear option after a delay"""
    try:
        # Check if we're on Windows
        if sys.platform.startswith('win'):
            # Create a batch file for Windows
            KILL_SCRIPT = os.path.join(ADDON_PATH, "kill_kodi.bat")
            with open(KILL_SCRIPT, 'w') as f:
                f.write('@echo off\r\n')
                f.write('timeout /t 3 /nobreak > nul\r\n')  # Wait 3 seconds
                f.write('taskkill /F /IM kodi.exe\r\n')  # Force kill Kodi
                f.write('exit\r\n')
            
            return KILL_SCRIPT
        else:
            # Original Linux/Unix version
            with open(KILL_SCRIPT, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('# Wait 3 seconds to allow python script to exit\n')
                f.write('sleep 3\n')
                f.write('# Kill Kodi\n')
                f.write('killall -9 kodi.bin\n')
                f.write('# Set up auto-cleanup after restart\n')
                f.write('(sleep 300 && rm -f "{}" "{}") &\n'.format(RESTART_MARKER, KILL_SCRIPT))
            
            # Make it executable
            os.chmod(KILL_SCRIPT, 0o755)
            
            return KILL_SCRIPT
    except Exception as e:
        log("Error creating nuclear script: {}".format(e))
        return None

def nuclear_option():
    """Execute the nuclear option safely"""
    # First create the restart marker to prevent endless loop
    if not create_restart_marker():
        log("Failed to create restart marker, aborting nuclear option")
        return False
    
    # Then create and execute the kill script
    kill_script = create_nuclear_script()
    if kill_script:
        log("Launching kill script: {}".format(kill_script))
        if sys.platform.startswith('win'):
            # Windows: use START command to run batch file
            os.system('start "" "{}"'.format(kill_script))
        else:
            # Linux/Unix: use shell
            os.system("sh {} &".format(kill_script))
        return True
    else:
        log("Failed to create kill script")
        return False

# Main execution
if __name__ == "__main__":
    log("Shutdown action script started")
    
    # Always clean up any old files first
    cleanup_old_files()
    
    # Parse action parameter if provided
    action = 0  # Default to Blackout Exit
    
    if len(sys.argv) > 1:
        try:
            action = int(sys.argv[1])
            log("Using action from command line: {}".format(action))
        except:
            log("Failed to parse action parameter, defaulting to Blackout Exit")
    
    # Check if we recently restarted - if so, exit early to avoid infinite loop
    if check_recently_restarted():
        log("Exiting early to avoid post-restart loop")
        sys.exit(0)
    
    # Show notification if enabled
    show_notification = ADDON.getSetting('ShowShutdownNotification') == 'true'
    
    # Step 1: Try the button sequence
    if action == 0:  # Blackout Exit
        execute_blackout_sequence()
    else:  # Normal Exit
        execute_normal_sequence()
    
    # Step 2: Wait for the sequence to take effect
    xbmc.sleep(3000)  # Reduced from 5 seconds
    
    # Step 3: Check if PTV is still running or if any video is playing
    if is_ptv_running():
        log("Button sequence failed, trying nuclear option")
        
        # Show notification before we kill Kodi
        if show_notification:
            notify("Button sequence failed, using nuclear option...")
            xbmc.sleep(2000)  # Give time for notification to appear
        
        # Execute nuclear option
        nuclear_option()
    else:
        # Normal exit was successful
        if show_notification:
            if action == 0:
                notify("Paragon TV blackout shutdown complete")
            else:
                notify("Paragon TV normal shutdown complete")
        
        log("Shutdown completed successfully using button sequence")