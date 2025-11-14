#!/usr/bin/python
#   Channel Organizer for Paragon TV
#
# This script organizes channels in the settings2.xml file according to specific rules.
# It can be run as a standalone script or called from PTV utilities.

import os
import re
import shutil
import sys
from collections import OrderedDict
from datetime import datetime

# Try to import Kodi modules, but provide fallbacks for CLI usage
try:
    import xbmc
    import xbmcgui

    IN_KODI = True
except ImportError:
    IN_KODI = False

    # Define fallback functions for CLI usage
    class xbmc:
        LOGNOTICE = 1

        @staticmethod
        def log(msg, level=1):
            print(msg)

    class xbmcgui:
        class Dialog:
            @staticmethod
            def ok(*args):
                print(" ".join(args[1:]))

            @staticmethod
            def yesno(*args):
                return True


def get_settings_path():
    """Get the path to settings2.xml"""
    return "/storage/.kodi/userdata/addon_data/script.paragontv/settings2.xml"


def log(message):
    """Log message to Kodi log or print to console"""
    if IN_KODI:
        xbmc.log("PTV Channel Organizer: " + str(message), level=xbmc.LOGNOTICE)
    else:
        print("PTV Channel Organizer: " + str(message))


def organize_channels():
    """
    Organizes channels according to specific rules
    """
    log("Starting channel organization")

    input_file = get_settings_path()

    try:
        # Check if file exists
        if not os.path.exists(input_file):
            log("ERROR: Settings file not found at {0}".format(input_file))
            if IN_KODI:
                xbmcgui.Dialog().ok(
                    "Error",
                    "Settings file not found",
                    "Could not find settings2.xml at:",
                    input_file,
                )
            return False

        log("Using settings file: {0}".format(input_file))

        # Create backup
        backup_file = input_file + ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(input_file, backup_file)
        log("Created backup: {0}".format(backup_file))

        # Read the input file
        with open(input_file, "r") as f:
            lines = f.readlines()

        # Parse all settings into a structure
        all_settings = OrderedDict()
        channel_data = {}

        for line in lines:
            line = line.strip()
            if not line or line == "<settings>" or line == "</settings>":
                continue

            # Parse setting line
            match = re.match(r'<setting id="([^"]+)" value="([^"]+)" />', line)
            if match:
                setting_id = match.group(1)
                setting_value = match.group(2)

                # Check if it's a channel setting
                channel_match = re.match(r"Channel_(\d+)_(.+)", setting_id)
                if channel_match:
                    channel_num = int(channel_match.group(1))
                    setting_type = channel_match.group(2)

                    if channel_num not in channel_data:
                        channel_data[channel_num] = {}
                    channel_data[channel_num][setting_type] = setting_value
                else:
                    # Non-channel setting
                    all_settings[setting_id] = setting_value

        log(
            "Found {0} channels and {1} other settings".format(
                len(channel_data), len(all_settings)
            )
        )

        # Categorize channels
        type3_non_documentary = []
        type3_documentary_performance = []
        type3_music_video = []
        type0_holiday_playlists = []
        type4_channels = []
        type12_channels = []
        preserved_channels = {}

        for channel_num, settings in channel_data.items():
            # Preserve channel 1 and channels 110+
            if channel_num == 1 or channel_num >= 110:
                preserved_channels[channel_num] = settings
                continue

            channel_type = settings.get("type", "")
            channel_name = settings.get("1", "")

            if channel_type == "0":
                type0_holiday_playlists.append((channel_num, channel_name, settings))
            elif channel_type == "3":
                # Check documentary/performance FIRST before music keywords
                if (
                    "documentary" in channel_name.lower()
                    or "performance" in channel_name.lower()
                ):
                    type3_documentary_performance.append(
                        (channel_num, channel_name, settings)
                    )
                # Then check if it's in music video range or has music keywords
                elif 70 <= channel_num <= 79 or any(
                    kw in channel_name.lower() for kw in ["music", "mtv", "vh1", "vevo"]
                ):
                    type3_music_video.append((channel_num, channel_name, settings))
                else:
                    type3_non_documentary.append((channel_num, channel_name, settings))
            elif channel_type == "4":
                type4_channels.append((channel_num, channel_name, settings))
            elif channel_type == "12":
                type12_channels.append((channel_num, channel_name, settings))
            else:
                # Preserve any other type
                preserved_channels[channel_num] = settings

        # Sort each category alphabetically by name
        type3_non_documentary.sort(key=lambda x: x[1].lower())
        type3_documentary_performance.sort(key=lambda x: x[1].lower())
        type3_music_video.sort(key=lambda x: x[1].lower())
        type4_channels.sort(key=lambda x: x[1].lower())
        type12_channels.sort(key=lambda x: x[1].lower())

        # Sort holiday playlists by holiday order
        def holiday_sort(item):
            name = item[1].lower()
            if "halloween" in name:
                return 1
            elif "thanksgiving" in name:
                return 2
            elif "christmas" in name:
                return 3
            else:
                return 4

        type0_holiday_playlists.sort(key=holiday_sort)

        # Build new channel lineup
        new_channels = OrderedDict()

        # Preserved channel 1
        if 1 in preserved_channels:
            new_channels[1] = preserved_channels[1]

        # Assign channels starting at 2
        current_num = 2

        # Type 3 non-documentary
        for _, name, settings in type3_non_documentary:
            new_channels[current_num] = settings
            current_num += 1

        # Type 3 documentary/performance
        for _, name, settings in type3_documentary_performance:
            new_channels[current_num] = settings
            current_num += 1

        # Type 0 holiday playlists
        for _, name, settings in type0_holiday_playlists:
            new_channels[current_num] = settings
            current_num += 1

        # Type 4 movies starting at 50
        current_num = max(50, current_num)
        for _, name, settings in type4_channels:
            new_channels[current_num] = settings
            current_num += 1

        # Type 3 music videos at 70-79
        music_num = 70
        for _, name, settings in type3_music_video:
            if music_num <= 79:
                new_channels[music_num] = settings
                music_num += 1

        # Type 12 audio at 90-99
        audio_num = 90
        for _, name, settings in type12_channels:
            if audio_num <= 99:
                new_channels[audio_num] = settings
                audio_num += 1

        # Add preserved channels 110+
        for channel_num in sorted(preserved_channels.keys()):
            if channel_num >= 110:
                new_channels[channel_num] = preserved_channels[channel_num]

        # Write new settings file
        with open(input_file, "w") as f:
            f.write("<settings>\n")

            # Write non-channel settings first
            for setting_id, value in all_settings.items():
                f.write(
                    '    <setting id="{0}" value="{1}" />\n'.format(setting_id, value)
                )

            # Write channel settings
            for channel_num in sorted(new_channels.keys()):
                settings = new_channels[channel_num]
                for setting_type in sorted(settings.keys()):
                    f.write(
                        '    <setting id="Channel_{0}_{1}" value="{2}" />\n'.format(
                            channel_num, setting_type, settings[setting_type]
                        )
                    )

            f.write("</settings>\n")

        log("Successfully reorganized channels")

        # Remote sync
        try:
            remote_ip = "10.0.0.91"
            remote_user = "root"
            remote_path = "/storage/.kodi/addons/script.remoteartwork/resources/media/flags/numbers/"

            import subprocess

            scp_cmd = [
                "scp",
                input_file,
                "{0}@{1}:{2}".format(remote_user, remote_ip, remote_path),
            ]
            result = subprocess.call(scp_cmd)

            if result == 0:
                log("Successfully synchronized to remote system")
        except Exception as e:
            log("Remote sync failed: {0}".format(str(e)))

        if IN_KODI:
            xbmcgui.Dialog().ok("Success", "Channels have been organized!")

        return True

    except Exception as e:
        log("Error: {0}".format(str(e)))
        import traceback

        log("Traceback: {0}".format(traceback.format_exc()))

        if IN_KODI:
            xbmcgui.Dialog().ok("Error", "Failed to organize channels:", str(e))

        return False


if __name__ == "__main__":
    organize_channels()
