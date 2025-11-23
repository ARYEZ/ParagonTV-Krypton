#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Paragon TV Push to Satellites - Standalone script for pushing after rebuild
"""

import os
import sys
import subprocess
import xbmc
import xbmcaddon
import xbmcgui

ADDON_ID = 'script.paragontv'
ADDON = xbmcaddon.Addon(ADDON_ID)

def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[PTV Push to Satellites] " + str(msg), level)

def notify(msg, title="PTV Push", icon=None):
    if icon is None:
        icon = "special://home/addons/script.paragontv/icon.png"
    xbmc.executebuiltin("Notification({}, {}, 5000, {})".format(title, msg, icon))

def push_to_satellites():
    """Push settings and cache to configured satellite systems"""
    log("Starting push to satellite systems")
    
    # Check if master push is enabled
    if ADDON.getSetting("EnableMasterPush") != "true":
        log("Master push disabled")
        return False
        
    # Get satelliteIPs from settings
    satellite_ips = []
    for i in range(1, 6):  # Support up to 5 satellites
        satellite_ip = ADDON.getSetting("SlaveIP{}".format(i))
        if satellite_ip:
            satellite_ips.append(satellite_ip)
    
    if not satellite_ips:
        log("No satellite systems configured")
        notify("No satellites configured")
        return False
        
    # Source paths
    addon_data = xbmc.translatePath('special://profile/addon_data/{}/'.format(ADDON_ID))
    settings2_path = os.path.join(addon_data, 'settings2.xml')
    cache_path = os.path.join(addon_data, 'cache/')
    
    # Check if files exist
    if not os.path.exists(settings2_path):
        log("settings2.xml not found", xbmc.LOGERROR)
        notify("settings2.xml not found", "Error")
        return False
        
    if not os.path.exists(cache_path):
        log("cache folder not found", xbmc.LOGERROR)
        notify("cache folder not found", "Error")
        return False
        
    notify("Pushing to {} satellite(s)".format(len(satellite_ips)))
    success_count = 0
    
    for satellite_ip in satellite_ips:
        try:
            log("Pushing to satellite: {}".format(satellite_ip))
            
            # Test connection first
            test_cmd = ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', 
                       'root@{}'.format(satellite_ip), 'echo "connected"']
            result = subprocess.call(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result != 0:
                log("Cannot connect to satellite{}".format(satellite_ip), xbmc.LOGWARNING)
                continue
                
            # Create target directory if needed
            mkdir_cmd = ['ssh', 'root@{}'.format(satellite_ip), 
                        'mkdir -p /storage/.kodi/userdata/addon_data/script.paragontv/cache']
            subprocess.call(mkdir_cmd)
            
            # Push settings2.xml
            log("Pushing settings2.xml to {}".format(satellite_ip))
            scp_cmd = ['scp', '-o', 'ConnectTimeout=10', settings2_path,
                      'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/'.format(satellite_ip)]
            result = subprocess.call(scp_cmd)
            
            if result != 0:
                log("Failed to push settings2.xml to {}".format(satellite_ip), xbmc.LOGERROR)
                continue
                
            # Push cache folder
            log("Pushing cache folder to {}".format(satellite_ip))
            
            # Check if rsync is available
            rsync_check = subprocess.call(['which', 'rsync'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if rsync_check == 0:
                # Use rsync
                rsync_cmd = ['rsync', '-az', '--delete', cache_path,
                           'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/'.format(satellite_ip)]
                result = subprocess.call(rsync_cmd)
            else:
                # Use scp as fallback
                scp_cmd = ['scp', '-r', '-o', 'ConnectTimeout=10', cache_path,
                          'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/'.format(satellite_ip)]
                result = subprocess.call(scp_cmd)
                
            if result == 0:
                log("Successfully pushed to {}".format(satellite_ip))
                success_count += 1
            else:
                log("Failed to push cache to {}".format(satellite_ip), xbmc.LOGERROR)
                
        except Exception as e:
            log("Error pushing to {}: {}".format(satellite_ip, str(e)), xbmc.LOGERROR)
            
    log("Push completed. {} of {} satellites updated".format(success_count, len(satellite_ips)))
    
    if success_count > 0:
        notify("Updated {} satellite(s)".format(success_count), "Push Complete")
    else:
        notify("Failed to update satellites", "Push Failed")
        
    return success_count > 0

# Main execution
if __name__ == "__main__":
    push_to_satellites()