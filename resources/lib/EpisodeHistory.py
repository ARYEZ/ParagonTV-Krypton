#   Copyright (C) 2025 Aryez
#
#
# This file is part of Paragon TV.
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

import json
import os
import time
from datetime import datetime

import xbmc
from FileAccess import FileAccess
from Globals import CHANNELS_LOC, log


class EpisodeHistory:
    """
    Manages per-channel episode history to prevent repeats.
    Tracks episodes per show, resetting each show independently when exhausted.
    """

    def __init__(self, channel_number):
        self.channel_number = channel_number
        self.history_dir = os.path.join(CHANNELS_LOC, "history")
        self.history_file = os.path.join(
            self.history_dir, "channel_{}_history.json".format(channel_number)
        )
        self.data = {
            "channel": channel_number,
            "channel_name": "",
            "last_updated": "",
            "shows": {},
        }
        self.loaded = False

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("EpisodeHistory (Ch{}): {}".format(self.channel_number, msg), level)

    def ensure_history_dir(self):
        """Create history directory if it doesn't exist"""
        if not os.path.exists(self.history_dir):
            try:
                os.makedirs(self.history_dir)
                self.log("Created history directory: {}".format(self.history_dir))
            except Exception as e:
                self.log("Failed to create history directory: {}".format(str(e)), xbmc.LOGERROR)
                return False
        return True

    def load(self):
        """Load episode history from JSON file"""
        if self.loaded:
            return True

        if not self.ensure_history_dir():
            return False

        if not os.path.exists(self.history_file):
            self.log("No history file found, starting fresh")
            self.loaded = True
            return True

        try:
            with open(self.history_file, "r") as f:
                self.data = json.load(f)
            self.log("Loaded history: {} shows tracked".format(len(self.data.get("shows", {}))))
            self.loaded = True
            return True
        except Exception as e:
            self.log("Failed to load history: {}".format(str(e)), xbmc.LOGERROR)
            # Start fresh if load fails
            self.data = {
                "channel": self.channel_number,
                "channel_name": "",
                "last_updated": "",
                "shows": {},
            }
            self.loaded = True
            return False

    def save(self):
        """Save episode history to JSON file"""
        if not self.ensure_history_dir():
            return False

        self.data["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.history_file, "w") as f:
                json.dump(self.data, f, indent=2)
            self.log("Saved history: {} shows tracked".format(len(self.data.get("shows", {}))))
            return True
        except Exception as e:
            self.log("Failed to save history: {}".format(str(e)), xbmc.LOGERROR)
            return False

    def set_channel_name(self, name):
        """Set the channel name in history data"""
        self.data["channel_name"] = name

    def get_played_episodes(self, show_name):
        """Get list of played episode file paths for a show"""
        if not self.loaded:
            self.load()

        shows = self.data.get("shows", {})
        if show_name not in shows:
            return []

        return shows[show_name].get("played_episodes", [])

    def get_available_episodes(self, show_name, all_episodes):
        """
        Get list of available (unplayed) episodes for a show.
        If all episodes are played, resets the show and returns all episodes.

        Args:
            show_name: Name of the show
            all_episodes: List of all episode file paths for this show

        Returns:
            List of available episode file paths
        """
        if not self.loaded:
            self.load()

        played = self.get_played_episodes(show_name)
        available = [ep for ep in all_episodes if ep not in played]

        # If exhausted, reset this show
        if len(available) == 0 and len(all_episodes) > 0:
            self.reset_show(show_name, len(all_episodes))
            available = all_episodes
            self.log(
                "{} EXHAUSTED - Reset to cycle {}".format(
                    show_name, self.get_cycle_count(show_name)
                ),
                xbmc.LOGNOTICE
            )

        return available

    def reset_show(self, show_name, total_available=0):
        """Reset play history for a specific show"""
        if not self.loaded:
            self.load()

        shows = self.data.get("shows", {})

        if show_name not in shows:
            shows[show_name] = {
                "played_episodes": [],
                "total_available": total_available,
                "current_cycle_start": datetime.now().isoformat(),
                "times_cycled": 0,
            }
        else:
            shows[show_name]["played_episodes"] = []
            shows[show_name]["current_cycle_start"] = datetime.now().isoformat()
            shows[show_name]["times_cycled"] = shows[show_name].get("times_cycled", 0) + 1
            shows[show_name]["total_available"] = total_available

        self.data["shows"] = shows

    def mark_episodes_played(self, episode_list):
        """
        Mark episodes as played from distributed episode list.

        Args:
            episode_list: List of episode strings (format: "duration,show//episode//desc\nfilepath")
        """
        if not self.loaded:
            self.load()

        shows = self.data.get("shows", {})

        for episode_str in episode_list:
            try:
                # Parse episode string to extract show name and file path
                parts = episode_str.split("\n")
                if len(parts) >= 2:
                    filepath = parts[1].strip()
                    info_parts = parts[0].split(",", 1)

                    if len(info_parts) >= 2:
                        show_info = info_parts[1].split("//")
                        show_name = show_info[0] if show_info else "Unknown"

                        # Initialize show if not exists
                        if show_name not in shows:
                            shows[show_name] = {
                                "played_episodes": [],
                                "total_available": 0,
                                "current_cycle_start": datetime.now().isoformat(),
                                "times_cycled": 0,
                            }

                        # Add to played list if not already there
                        if filepath not in shows[show_name]["played_episodes"]:
                            shows[show_name]["played_episodes"].append(filepath)

            except Exception as e:
                self.log("Error parsing episode for history: {}".format(str(e)), xbmc.LOGWARNING)
                continue

        self.data["shows"] = shows

    def get_cycle_count(self, show_name):
        """Get the number of times a show has been cycled"""
        if not self.loaded:
            self.load()

        shows = self.data.get("shows", {})
        if show_name not in shows:
            return 0

        return shows[show_name].get("times_cycled", 0)

    def get_stats(self):
        """Get statistics about the episode history"""
        if not self.loaded:
            self.load()

        shows = self.data.get("shows", {})
        total_shows = len(shows)
        total_played = sum(len(show.get("played_episodes", [])) for show in shows.values())

        return {
            "total_shows": total_shows,
            "total_played": total_played,
            "shows": shows,
        }

    def clear(self):
        """Clear all episode history for this channel"""
        self.data = {
            "channel": self.channel_number,
            "channel_name": self.data.get("channel_name", ""),
            "last_updated": datetime.now().isoformat(),
            "shows": {},
        }
        self.log("Cleared all episode history", xbmc.LOGNOTICE)

    @staticmethod
    def reset_all_channels():
        """Reset episode history for all channels (class method)"""
        history_dir = os.path.join(CHANNELS_LOC, "history")

        if not os.path.exists(history_dir):
            log("EpisodeHistory: No history directory found")
            return 0

        count = 0
        try:
            for filename in os.listdir(history_dir):
                if filename.startswith("channel_") and filename.endswith("_history.json"):
                    filepath = os.path.join(history_dir, filename)
                    os.remove(filepath)
                    count += 1
                    log("EpisodeHistory: Deleted {}".format(filename))
        except Exception as e:
            log("EpisodeHistory: Error resetting all channels: {}".format(str(e)), xbmc.LOGERROR)

        log("EpisodeHistory: Reset {} channel histories".format(count), xbmc.LOGNOTICE)
        return count
