#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (C) 2025 Aryez
#
# This file is part of Paragon TV.

"""
Episode History Dashboard

Provides a visual dashboard for viewing and managing episode history across all channels.
Shows summary statistics and allows granular reset options.
"""

import os
import json
from datetime import datetime

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs


class HistoryDashboard:
    """Episode History Dashboard UI"""

    def __init__(self):
        self.addon = xbmcaddon.Addon(id="script.paragontv")

        # Get CHANNELS_LOC from addon settings (avoid circular import)
        settings_folder = self.addon.getAddonInfo("profile")
        channels_loc = xbmc.translatePath(os.path.join(settings_folder, "cache"))
        self.history_dir = xbmc.translatePath(os.path.join(channels_loc, "history"))

    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log("PTV-HistoryDashboard: {}".format(msg), level)

    def get_all_channel_histories(self):
        """Scan history directory and load all channel histories"""
        histories = []

        if not os.path.exists(self.history_dir):
            self.log("History directory doesn't exist: {}".format(self.history_dir))
            return histories

        try:
            files = os.listdir(self.history_dir)
            for filename in files:
                if filename.startswith("channel_") and filename.endswith("_history.json"):
                    # Extract channel number from filename
                    try:
                        channel_num = int(filename.replace("channel_", "").replace("_history.json", ""))
                        filepath = os.path.join(self.history_dir, filename)

                        with open(filepath, "r") as f:
                            data = json.load(f)

                        # Calculate statistics
                        shows = data.get("shows", {})
                        total_episodes = sum(len(show.get("played_episodes", [])) for show in shows.values())
                        cycled_shows = [name for name, show in shows.items() if show.get("times_cycled", 0) > 0]

                        histories.append({
                            "channel": channel_num,
                            "channel_name": data.get("channel_name", "Channel {}".format(channel_num)),
                            "shows_tracked": len(shows),
                            "episodes_played": total_episodes,
                            "last_updated": data.get("last_updated", "Never"),
                            "cycled_shows": cycled_shows,
                            "data": data
                        })
                    except (ValueError, json.JSONDecodeError) as e:
                        self.log("Error loading {}: {}".format(filename, str(e)), xbmc.LOGERROR)

            # Sort by channel number
            histories.sort(key=lambda x: x["channel"])

        except Exception as e:
            self.log("Error scanning history directory: {}".format(str(e)), xbmc.LOGERROR)

        return histories

    def format_datetime(self, iso_string):
        """Format ISO datetime string to readable format"""
        if not iso_string or iso_string == "Never":
            return "Never"
        try:
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return iso_string

    def show_main_dashboard(self):
        """Show main dashboard with all channels"""
        histories = self.get_all_channel_histories()

        if not histories:
            xbmcgui.Dialog().ok(
                "Episode History Dashboard",
                "No episode history found.",
                "Channel history will be created when you rebuild channels",
                "with Episode History Tracking enabled."
            )
            return

        # Build list of channels for selection
        items = []
        for hist in histories:
            # Format the display line
            label = "Ch{} - {} shows - {} episodes played".format(
                hist["channel"],
                hist["shows_tracked"],
                hist["episodes_played"]
            )

            # Add cycle info if any shows have cycled
            if hist["cycled_shows"]:
                label += " - {} cycled".format(len(hist["cycled_shows"]))

            items.append(label)

        # Add action buttons at the end
        items.append("[COLOR yellow]Reset ALL Channels[/COLOR]")
        items.append("[COLOR cyan]Refresh Dashboard[/COLOR]")

        # Show selection dialog
        selected = xbmcgui.Dialog().select(
            "Episode History Dashboard - {} Channels".format(len(histories)),
            items
        )

        if selected == -1:
            return  # User cancelled

        # Handle selection
        if selected == len(histories):
            # Reset ALL channels
            self.reset_all_channels(histories)
        elif selected == len(histories) + 1:
            # Refresh - recursive call
            self.show_main_dashboard()
        else:
            # Show detail view for selected channel
            self.show_channel_detail(histories[selected])

    def show_channel_detail(self, channel_hist):
        """Show detailed view for a specific channel"""
        shows = channel_hist["data"].get("shows", {})

        if not shows:
            xbmcgui.Dialog().ok(
                "Channel {} Detail".format(channel_hist["channel"]),
                "No shows tracked for this channel yet."
            )
            return

        # Build list of shows
        items = []
        show_names = sorted(shows.keys())

        for show_name in show_names:
            show_data = shows[show_name]
            played = len(show_data.get("played_episodes", []))
            cycles = show_data.get("times_cycled", 0)

            label = "{} - {} played".format(show_name, played)
            if cycles > 0:
                label += " - Cycle {}".format(cycles)

            items.append(label)

        # Add action buttons
        items.append("")
        items.append("[COLOR yellow]Reset This Channel[/COLOR]")
        items.append("[COLOR cyan]Back to Dashboard[/COLOR]")

        # Show selection dialog
        selected = xbmcgui.Dialog().select(
            "Channel {} - {} Shows Tracked".format(
                channel_hist["channel"],
                len(shows)
            ),
            items
        )

        if selected == -1 or selected == len(items) - 1:
            # Back to dashboard
            self.show_main_dashboard()
            return

        if selected == len(items) - 2:
            # Reset this channel
            self.reset_single_channel(channel_hist)
            return

        if selected < len(show_names):
            # Show individual show details
            self.show_show_detail(channel_hist, show_names[selected], shows[show_names[selected]])

    def show_show_detail(self, channel_hist, show_name, show_data):
        """Show detailed view for a specific show"""
        played_episodes = show_data.get("played_episodes", [])
        cycles = show_data.get("times_cycled", 0)
        cycle_start = self.format_datetime(show_data.get("current_cycle_start", "Never"))

        # Build info text
        info_lines = [
            "Show: {}".format(show_name),
            "Channel: {}".format(channel_hist["channel"]),
            "",
            "Episodes Played: {}".format(len(played_episodes)),
            "Times Cycled: {}".format(cycles),
            "Current Cycle Started: {}".format(cycle_start),
        ]

        # Show dialog with reset option
        if xbmcgui.Dialog().yesno(
            "Show History Detail",
            "\n".join(info_lines),
            "",
            "",
            "Back",
            "Reset This Show"
        ):
            # User clicked "Reset This Show"
            self.reset_single_show(channel_hist, show_name)
        else:
            # Back to channel detail
            self.show_channel_detail(channel_hist)

    def reset_single_show(self, channel_hist, show_name):
        """Reset history for a single show"""
        confirmed = xbmcgui.Dialog().yesno(
            "Reset Show History",
            "Reset episode history for:",
            "[B]{}[/B]".format(show_name),
            "on Channel {}?".format(channel_hist["channel"]),
            "Cancel",
            "Reset Show"
        )

        if not confirmed:
            self.show_channel_detail(channel_hist)
            return

        try:
            # Load the history JSON, reset the show, and save
            history_file = os.path.join(
                self.history_dir,
                "channel_{}_history.json".format(channel_hist["channel"])
            )

            with open(history_file, "r") as f:
                data = json.load(f)

            # Reset this show's history
            if show_name in data.get("shows", {}):
                data["shows"][show_name] = {
                    "played_episodes": [],
                    "times_cycled": 0,
                    "total_available": 0,
                    "current_cycle_start": datetime.now().isoformat()
                }
                data["last_updated"] = datetime.now().isoformat()

            # Save back to file
            with open(history_file, "w") as f:
                json.dump(data, f, indent=2)

            xbmcgui.Dialog().notification(
                "History Reset",
                "Reset {} on Channel {}".format(show_name, channel_hist["channel"]),
                xbmcgui.NOTIFICATION_INFO,
                3000
            )

            self.log("Reset show {} on channel {}".format(show_name, channel_hist["channel"]), xbmc.LOGNOTICE)

        except Exception as e:
            xbmcgui.Dialog().ok(
                "Error",
                "Failed to reset show history:",
                str(e)
            )
            self.log("Error resetting show: {}".format(str(e)), xbmc.LOGERROR)

        # Return to channel detail (refreshed)
        self.show_main_dashboard()

    def reset_single_channel(self, channel_hist):
        """Reset all history for a single channel"""
        confirmed = xbmcgui.Dialog().yesno(
            "Reset Channel History",
            "Reset ALL episode history for:",
            "[B]Channel {}[/B]".format(channel_hist["channel"]),
            "({} shows, {} episodes played)?".format(
                channel_hist["shows_tracked"],
                channel_hist["episodes_played"]
            ),
            "Cancel",
            "Reset Channel"
        )

        if not confirmed:
            self.show_channel_detail(channel_hist)
            return

        try:
            # Delete the channel history file
            history_file = os.path.join(
                self.history_dir,
                "channel_{}_history.json".format(channel_hist["channel"])
            )

            if os.path.exists(history_file):
                os.remove(history_file)

            xbmcgui.Dialog().notification(
                "History Reset",
                "Reset Channel {}".format(channel_hist["channel"]),
                xbmcgui.NOTIFICATION_INFO,
                3000
            )

            self.log("Reset channel {}".format(channel_hist["channel"]), xbmc.LOGNOTICE)

        except Exception as e:
            xbmcgui.Dialog().ok(
                "Error",
                "Failed to reset channel history:",
                str(e)
            )
            self.log("Error resetting channel: {}".format(str(e)), xbmc.LOGERROR)

        # Return to main dashboard
        self.show_main_dashboard()

    def reset_all_channels(self, histories):
        """Reset all channel histories"""
        total_shows = sum(h["shows_tracked"] for h in histories)
        total_episodes = sum(h["episodes_played"] for h in histories)

        confirmed = xbmcgui.Dialog().yesno(
            "Reset All Channel Histories",
            "Reset episode history for ALL {} channels?".format(len(histories)),
            "",
            "Total: {} shows, {} episodes tracked".format(total_shows, total_episodes),
            "Cancel",
            "Reset All"
        )

        if not confirmed:
            self.show_main_dashboard()
            return

        try:
            # Delete all history files
            count = 0
            if os.path.exists(self.history_dir):
                files = os.listdir(self.history_dir)
                for filename in files:
                    if filename.startswith("channel_") and filename.endswith("_history.json"):
                        filepath = os.path.join(self.history_dir, filename)
                        os.remove(filepath)
                        count += 1

            xbmcgui.Dialog().ok(
                "All Histories Reset",
                "Successfully reset {} channel histories.".format(count),
                "All shows will start fresh on next rebuild."
            )

            self.log("Reset all {} channel histories".format(count), xbmc.LOGNOTICE)

        except Exception as e:
            xbmcgui.Dialog().ok(
                "Error",
                "Failed to reset all histories:",
                str(e)
            )
            self.log("Error resetting all: {}".format(str(e)), xbmc.LOGERROR)

        # Return to main dashboard (will show empty now)
        self.show_main_dashboard()


def main():
    """Entry point for the dashboard"""
    dashboard = HistoryDashboard()
    dashboard.show_main_dashboard()


if __name__ == "__main__":
    main()
