#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Paragon TV Satellite Alignment - Push entire addon and skin to satellite systems
"""

import os
import sys
import subprocess
import xbmc
import xbmcaddon
import xbmcgui

ADDON_ID = 'script.paragontv'
ADDON = xbmcaddon.Addon(ADDON_ID)

# Addons to push during satellite alignment
ADDONS_TO_PUSH = [
    {'name': 'script.paragontv', 'path': '/storage/.kodi/addons/script.paragontv/'},
    {'name': 'script.paragon', 'path': '/storage/.kodi/addons/script.paragon/'},
]

def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("[PTV Satellite Alignment] " + str(msg), level)

def notify(msg, title="Satellite Alignment", icon=None):
    if icon is None:
        icon = "special://home/addons/script.paragontv/icon.png"
    xbmc.executebuiltin("Notification({}, {}, 5000, {})".format(title, msg, icon))

def push_addon_to_satellite(addon_info, satellite_ip, use_rsync):
    """Push a single addon to a satellite system"""
    addon_name = addon_info['name']
    addon_path = addon_info['path']

    if not os.path.exists(addon_path):
        log("Addon path not found, skipping: {}".format(addon_path))
        return True  # Not a failure, just skip

    log("Pushing {} to {}".format(addon_name, satellite_ip))

    if use_rsync:
        # Use rsync - delete files on destination that don't exist in source
        rsync_cmd = ['rsync', '-az', '--delete', addon_path,
                   'root@{}:/storage/.kodi/addons/'.format(satellite_ip)]
        result = subprocess.call(rsync_cmd)
    else:
        # Use scp as fallback (recursive copy)
        # First, remove the old addon folder on the satellite
        rm_cmd = ['ssh', 'root@{}'.format(satellite_ip),
                 'rm -rf /storage/.kodi/addons/{}'.format(addon_name)]
        subprocess.call(rm_cmd)

        # Then copy the new one
        scp_cmd = ['scp', '-r', '-o', 'ConnectTimeout=10', addon_path,
                  'root@{}:/storage/.kodi/addons/'.format(satellite_ip)]
        result = subprocess.call(scp_cmd)

    if result == 0:
        log("Successfully pushed {} to {}".format(addon_name, satellite_ip))
        return True
    else:
        log("Failed to push {} to {}".format(addon_name, satellite_ip), xbmc.LOGERROR)
        return False

def satellite_alignment():
    """Push entire addon and skin to configured satellite systems"""
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

    # Check if at least one addon path exists
    available_addons = [a for a in ADDONS_TO_PUSH if os.path.exists(a['path'])]
    if not available_addons:
        log("No addon paths found", xbmc.LOGERROR)
        notify("No addon paths found", "Error")
        return False

    icon_path = "/storage/.kodi/addons/script.paragontv/icon.png"
    addon_names = ", ".join([a['name'] for a in available_addons])
    notify("Aligning {} satellite(s)".format(len(satellite_ips)), icon=icon_path)
    log("Addons to push: {}".format(addon_names))
    success_count = 0

    # Check if rsync is available (once, not per satellite)
    use_rsync = subprocess.call(['which', 'rsync'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

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

            # Push all addons to this satellite
            all_pushed = True
            for addon_info in ADDONS_TO_PUSH:
                if not push_addon_to_satellite(addon_info, satellite_ip, use_rsync):
                    all_pushed = False

            if all_pushed:
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
                log("Partial failure aligning {}".format(satellite_ip), xbmc.LOGERROR)

        except Exception as e:
            log("Error aligning {}: {}".format(satellite_ip, str(e)), xbmc.LOGERROR)

    log("Alignment completed. {} of {} satellites aligned".format(success_count, len(satellite_ips)))

    if success_count > 0:
        notify("Alignment complete. Updated {} satellite(s)".format(success_count), icon=icon_path)
    else:
        notify("Alignment failed", "Error", icon=icon_path)
        
    return success_count > 0

# Main execution
if __name__ == "__main__":
    satellite_alignment()
