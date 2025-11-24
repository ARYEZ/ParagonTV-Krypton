#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Paragon TV Autopilot Mode Service - Simplified Implementation
Syncs only cache folder and settings2.xml from master
"""

import xbmc
import xbmcaddon
import xbmcgui
import os
import sys
import shutil
import subprocess
from datetime import datetime
import hashlib
import time

ADDON_ID = 'script.paragontv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')

class AutopilotService:
    def __init__(self):
        self.running = True
        self.master_ip = REAL_SETTINGS.getSetting('AutopilotMasterIP')
        self.sync_interval = int(REAL_SETTINGS.getSetting('AutopilotSyncInterval'))
        self.sync_method = int(REAL_SETTINGS.getSetting('AutopilotSyncMethod'))
        
        self.local_path = xbmc.translatePath('special://profile/addon_data/{}/'.format(ADDON_ID))
        self.local_cache = os.path.join(self.local_path, 'cache/')
        self.local_settings2 = os.path.join(self.local_path, 'settings2.xml')
        
        # Track last known state
        self.settings2_checksum = None
        self.cache_checksums = {}
        self.connected = False
        self.initial_sync_done = False
        
        self.log("Autopilot Mode initialized - Master: {}".format(self.master_ip))
        self.update_status("Initializing")
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log('[PTV Autopilot] {}'.format(msg), level)
        
    def update_status(self, status):
        """Update status in settings"""
        REAL_SETTINGS.setSetting('AutopilotSyncStatus', status)
        if status == "Connected":
            REAL_SETTINGS.setSetting('AutopilotLastSync', 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
    def test_connection(self):
        """Test SSH connection to master"""
        try:
            cmd = ['ssh', '-o', 'ConnectTimeout=5', '-o', 'BatchMode=yes', 
                   'root@{}'.format(self.master_ip), 'echo "connected"']
            result = subprocess.call(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result == 0
        except Exception as e:
            return False
            
    def get_file_checksum(self, filepath):
        """Calculate MD5 checksum of file"""
        try:
            if filepath.startswith('root@'):  # Remote file
                cmd = ['ssh', 'root@{}'.format(self.master_ip), 
                       'md5sum {}'.format(filepath.split(':')[1])]
                output = subprocess.check_output(cmd).strip()
                return output.split()[0] if output else None
            else:  # Local file
                with open(filepath, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            return None
            
    def sync_settings2(self):
        """Sync settings2.xml if changed"""
        try:
            remote_settings2 = 'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/settings2.xml'.format(
                self.master_ip)
            
            # Check if remote file exists
            check_cmd = ['ssh', 'root@{}'.format(self.master_ip), 
                        'test -f /storage/.kodi/userdata/addon_data/script.paragontv/settings2.xml']
            if subprocess.call(check_cmd) != 0:
                self.log("settings2.xml not found on master")
                return False
                
            # Get remote checksum
            remote_checksum = self.get_file_checksum(remote_settings2)
            
            # Compare with local
            if remote_checksum and remote_checksum != self.settings2_checksum:
                self.log("settings2.xml changed, syncing...")
                
                # Backup local file if it exists
                if os.path.exists(self.local_settings2):
                    backup_path = self.local_settings2 + '.autopilot_backup'
                    shutil.copy2(self.local_settings2, backup_path)
                
                # Copy from master
                scp_cmd = ['scp', '-o', 'ConnectTimeout=10',
                          remote_settings2, self.local_settings2]
                
                if subprocess.call(scp_cmd) == 0:
                    self.settings2_checksum = remote_checksum
                    self.log("settings2.xml synced successfully")
                    
                    # Check for force reset flag
                    self.check_force_reset()
                    return True
                else:
                    self.log("Failed to sync settings2.xml", xbmc.LOGERROR)
                    return False
            else:
                self.log("settings2.xml unchanged", xbmc.LOGDEBUG)
                return True
                
        except Exception as e:
            self.log("Error syncing settings2.xml: {}".format(str(e)), xbmc.LOGERROR)
            return False
            
    def sync_cache_folder(self):
        """Sync cache folder if changed"""
        try:
            # Create local cache if needed
            if not os.path.exists(self.local_cache):
                os.makedirs(self.local_cache)
                
            # Check if remote cache exists
            check_cmd = ['ssh', 'root@{}'.format(self.master_ip), 
                        'test -d /storage/.kodi/userdata/addon_data/script.paragontv/cache']
            if subprocess.call(check_cmd) != 0:
                self.log("Cache folder not found on master")
                return True  # Not an error
                
            # For initial sync or if no checksums, sync everything
            if not self.initial_sync_done or not self.cache_checksums:
                self.log("Performing full cache sync...")
                
                if self.sync_method == 0 and self.check_rsync_available():
                    # Use rsync
                    rsync_cmd = [
                        'rsync', '-az', '--delete', '--timeout=30',
                        'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/cache/'.format(self.master_ip),
                        self.local_cache
                    ]
                    result = subprocess.call(rsync_cmd)
                else:
                    # Use SCP
                    remote_cache = 'root@{}:/storage/.kodi/userdata/addon_data/script.paragontv/cache/*'.format(
                        self.master_ip)
                    scp_cmd = ['scp', '-r', '-o', 'ConnectTimeout=10',
                              remote_cache, self.local_cache]
                    result = subprocess.call(scp_cmd)
                    
                if result == 0:
                    self.log("Cache folder synced successfully")
                    self.initial_sync_done = True
                    # Update checksums after sync
                    self.update_cache_checksums()
                    return True
                else:
                    self.log("Failed to sync cache folder", xbmc.LOGERROR)
                    return False
                    
            else:
                # Check for changes
                changed_files = self.check_cache_changes()
                if changed_files:
                    self.log("Cache files changed: {}".format(len(changed_files)))
                    for remote_file in changed_files:
                        local_file = remote_file.replace(
                            '/storage/.kodi/userdata/addon_data/script.paragontv/cache/',
                            self.local_cache
                        )
                        
                        # Ensure directory exists
                        local_dir = os.path.dirname(local_file)
                        if not os.path.exists(local_dir):
                            os.makedirs(local_dir)
                            
                        # Copy file
                        scp_cmd = ['scp', '-o', 'ConnectTimeout=10',
                                  'root@{}:{}'.format(self.master_ip, remote_file),
                                  local_file]
                        subprocess.call(scp_cmd)
                        
                    # Update checksums
                    self.update_cache_checksums()
                    return True
                else:
                    self.log("Cache unchanged", xbmc.LOGDEBUG)
                    return True
                    
        except Exception as e:
            self.log("Error syncing cache: {}".format(str(e)), xbmc.LOGERROR)
            return False
            
    def check_cache_changes(self):
        """Check which cache files have changed"""
        changed_files = []
        try:
            # Get list of remote cache files with checksums
            cmd = ['ssh', 'root@{}'.format(self.master_ip),
                   'find /storage/.kodi/userdata/addon_data/script.paragontv/cache -type f -exec md5sum {} \\;']
            output = subprocess.check_output(cmd).strip()
            
            if output:
                for line in output.split('\n'):
                    if line:
                        checksum, filepath = line.split('  ', 1)
                        if filepath not in self.cache_checksums or self.cache_checksums[filepath] != checksum:
                            changed_files.append(filepath)
                            
        except Exception as e:
            self.log("Error checking cache changes: {}".format(str(e)), xbmc.LOGDEBUG)
            
        return changed_files
        
    def update_cache_checksums(self):
        """Update stored checksums for cache files"""
        try:
            cmd = ['ssh', 'root@{}'.format(self.master_ip),
                   'find /storage/.kodi/userdata/addon_data/script.paragontv/cache -type f -exec md5sum {} \\;']
            output = subprocess.check_output(cmd).strip()
            
            self.cache_checksums = {}
            if output:
                for line in output.split('\n'):
                    if line:
                        checksum, filepath = line.split('  ', 1)
                        self.cache_checksums[filepath] = checksum
                        
        except Exception as e:
            self.log("Error updating cache checksums: {}".format(str(e)), xbmc.LOGDEBUG)
            
    def check_rsync_available(self):
        """Check if rsync is available"""
        try:
            subprocess.call(['rsync', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            return False
            
    def check_force_reset(self):
        """Check if force reset is needed based on settings2.xml"""
        try:
            # Simple check for ForceChannelReset in settings2.xml
            if os.path.exists(self.local_settings2):
                with open(self.local_settings2, 'r') as f:
                    content = f.read()
                    if 'ForceChannelReset' in content and 'true' in content:
                        current_reset = REAL_SETTINGS.getSetting('ForceChannelReset')
                        if current_reset != 'true':
                            self.log("Force reset detected from master")
                            REAL_SETTINGS.setSetting('ForceChannelReset', 'true')
                            
        except Exception as e:
            self.log("Error checking force reset: {}".format(str(e)), xbmc.LOGDEBUG)
            
    def perform_sync(self):
        """Perform sync operation"""
        try:
            # Test connection
            if not self.test_connection():
                self.connected = False
                self.update_status("Connection Failed")
                return False
                
            # Sync settings2.xml
            settings_ok = self.sync_settings2()
            
            # Sync cache folder
            cache_ok = self.sync_cache_folder()
            
            if settings_ok and cache_ok:
                self.connected = True
                self.update_status("Connected")
                return True
            else:
                self.update_status("Sync Error")
                return False
                
        except Exception as e:
            self.log("Sync failed: {}".format(str(e)), xbmc.LOGERROR)
            self.update_status("Error")
            return False
            
    def monitor_loop(self):
        """Main monitoring loop"""
        self.log("Starting Autopilot monitoring loop", xbmc.LOGNOTICE)
        
        # Track connection state for notifications
        was_connected = False
        startup_notification_shown = False
        
        while self.running and not xbmc.abortRequested:
            # Check if still enabled
            if REAL_SETTINGS.getSetting('AutopilotEnabled') != 'true':
                self.log("Autopilot Mode disabled")
                break
                
            # Perform sync
            is_connected = self.perform_sync()
            
            # Handle notifications
            if is_connected and not was_connected:
                if not startup_notification_shown:
                    xbmcgui.Dialog().notification(
                        "Autopilot Mode",
                        "Connected to master at {}".format(self.master_ip),
                        xbmcgui.NOTIFICATION_INFO,
                        3000
                    )
                    startup_notification_shown = True
                else:
                    xbmcgui.Dialog().notification(
                        "Autopilot Mode",
                        "Reconnected to master",
                        xbmcgui.NOTIFICATION_INFO,
                        3000
                    )
                was_connected = True
                
            elif not is_connected and was_connected:
                xbmcgui.Dialog().notification(
                    "Autopilot Mode",
                    "Lost connection to master",
                    xbmcgui.NOTIFICATION_WARNING,
                    3000
                )
                was_connected = False
                
            # Wait for next sync
            for i in range(self.sync_interval):
                if self.running and not xbmc.abortRequested:
                    xbmc.sleep(1000)
                else:
                    break
                    
    def stop(self):
        """Stop the service"""
        self.running = False
        self.update_status("Stopped")
        self.log("Autopilot service stopped", xbmc.LOGNOTICE)

class AutopilotTester:
    """Test autopilot connection"""
    
    def __init__(self):
        self.master_ip = REAL_SETTINGS.getSetting('AutopilotMasterIP')
        
    def test(self):
        service = AutopilotService()
        
        xbmcgui.Dialog().notification("Testing Connection", 
                                     "Connecting to {}...".format(self.master_ip))
        
        if service.test_connection():
            try:
                # Check for settings2.xml
                cmd = ['ssh', 'root@{}'.format(self.master_ip),
                       'test -f /storage/.kodi/userdata/addon_data/script.paragontv/settings2.xml && echo "exists"']
                result = subprocess.check_output(cmd).strip()
                
                if result == "exists":
                    # Get channel count
                    cmd = ['ssh', 'root@{}'.format(self.master_ip),
                           'grep -c "Setting id=\\"Channel_.*_type\\"" /storage/.kodi/userdata/addon_data/script.paragontv/settings2.xml || echo "0"']
                    channels = subprocess.check_output(cmd).strip()
                    
                    message = "Connected! Master has {} channels configured".format(channels)
                else:
                    message = "Connected but no settings2.xml found on master"
                    
                xbmcgui.Dialog().ok("Connection Test", message)
                
            except Exception as e:
                xbmcgui.Dialog().ok("Connection Test", 
                                   "Connected to master at {}".format(self.master_ip))
        else:
            xbmcgui.Dialog().ok("Connection Test Failed",
                               "Cannot connect to master at {}".format(self.master_ip),
                               "Check IP address and SSH access")

# Service entry point
def main():
    if REAL_SETTINGS.getSetting('AutopilotEnabled') == 'true':
        service = AutopilotService()
        try:
            service.monitor_loop()
        except Exception as e:
            xbmc.log('[PTV Autopilot] Fatal error: {}'.format(str(e)), xbmc.LOGERROR)
        finally:
            service.stop()
    else:
        xbmc.log('[PTV Autopilot] Service not enabled', xbmc.LOGNOTICE)

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'TEST_AUTOPILOT':
        tester = AutopilotTester()
        tester.test()
    else:
        main()