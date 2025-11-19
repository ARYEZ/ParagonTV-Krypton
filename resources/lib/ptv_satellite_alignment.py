#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Paragon TV Satellite Alignment - Push entire addon to satellite systems
"""

import os
import sys
import subprocess
import xbmc
import xbmcaddon
import xbmcgui

ADDON_ID = 'script.paragontv'
ADDON = xbmcaddon.Addon(ADDON_ID)
ADDON_PATH = '/storage/.kodi/addons/script.paragontv/'

def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[PTV Satellite Alignment] " + str(msg), level)

def notify(msg, title="Satellite Alignment"):
    xbmc.executebuiltin("Notification({}, {}, 5000)".format(title, msg))

def satellite_alignment():
    """Push entire addon to configured satellite systems"""
    log("Starting satellite alignment")
    
    # Check if satellite alignment is enabled
    if ADDON.getSetting("EnableSatelliteAlignment") != "true":
        log("Satellite alignment disabled")
        return False
        
    # Get satellite IPs from settings
    satellite_ips = []
    for i in range(1, 6):  # Support up to 5 satellites
        satellite_ip = ADDON.getSetting("SlaveIP{}".format(i))
        if satellite_ip:
            satellite_ips.append(satellite_ip)
    
    if not satellite_ips:
        log("No satellite systems configured")
        notify("No satellites configured")
        return False
        
    # Check if source addon path exists
    if not os.path.exists(ADDON_PATH):
        log("Addon path not found: {}".format(ADDON_PATH), xbmc.LOGERROR)
        notify("Addon path not found", "Error")
        return False
        
    notify("Aligning {} satellite(s)".format(len(satellite_ips)))
    success_count = 0
    
    for satellite_ip in satellite_ips:
        try:
            log("Aligning satellite: {}".format(satellite_ip))
            
            # Test connection first
            test_cmd = ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', 
                       'root@{}'.format(satellite_ip), 'echo "connected"']
            result = subprocess.call(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result != 0:
                log("Cannot connect to satellite {}".format(satellite_ip), xbmc.LOGWARNING)
                continue
                
            # Push entire addon folder
            log("Pushing addon to {}".format(satellite_ip))
            
            # Check if rsync is available
            rsync_check = subprocess.call(['which', 'rsync'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if rsync_check == 0:
                # Use rsync - delete files on destination that don't exist in source
                rsync_cmd = ['rsync', '-az', '--delete', ADDON_PATH,
                           'root@{}:/storage/.kodi/addons/'.format(satellite_ip)]
                result = subprocess.call(rsync_cmd)
            else:
                # Use scp as fallback (recursive copy)
                # First, remove the old addon folder on the satellite
                rm_cmd = ['ssh', 'root@{}'.format(satellite_ip), 
                         'rm -rf /storage/.kodi/addons/script.paragontv']
                subprocess.call(rm_cmd)
                
                # Then copy the new one
                scp_cmd = ['scp', '-r', '-o', 'ConnectTimeout=10', ADDON_PATH,
                          'root@{}:/storage/.kodi/addons/'.format(satellite_ip)]
                result = subprocess.call(scp_cmd)
                
            if result == 0:
                log("Successfully aligned {}".format(satellite_ip))
                success_count += 1
                
                # Send notification to the satellite box
                notify_cmd = ['ssh', 'root@{}'.format(satellite_ip),
                            'kodi-send --action="Notification(Satellite Alignment,Satellites Realigned. Reset in 10 seconds.,10000)"']
                subprocess.call(notify_cmd)
                
                # Schedule Kodi restart on satellite after 10 seconds
                restart_cmd = ['ssh', 'root@{}'.format(satellite_ip),
                             'nohup sh -c "sleep 10 && killall -9 kodi.bin" > /dev/null 2>&1 &']
                subprocess.call(restart_cmd)
                
                log("Scheduled restart for {} in 10 seconds".format(satellite_ip))
            else:
                log("Failed to align {}".format(satellite_ip), xbmc.LOGERROR)
                
        except Exception as e:
            log("Error aligning {}: {}".format(satellite_ip, str(e)), xbmc.LOGERROR)
            
    log("Alignment completed. {} of {} satellites aligned".format(success_count, len(satellite_ips)))
    
    if success_count > 0:
        notify("Alignment complete. Updated {} satellite(s)".format(success_count))
    else:
        notify("Alignment failed", "Error")
        
    return success_count > 0

# Main execution
if __name__ == "__main__":
    satellite_alignment()
