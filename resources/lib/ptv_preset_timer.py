#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Paragon TV Preset Refresh Timer - 9-Phase Macro System
Consolidated system with built-in maintenance and startup functionality
Phase 4: Push to Satellites
Phase 9: Evening Startup (Final Phase)
"""

import os
import sys
import time
import traceback
from datetime import datetime, timedelta

import xbmc
import xbmcaddon
import xbmcgui

# Plugin Info
ADDON_ID = "script.paragontv"
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo("name")
ADDON_PATH = REAL_SETTINGS.getAddonInfo("path").decode("utf-8")


def log(msg, level=xbmc.LOGNOTICE):
    """Unified logging"""
    xbmc.log("[PTV Preset Timer] {}".format(msg), level)


def notify(message, heading="PTV Scheduler", icon="", time=5000, sound=True):
    """Display a notification with custom icon"""
    if icon == "":
        icon = os.path.join(ADDON_PATH, "scheduler_icon.png")
        if not os.path.exists(icon):
            icon = os.path.join(ADDON_PATH, "resources", "images", "icon.png")
        if not os.path.exists(icon):
            icon = xbmcgui.NOTIFICATION_INFO

    xbmcgui.Dialog().notification(heading, message, icon, time, sound)


class PresetRefreshTimer:
    def __init__(self):
        self.running = True
        self.last_phase_trigger = {}
        self.preset_names = ["Alpha", "Omega", "Delta", "Epsilon", "Gamma", "Sigma", "Omicron", "Theta", "Lambda"]
        log("PTV Preset Refresh Timer (9-Phase Consolidated System) initialized", xbmc.LOGNOTICE)

    def get_todays_preset(self):
        """Get which preset should run today"""
        weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday

        day_map = {
            0: "MondayPreset",
            1: "TuesdayPreset",
            2: "WednesdayPreset",
            3: "ThursdayPreset",
            4: "FridayPreset",
            5: "SaturdayPreset",
            6: "SundayPreset",
        }

        day_names = [
            "Monday", "Tuesday", "Wednesday", "Thursday", 
            "Friday", "Saturday", "Sunday"
        ]

        setting_name = day_map[weekday]
        preset_value_str = REAL_SETTINGS.getSetting(setting_name) or "0"
        preset_value = int(preset_value_str)
        
        # Debug logging
        log("DEBUG: Today is {} (weekday={})".format(day_names[weekday], weekday), xbmc.LOGNOTICE)
        log("DEBUG: Setting name: {}".format(setting_name), xbmc.LOGNOTICE)
        log("DEBUG: Raw preset value: '{}' (int: {})".format(preset_value_str, preset_value), xbmc.LOGNOTICE)
        log("DEBUG: Available presets: {}".format(self.preset_names), xbmc.LOGNOTICE)

        if preset_value == 0:
            log("No preset scheduled for {}".format(day_names[weekday]))
            return None
        elif preset_value <= 9:
            preset_name = self.preset_names[preset_value - 1]
            log("Today's preset for {}: {} (index={})".format(day_names[weekday], preset_name, preset_value - 1), xbmc.LOGNOTICE)
            return preset_name
        else:
            log("Invalid preset value {} for {}".format(preset_value, day_names[weekday]), xbmc.LOGERROR)
            return None

    def get_preset_config(self, preset_name):
        """Get configuration for all phases of a named preset"""
        if preset_name not in self.preset_names:
            return None

        config = {
            "name": preset_name,
            "description": REAL_SETTINGS.getSetting("{}Description".format(preset_name)) or preset_name,
        }

        # For satellite presets (Sigma, Omicron, Theta, Lambda), skip Phase 1 (no maintenance)
        if preset_name not in ["Sigma", "Omicron", "Theta", "Lambda"]:
            config["phase1"] = {
                "time": REAL_SETTINGS.getSetting("{}Phase1Time".format(preset_name)),
                "nfo_bumpers": REAL_SETTINGS.getSetting("{}Phase1NFOBumpers".format(preset_name)) == "true",
                "nfo_movies": REAL_SETTINGS.getSetting("{}Phase1NFOMovies".format(preset_name)) == "true",
                "nfo_television": REAL_SETTINGS.getSetting("{}Phase1NFOTelevision".format(preset_name)) == "true",
                "video_library": REAL_SETTINGS.getSetting("{}Phase1VideoLibrary".format(preset_name)) == "true",
                "clean_video": REAL_SETTINGS.getSetting("{}Phase1CleanVideo".format(preset_name)) == "true",
                "music_library": REAL_SETTINGS.getSetting("{}Phase1MusicLibrary".format(preset_name)) == "true",
                "clean_music": REAL_SETTINGS.getSetting("{}Phase1CleanMusic".format(preset_name)) == "true",
                "force_reset": REAL_SETTINGS.getSetting("{}Phase1ForceReset".format(preset_name)) == "true",
                "organize_channels": REAL_SETTINGS.getSetting("{}Phase1OrganizeChannels".format(preset_name)) == "true",
                "reload_config": REAL_SETTINGS.getSetting("{}Phase1ReloadConfig".format(preset_name)) == "true",
            }

        # Phases 2-9 are the same for all presets including satellite presets
        config["phase2"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase2Time".format(preset_name)),
            "enable_channel": REAL_SETTINGS.getSetting("{}Phase2EnableChannel".format(preset_name)) == "true",
            "start_channel": REAL_SETTINGS.getSetting("{}Phase2StartChannel".format(preset_name)),
            "volume_level": REAL_SETTINGS.getSetting("{}Phase2VolumeLevel".format(preset_name)),
        }
        config["phase3"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase3Time".format(preset_name)),
            "action": int(REAL_SETTINGS.getSetting("{}Phase3Action".format(preset_name)) or "0"),
        }
        config["phase4"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase4Time".format(preset_name)),
            "enable": REAL_SETTINGS.getSetting("{}Phase4Enable".format(preset_name)) == "true",
        }
        config["phase5"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase5Time".format(preset_name)),
            "enable_channel": REAL_SETTINGS.getSetting("{}Phase5EnableChannel".format(preset_name)) == "true",
            "start_channel": REAL_SETTINGS.getSetting("{}Phase5StartChannel".format(preset_name)),
            "volume_level": REAL_SETTINGS.getSetting("{}Phase5VolumeLevel".format(preset_name)),
        }
        config["phase6"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase6Time".format(preset_name)),
            "action": int(REAL_SETTINGS.getSetting("{}Phase6Action".format(preset_name)) or "0"),
        }
        config["phase7"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase7Time".format(preset_name)),
            "enable_channel": REAL_SETTINGS.getSetting("{}Phase7EnableChannel".format(preset_name)) == "true",
            "start_channel": REAL_SETTINGS.getSetting("{}Phase7StartChannel".format(preset_name)),
            "volume_level": REAL_SETTINGS.getSetting("{}Phase7VolumeLevel".format(preset_name)),
        }
        config["phase8"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase8Time".format(preset_name)),
            "action": int(REAL_SETTINGS.getSetting("{}Phase8Action".format(preset_name)) or "0"),
        }
        config["phase9"] = {
            "time": REAL_SETTINGS.getSetting("{}Phase9Time".format(preset_name)),
            "enable_channel": REAL_SETTINGS.getSetting("{}Phase9EnableChannel".format(preset_name)) == "true",
            "start_channel": REAL_SETTINGS.getSetting("{}Phase9StartChannel".format(preset_name)),
            "volume_level": REAL_SETTINGS.getSetting("{}Phase9VolumeLevel".format(preset_name)),
        }

        return config

    def check_phase_trigger(self, preset_name, phase_num, phase_time):
        """Check if a specific phase should trigger"""
        if not phase_time:
            return False

        now = datetime.now()
        hour, minute = phase_time.split(":")
        phase_dt = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

        # Check if within 30 second window
        time_diff = abs((now - phase_dt).total_seconds())
        if time_diff <= 30:
            # Check cooldown
            phase_key = "{}_phase{}_{}_{}".format(
                preset_name, phase_num, now.strftime("%Y%m%d"), phase_time.replace(":", "")
            )

            if phase_key in self.last_phase_trigger:
                last_trigger = self.last_phase_trigger[phase_key]
                if (now - last_trigger).total_seconds() < 120:  # 2 minute cooldown
                    return False

            self.last_phase_trigger[phase_key] = now
            return True

        return False

    def execute_phase1_maintenance(self, config):
        """Execute Phase 1 - Maintenance with built-in functionality"""
        log("Executing Phase 1 (Maintenance) for preset: {}".format(config["name"]), xbmc.LOGERROR)
        
        notify("Phase 1: Maintenance - {}".format(config["name"]), "PTV Preset Timer")
        
        phase1 = config["phase1"]
        tasks_completed = []
        show_notification = True  # Always show notifications for preset maintenance

        # 1. NFO Rename - Bumpers
        if phase1["nfo_bumpers"]:
            log("Running NFO renamer for Bumpers", xbmc.LOGERROR)
            if show_notification:
                notify("Renaming Bumper files...")
            
            bumpers_dir = REAL_SETTINGS.getSetting("NFOBumpersPath")
            if bumpers_dir:
                nfo_script = os.path.join(ADDON_PATH, "resources", "lib", "nfo_renamer_bumpers.py")
                if os.path.exists(nfo_script):
                    xbmc.executebuiltin("RunScript({}, {})".format(nfo_script, bumpers_dir))
                    xbmc.sleep(10000)
                    tasks_completed.append("Bumpers Renamed")
                else:
                    log("NFO renamer bumpers script not found: {}".format(nfo_script))
            else:
                log("Bumpers directory not configured")

        # 2. NFO Rename - Movies
        if phase1["nfo_movies"]:
            log("Running NFO renamer for Movies", xbmc.LOGERROR)
            if show_notification:
                notify("Renaming Movie files...")
            
            movies_dir = REAL_SETTINGS.getSetting("NFOMoviesPath")
            if movies_dir:
                nfo_script = os.path.join(ADDON_PATH, "resources", "lib", "nfo_renamer_movies.py")
                if os.path.exists(nfo_script):
                    xbmc.executebuiltin("RunScript({}, {}, --recursive)".format(nfo_script, movies_dir))
                    xbmc.sleep(15000)
                    tasks_completed.append("Movies Renamed")
                else:
                    log("NFO renamer movies script not found: {}".format(nfo_script))
            else:
                log("Movies directory not configured")

        # 3. NFO Rename - Television
        if phase1["nfo_television"]:
            log("Running NFO renamer for Television", xbmc.LOGERROR)
            if show_notification:
                notify("Renaming TV Show files...")
            
            tv_dir = REAL_SETTINGS.getSetting("NFOTelevisionPath")
            if tv_dir:
                nfo_script = os.path.join(ADDON_PATH, "resources", "lib", "nfo_renamer_television.py")
                if os.path.exists(nfo_script):
                    xbmc.executebuiltin("RunScript({}, {}, --recursive)".format(nfo_script, tv_dir))
                    xbmc.sleep(20000)
                    tasks_completed.append("TV Shows Renamed")
                else:
                    log("NFO renamer television script not found: {}".format(nfo_script))
            else:
                log("Television directory not configured")

        # 4. Update Video Library
        if phase1["video_library"]:
            log("Updating video library", xbmc.LOGERROR)
            if show_notification:
                notify("Updating video library...")
            
            xbmc.executebuiltin("UpdateLibrary(video)")
            xbmc.sleep(5000)
            
            max_wait = 300
            waited = 0
            while xbmc.getCondVisibility("Library.IsScanningVideo") and waited < max_wait:
                xbmc.sleep(1000)
                waited += 1
            
            tasks_completed.append("Video Library Updated")

            # Clean video library if enabled
            if phase1["clean_video"]:
                log("Cleaning video library", xbmc.LOGERROR)
                if show_notification:
                    notify("Cleaning video library...")
                
                xbmc.executebuiltin("CleanLibrary(video)")
                xbmc.sleep(5000)
                
                waited = 0
                while xbmc.getCondVisibility("Library.IsScanningVideo") and waited < max_wait:
                    xbmc.sleep(1000)
                    waited += 1
                
                tasks_completed.append("Video Library Cleaned")

        # 5. Update Music Library
        if phase1["music_library"]:
            log("Updating music library", xbmc.LOGERROR)
            if show_notification:
                notify("Updating music library...")
            
            xbmc.executebuiltin("UpdateLibrary(music)")
            xbmc.sleep(5000)
            
            max_wait = 300
            waited = 0
            while xbmc.getCondVisibility("Library.IsScanningMusic") and waited < max_wait:
                xbmc.sleep(1000)
                waited += 1
            
            tasks_completed.append("Music Library Updated")

            # Clean music library if enabled
            if phase1["clean_music"]:
                log("Cleaning music library", xbmc.LOGERROR)
                if show_notification:
                    notify("Cleaning music library...")
                
                xbmc.executebuiltin("CleanLibrary(music)")
                xbmc.sleep(5000)
                
                waited = 0
                while xbmc.getCondVisibility("Library.IsScanningMusic") and waited < max_wait:
                    xbmc.sleep(1000)
                    waited += 1
                
                tasks_completed.append("Music Library Cleaned")

        # 6. Organize Channels
        if phase1["organize_channels"]:
            log("Running channel organizer", xbmc.LOGERROR)
            if show_notification:
                notify("Organizing channels...")
            
            organizer_script = os.path.join(ADDON_PATH, "resources", "lib", "channel_organizer.py")
            if os.path.exists(organizer_script):
                xbmc.executebuiltin("RunScript({})".format(organizer_script))
                xbmc.sleep(2000)
                tasks_completed.append("Channels Organized")
            else:
                log("Channel organizer script not found: {}".format(organizer_script))

        # 7. Reload Configuration
        if phase1["reload_config"]:
            log("Running config reloader", xbmc.LOGERROR)
            if show_notification:
                notify("Reloading configuration...")
            
            reloader_script = os.path.join(ADDON_PATH, "resources", "lib", "config_reloader.py")
            if os.path.exists(reloader_script):
                xbmc.executebuiltin("RunScript({})".format(reloader_script))
                xbmc.sleep(2000)
                tasks_completed.append("Config Reloaded")
            else:
                log("Config reloader script not found: {}".format(reloader_script))

        # 8. Force Channel Reset (Last)
        if phase1["force_reset"]:
            log("Setting force channel reset", xbmc.LOGERROR)
            REAL_SETTINGS.setSetting("ForceChannelReset", "true")
            tasks_completed.append("Channel Reset Flag Set")
            
            if show_notification:
                notify("Channel reset scheduled for next startup")

        # Log completion
        if tasks_completed:
            log("Maintenance completed. Tasks run: {}".format(", ".join(tasks_completed)))
            if show_notification:
                task_summary = ", ".join(tasks_completed[:3])
                if len(tasks_completed) > 3:
                    task_summary += "..."
                notify("Maintenance completed: {}".format(task_summary))
        else:
            log("No maintenance tasks were enabled for preset {}".format(config["name"]))

        # Update last run time
        now = datetime.now()
        REAL_SETTINGS.setSetting("LastMaintenanceRun", now.strftime("%Y-%m-%d %H:%M"))
        
        log("Phase 1 maintenance completed for preset {}".format(config["name"]), xbmc.LOGERROR)

    def execute_phase4_push(self, config):
        """Execute Phase 4 - Push to Satellites"""
        log("Executing Phase 4 (Push to Satellites) for preset: {}".format(config["name"]), xbmc.LOGERROR)
        
        # Satellite presets always skip Phase 4 (they're for satellite systems only)
        if config["name"] in ["Sigma", "Omicron", "Theta", "Lambda"]:
            log("Phase 4 skipped for {} preset (satellite-only preset)".format(config["name"]), xbmc.LOGNOTICE)
            return
        
        if not config["phase4"]["enable"]:
            log("Phase 4 disabled for preset {}".format(config["name"]))
            return
        
        icon_path = os.path.join(ADDON_PATH, "icon.png")
        notify("Phase 4: Pushing to satellites - {}".format(config["name"]), "PTV Preset Timer", icon_path)
        
        push_script = os.path.join(ADDON_PATH, "resources", "lib", "ptv_push_to_satellites.py")
        
        if os.path.exists(push_script):
            try:
                xbmc.executebuiltin("RunScript({})".format(push_script))
                log("Launched push to satellites script", xbmc.LOGERROR)
            except Exception as e:
                log("Error launching push script: {}".format(e), xbmc.LOGERROR)
                notify("Failed to launch push script", "PTV Preset Timer")
        else:
            log("Push script not found: {}".format(push_script), xbmc.LOGERROR)
            notify("Push script not found", "PTV Preset Timer")

    def execute_startup_phase(self, config, phase_num, phase_data, phase_name):
        """Generic startup phase execution for phases 2, 5, 7, 9"""
        log("Executing Phase {} ({}) for preset: {}".format(phase_num, phase_name, config["name"]), xbmc.LOGERROR)

        notify("Phase {}: {} - {}".format(phase_num, phase_name, config["name"]), "PTV Preset Timer")

        # Check if ForceChannelReset is enabled (from phase 1)
        # For satellite presets, since there's no Phase 1, ForceChannelReset won't be set
        force_reset = REAL_SETTINGS.getSetting("ForceChannelReset") == "true" if phase_num == 2 else False

        if force_reset:
            log("Channel rebuild in progress - launching PTV without channel tuning", xbmc.LOGERROR)
            REAL_SETTINGS.setSetting("PresetRebuildMode", "true")

        # Launch PTV
        log("Launching PTV...", xbmc.LOGERROR)
        xbmc.executebuiltin("RunScript(script.paragontv)")

        # Wait for PTV to initialize
        xbmc.sleep(15000)  # 15 seconds

        # Handle channel tuning if not in rebuild mode
        if not force_reset and phase_data["enable_channel"] and phase_data["start_channel"]:
            channel_num = phase_data["start_channel"].strip()
            log("Tuning to channel: {}".format(channel_num), xbmc.LOGERROR)

            # Send channel digits
            for digit in channel_num:
                xbmc.executebuiltin("Action(Number{})".format(digit))
                log("Sent digit: {}".format(digit), xbmc.LOGERROR)
                xbmc.sleep(1000)

            # Confirm channel
            xbmc.sleep(2000)
            xbmc.executebuiltin("Action(Select)")

        # Set volume if specified
        if phase_data["volume_level"]:
            try:
                vol_percent = int(phase_data["volume_level"])
                xbmc.executebuiltin("SetVolume({})".format(vol_percent))
                log("Set volume to {}%".format(vol_percent), xbmc.LOGERROR)
            except:
                pass

        # Clear force reset flag after phase 5 (first wake)
        if phase_num == 5:
            REAL_SETTINGS.setSetting("ForceChannelReset", "false")

        # Show completion for final phase (phase 9)
        if phase_num == 9:
            notify("Final startup complete: {}".format(config["name"]), "PTV Preset Timer")
            log("Phase 9 final startup completed - {} preset sequence finished".format(config["name"]), xbmc.LOGERROR)

        log("Phase {} startup completed".format(phase_num), xbmc.LOGERROR)

    def execute_shutdown_phase(self, config, phase_num, phase_data, phase_name):
        """Generic shutdown phase execution for phases 3, 6, 8"""
        log("Executing Phase {} ({}) for preset: {}".format(phase_num, phase_name, config["name"]), xbmc.LOGERROR)

        notify("Phase {}: {} - {}".format(phase_num, phase_name, config["name"]), "PTV Preset Timer")

        action = phase_data["action"]  # 0=Blackout, 1=Normal

        # Execute shutdown action script
        shutdown_script = os.path.join(ADDON_PATH, "resources", "lib", "ptv_shutdown_action.py")
        xbmc.executebuiltin("RunScript({}, {})".format(shutdown_script, action))

        # Clear rebuild mode flag on first shutdown
        if phase_num == 3:
            REAL_SETTINGS.setSetting("PresetRebuildMode", "false")

        log("Phase {} shutdown triggered (action: {})".format(phase_num, action), xbmc.LOGERROR)

    def check_phases(self):
        """Check all phases for today's preset"""
        try:
            preset_name = self.get_todays_preset()
            if not preset_name:
                return

            config = self.get_preset_config(preset_name)
            if not config:
                log("Failed to get config for preset: {}".format(preset_name))
                return

            # Check Phase 1 only if preset has it (not satellite presets)
            if "phase1" in config and self.check_phase_trigger(preset_name, 1, config["phase1"]["time"]):
                self.execute_phase1_maintenance(config)

            # Check remaining phases (2-9) - all presets including satellite presets have these
            if self.check_phase_trigger(preset_name, 2, config["phase2"]["time"]):
                self.execute_startup_phase(config, 2, config["phase2"], "First Startup")

            elif self.check_phase_trigger(preset_name, 3, config["phase3"]["time"]):
                self.execute_shutdown_phase(config, 3, config["phase3"], "First Shutdown")

            elif self.check_phase_trigger(preset_name, 4, config["phase4"]["time"]):
                self.execute_phase4_push(config)

            elif self.check_phase_trigger(preset_name, 5, config["phase5"]["time"]):
                self.execute_startup_phase(config, 5, config["phase5"], "First Wake")

            elif self.check_phase_trigger(preset_name, 6, config["phase6"]["time"]):
                self.execute_shutdown_phase(config, 6, config["phase6"], "Second Shutdown")

            elif self.check_phase_trigger(preset_name, 7, config["phase7"]["time"]):
                self.execute_startup_phase(config, 7, config["phase7"], "Second Startup")

            elif self.check_phase_trigger(preset_name, 8, config["phase8"]["time"]):
                self.execute_shutdown_phase(config, 8, config["phase8"], "Third Shutdown")

            elif self.check_phase_trigger(preset_name, 9, config["phase9"]["time"]):
                self.execute_startup_phase(config, 9, config["phase9"], "Evening Startup")

        except Exception as e:
            log("Error checking phases: {}".format(str(e)), xbmc.LOGERROR)
            log(traceback.format_exc(), xbmc.LOGERROR)

    def run(self):
        """Main timer loop"""
        log("Starting PTV Preset Refresh Timer (9-Phase Consolidated System)", xbmc.LOGNOTICE)

        notify("9-Phase preset system started", "PTV Preset Timer", time=3000)

        preset_name = self.get_todays_preset()
        if preset_name:
            xbmc.sleep(3000)
            notify("Today's preset: {}".format(preset_name), "PTV Preset Timer", time=3000)

        while self.running and not xbmc.abortRequested:
            try:
                if REAL_SETTINGS.getSetting("EnablePresetSystem") == "true":
                    self.check_phases()

                xbmc.sleep(10000)

            except Exception as e:
                log("Error in timer loop: {}".format(str(e)), xbmc.LOGERROR)
                xbmc.sleep(30000)

        log("PTV Preset Refresh Timer stopped", xbmc.LOGNOTICE)

    def stop(self):
        """Stop the timer"""
        self.running = False


# Main execution
if __name__ == "__main__":
    preset_timer = PresetRefreshTimer()

    try:
        preset_timer.run()
    except Exception as e:
        log("Fatal error in preset timer: {}".format(str(e)), xbmc.LOGERROR)
        notify("Error: {}".format(str(e)), "PTV Preset Timer", time=5000)
    finally:
        preset_timer.stop()