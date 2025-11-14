#   Copyright (C) 2025 Aryez
#
#
# This file is part of Paragon TV
#
# Paragon TV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Paragon TV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Paragon TV.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui

# Plugin Info
ADDON_ID = "script.paragontv"
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo("name")
ADDON_PATH = REAL_SETTINGS.getAddonInfo("path")
ADDON_VERSION = REAL_SETTINGS.getAddonInfo("version")
ICON = os.path.join(ADDON_PATH, "icon.png")
LANGUAGE = REAL_SETTINGS.getLocalizedString

# Autostart settings
timer_amounts = [0, 5, 10, 15, 20]
IDLE_TIME = timer_amounts[int(REAL_SETTINGS.getSetting("timer_amount"))]
Msg = REAL_SETTINGS.getSetting("notify")
Enabled = REAL_SETTINGS.getSetting("enable")


def log(msg, level=xbmc.LOGDEBUG):
    try:
        xbmc.log(ADDON_ID + "-" + ADDON_NAME + "-" + str(msg), level)
    except Exception as e:
        pass


def migrate_legacy_maintenance_schedules():
    """
    One-time migration to clean up legacy custom maintenance schedules (1-10).
    Schedule 99 is preserved as it's used by the preset sequence system.
    """
    # Check if migration has already run
    if REAL_SETTINGS.getSetting('maintenance_migration_complete') == 'true':
        return
    
    log('[Migration] Cleaning up legacy maintenance schedules...', xbmc.LOGNOTICE)
    
    # List of all setting suffixes for each schedule
    setting_suffixes = [
        'EnableMaintenanceScheduler',
        'MaintenanceLabel',
        'MaintenanceTime',
        'MaintenanceDays',
        'MaintenanceWeekday',
        'MaintenanceDayOfMonth',
        'MaintenanceCustomDays',
        'LastMaintenanceRun',
        'MaintenanceNFOBumpers',
        'MaintenanceNFOMovies',
        'MaintenanceNFOTelevision',
        'MaintenanceVideoLibrary',
        'MaintenanceCleanVideo',
        'MaintenanceMusicLibrary',
        'MaintenanceCleanMusic',
        'MaintenanceOrganizeChannels',
        'MaintenanceReloadConfig',
        'MaintenanceForceReset'
    ]
    
    # Clean up schedules 1-10 (preserve 99 for preset system)
    schedules_cleaned = 0
    for schedule_id in range(1, 11):
        # Check if this schedule was enabled
        was_enabled = REAL_SETTINGS.getSetting('EnableMaintenanceScheduler{}'.format(schedule_id)) == 'true'
        
        if was_enabled:
            schedule_name = REAL_SETTINGS.getSetting('MaintenanceLabel{}'.format(schedule_id))
            log('[Migration] Disabling legacy schedule {}: {}'.format(schedule_id, schedule_name), xbmc.LOGNOTICE)
            schedules_cleaned += 1
        
        # Clear all settings for this schedule
        for suffix in setting_suffixes:
            setting_id = '{}{}'.format(suffix, schedule_id)
            try:
                # Set to empty string for text fields, 'false' for booleans
                if suffix.startswith('Enable') or suffix.startswith('Maintenance') and not suffix.endswith('Label'):
                    REAL_SETTINGS.setSetting(setting_id, 'false')
                else:
                    REAL_SETTINGS.setSetting(setting_id, '')
            except Exception as e:
                # Some settings might not exist, that's okay
                pass
    
    # Mark migration as complete
    REAL_SETTINGS.setSetting('maintenance_migration_complete', 'true')
    
    if schedules_cleaned > 0:
        log('[Migration] Cleaned up {} legacy maintenance schedule(s)'.format(schedules_cleaned), xbmc.LOGNOTICE)
        log('[Migration] All maintenance tasks should now be configured via Preset Sequences', xbmc.LOGNOTICE)
    else:
        log('[Migration] No legacy schedules found to clean up', xbmc.LOGNOTICE)
    
    log('[Migration] Legacy maintenance schedule cleanup complete', xbmc.LOGNOTICE)


class Service(object):

    def __init__(self):
        self.stop = False
        self.autostart_complete = False
        self.settingsMonitor = SettingsMonitor()
        self.autopilot_thread = None

        # Run migration before anything else
        migrate_legacy_maintenance_schedules()

        # Track enable states to detect changes
        self._maintenance_enabled = (
            REAL_SETTINGS.getSetting("EnableMaintenanceScheduler") == "true"
        )
        self._startup_enabled = (
            REAL_SETTINGS.getSetting("EnableStartupScheduler") == "true"
        )
        self._shutdown_enabled = (
            REAL_SETTINGS.getSetting("EnableShutdownScheduler") == "true"
        )
        self._preset_enabled = REAL_SETTINGS.getSetting("EnablePresetSystem") == "true"
        self._autopilot_enabled = REAL_SETTINGS.getSetting("AutopilotEnabled") == "true"

        # Handle autostart first
        if Enabled == "true":
            self.autostart()

        # Then start all services
        self.startTimers()
        self.startAutopilot()

    def autostart(self):
        """Handle Paragon TV autostart"""
        if Msg == "true":
            xbmc.executebuiltin(
                "Notification( %s, %s, %d, %s)"
                % (ADDON_NAME, LANGUAGE(30030), 4000, ICON)
            )
        xbmc.sleep(IDLE_TIME * 1000)
        xbmc.executebuiltin("RunScript(" + ADDON_ID + ")")
        log("AUTOSTART PTV: Service Started...")
        self.autostart_complete = True

    def startTimers(self):
        """Start all scheduler services"""
        try:
            # Check if we're in Autopilot Mode (slave)
            autopilot_enabled = REAL_SETTINGS.getSetting("AutopilotEnabled") == "true"
            
            if autopilot_enabled:
                log("Autopilot Mode enabled - skipping local timer services")
                # In autopilot mode, we don't run local timers
                # The master controls everything
                return

            # Start maintenance timer
            maintenance_enabled = (
                REAL_SETTINGS.getSetting("EnableMaintenanceScheduler") == "true"
            )
            if maintenance_enabled:
                maintenance_timer = os.path.join(
                    ADDON_PATH, "resources", "lib", "ptv_maintenance_timer.py"
                )
                if os.path.exists(maintenance_timer):
                    log("Starting Maintenance Timer Service")
                    xbmc.executebuiltin('RunScript("{}")'.format(maintenance_timer))
                else:
                    log(
                        "Maintenance timer script not found at: {}".format(
                            maintenance_timer
                        ),
                        xbmc.LOGERROR,
                    )

            # Start startup timer
            startup_enabled = (
                REAL_SETTINGS.getSetting("EnableStartupScheduler") == "true"
            )
            if startup_enabled:
                startup_timer = os.path.join(
                    ADDON_PATH, "resources", "lib", "ptv_startup_timer.py"
                )
                if os.path.exists(startup_timer):
                    log("Starting Startup Timer Service")
                    xbmc.executebuiltin('RunScript("{}")'.format(startup_timer))
                else:
                    log(
                        "Startup timer script not found at: {}".format(startup_timer),
                        xbmc.LOGERROR,
                    )

            # Start shutdown scheduler
            shutdown_enabled = (
                REAL_SETTINGS.getSetting("EnableShutdownScheduler") == "true"
            )
            if shutdown_enabled:
                shutdown_scheduler = os.path.join(
                    ADDON_PATH, "resources", "lib", "ptv_shutdown_timer.py"
                )
                if os.path.exists(shutdown_scheduler):
                    log("Starting Shutdown Scheduler Service")
                    xbmc.executebuiltin('RunScript("{}")'.format(shutdown_scheduler))
                else:
                    log(
                        "Shutdown scheduler script not found at: {}".format(
                            shutdown_scheduler
                        ),
                        xbmc.LOGERROR,
                    )

            # Start preset system timer
            preset_enabled = REAL_SETTINGS.getSetting("EnablePresetSystem") == "true"
            if preset_enabled:
                preset_timer = os.path.join(
                    ADDON_PATH, "resources", "lib", "ptv_preset_timer.py"
                )
                if os.path.exists(preset_timer):
                    log("Starting Preset System Timer Service", xbmc.LOGNOTICE)
                    xbmc.executebuiltin('RunScript("{}")'.format(preset_timer))
                else:
                    log(
                        "Preset system timer script not found at: {}".format(
                            preset_timer
                        ),
                        xbmc.LOGERROR,
                    )

        except Exception as e:
            log("Error starting timer services: {}".format(str(e)), xbmc.LOGERROR)

    def startAutopilot(self):
        """Start autopilot service if enabled"""
        try:
            if REAL_SETTINGS.getSetting("AutopilotEnabled") == "true":
                log("Starting Autopilot Mode", xbmc.LOGNOTICE)
                
                # Add lib path
                lib_path = os.path.join(ADDON_PATH, "resources", "lib")
                if lib_path not in sys.path:
                    sys.path.append(lib_path)
                
                # Import and start autopilot service
                import autopilot_service
                
                # Create thread for autopilot
                self.autopilot_thread = threading.Thread(
                    target=autopilot_service.main,
                    name="PTV-Autopilot"
                )
                self.autopilot_thread.daemon = True
                self.autopilot_thread.start()
                
                log("Autopilot service started successfully")
                
                # Show notification
                xbmcgui.Dialog().notification(
                    "Paragon TV Autopilot",
                    "Multi-room sync enabled",
                    ICON,
                    3000
                )
                
        except Exception as e:
            log("Failed to start Autopilot: {}".format(str(e)), xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                "Autopilot Error",
                "Failed to start - check logs",
                xbmcgui.NOTIFICATION_ERROR,
                5000
            )

    def stopAutopilot(self):
        """Stop autopilot service if running"""
        try:
            if self.autopilot_thread and self.autopilot_thread.is_alive():
                log("Stopping Autopilot service")
                # The autopilot service monitors xbmc.abortRequested
                # So it should stop gracefully
                self.autopilot_thread.join(timeout=5)
                if self.autopilot_thread.is_alive():
                    log("Autopilot service did not stop gracefully", xbmc.LOGWARNING)
        except Exception as e:
            log("Error stopping Autopilot: {}".format(str(e)), xbmc.LOGERROR)

    def onScreensaverActivated(self):
        log("Screensaver activated")

    def onScreensaverDeactivated(self):
        log("Screensaver deactivated")

    def onSettingsChanged(self):
        log("Settings changed")
        
        # Check if Autopilot Mode setting changed
        current_autopilot = REAL_SETTINGS.getSetting("AutopilotEnabled") == "true"
        if current_autopilot != self._autopilot_enabled:
            self._autopilot_enabled = current_autopilot
            
            if current_autopilot:
                # Autopilot was just enabled
                log("Autopilot Mode enabled - starting service")
                self.startAutopilot()
                
                # Stop local timers if running
                log("Stopping local timer services")
                xbmc.executebuiltin("StopScript(ptv_maintenance_timer.py)")
                xbmc.executebuiltin("StopScript(ptv_startup_timer.py)")
                xbmc.executebuiltin("StopScript(ptv_shutdown_timer.py)")
                xbmc.executebuiltin("StopScript(ptv_preset_timer.py)")
            else:
                # Autopilot was just disabled
                log("Autopilot Mode disabled - stopping service")
                self.stopAutopilot()
                
                # Restart local timers
                log("Restarting local timer services")
                self.startTimers()

    def doStop(self):
        self.stop = True

        # Stop autopilot if running
        self.stopAutopilot()

        # Stop all timer services
        try:
            log("Stopping all timer services")
            xbmc.executebuiltin("StopScript(ptv_maintenance_timer.py)")
            xbmc.executebuiltin("StopScript(ptv_startup_timer.py)")
            xbmc.executebuiltin("StopScript(ptv_shutdown_timer.py)")
            xbmc.executebuiltin("StopScript(ptv_preset_timer.py)")
        except Exception as e:
            log("Error stopping timer services: {}".format(str(e)), xbmc.LOGERROR)


class Player(xbmc.Player):

    def __init__(self):
        xbmc.Player.__init__(self)

    def onPlayBackStarted(self):
        log("Playback started")

    def onPlayBackStopped(self):
        log("Playback stopped")

    def onPlayBackEnded(self):
        log("Playback ended")


class Monitor(xbmc.Monitor):

    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.service = None

    def onScreensaverActivated(self):
        if self.service:
            self.service.onScreensaverActivated()

    def onScreensaverDeactivated(self):
        if self.service:
            self.service.onScreensaverDeactivated()

    def onSettingsChanged(self):
        if self.service:
            self.service.onSettingsChanged()

    def onAbortRequested(self):
        if self.service:
            self.service.doStop()


class SettingsMonitor(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.start()

    def run(self):
        log("Settings monitor started")
        while not self.stopped.wait(5):
            pass
        log("Settings monitor stopped")

    def stop(self):
        self.stopped.set()


# Start service
if __name__ == "__main__":
    log("Paragon TV Service Started")
    log("Version: " + ADDON_VERSION)

    monitor = Monitor()
    player = Player()
    service = Service()
    monitor.service = service

    # Main service loop
    while not service.stop:
        if xbmc.abortRequested:
            break
        xbmc.sleep(1000)

    # Cleanup
    service.settingsMonitor.stop()
    service.doStop()
    del monitor
    del player
    del service

    log("Paragon TV Service Stopped")