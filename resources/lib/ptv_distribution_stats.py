#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   Copyright (C) 2025 Aryez
#
# This file is part of Paragon TV.

"""
Distribution Statistics Dashboard

Displays smart distribution quality metrics including:
- 5% hard cap compliance
- Episode spacing violations
- Per-show episode counts
- Average spacing statistics
"""

import os
import json
from datetime import datetime

import xbmc
import xbmcgui
import xbmcaddon


class DistributionStatsDashboard:
    """Distribution Statistics Dashboard UI"""

    def __init__(self):
        self.addon = xbmcaddon.Addon(id="script.paragontv")
        settings_folder = self.addon.getAddonInfo("profile")
        cache_loc = xbmc.translatePath(os.path.join(settings_folder, "cache"))
        self.stats_dir = xbmc.translatePath(os.path.join(cache_loc, "distribution_stats"))
        self.ensure_stats_dir()

    def log(self, msg, level=xbmc.LOGDEBUG):
        xbmc.log("PTV-DistributionStats: {}".format(msg), level)

    def ensure_stats_dir(self):
        """Create stats directory if it doesn't exist"""
        if not os.path.exists(self.stats_dir):
            try:
                os.makedirs(self.stats_dir)
                self.log("Created stats directory: {}".format(self.stats_dir))
            except Exception as e:
                self.log("Failed to create stats directory: {}".format(str(e)), xbmc.LOGERROR)

    def get_all_channel_stats(self):
        """Load all channel distribution stats"""
        stats = []

        if not os.path.exists(self.stats_dir):
            return stats

        try:
            files = os.listdir(self.stats_dir)
            for filename in files:
                if filename.startswith("channel_") and filename.endswith("_stats.json"):
                    try:
                        channel_num = int(filename.replace("channel_", "").replace("_stats.json", ""))
                        filepath = os.path.join(self.stats_dir, filename)

                        with open(filepath, "r") as f:
                            data = json.load(f)

                        stats.append({
                            "channel": channel_num,
                            "data": data
                        })
                    except (ValueError, json.JSONDecodeError) as e:
                        self.log("Error loading {}: {}".format(filename, str(e)), xbmc.LOGERROR)

            # Sort by channel number
            stats.sort(key=lambda x: x["channel"])

        except Exception as e:
            self.log("Error scanning stats directory: {}".format(str(e)), xbmc.LOGERROR)

        return stats

    def format_datetime(self, iso_string):
        """Format ISO datetime string to readable format"""
        if not iso_string:
            return "Never"
        try:
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M")
        except Exception as e:
            return iso_string

    def show_main_dashboard(self):
        """Show main dashboard with all channels"""
        all_stats = self.get_all_channel_stats()

        if not all_stats:
            xbmcgui.Dialog().ok(
                "Distribution Statistics",
                "No distribution statistics found.",
                "Statistics are generated when channels are rebuilt",
                "with smart distribution enabled."
            )
            return

        # Build list of channels for selection
        items = []
        for stat in all_stats:
            data = stat["data"]
            channel = stat["channel"]

            # Build summary line
            num_shows = data.get("num_shows", 0)
            cap_violations = data.get("cap_violations", 0)
            spacing_violations = data.get("spacing_violations", 0)
            avg_spacing = data.get("average_spacing", 0)
            timestamp = self.format_datetime(data.get("timestamp", ""))

            label = "Ch{} - {} shows".format(channel, num_shows)

            # Add status indicators
            if num_shows >= 10:
                if cap_violations == 0:
                    label += " [COLOR green][OK][/COLOR]"
                else:
                    label += " [COLOR red][X] {} cap[/COLOR]".format(cap_violations)

            if spacing_violations == 0:
                label += " [COLOR green][OK][/COLOR]"
            else:
                label += " [COLOR yellow][!] {} space[/COLOR]".format(spacing_violations)

            label += " - {}".format(timestamp)

            items.append(label)

        # Add action buttons
        items.append("")
        items.append("[COLOR cyan]Refresh Dashboard[/COLOR]")

        # Show selection dialog
        selected = xbmcgui.Dialog().select(
            "Distribution Statistics - {} Channels".format(len(all_stats)),
            items
        )

        if selected == -1:
            return  # User cancelled

        # Handle selection
        if selected == len(all_stats) + 1:
            # Refresh
            self.show_main_dashboard()
        elif selected < len(all_stats):
            # Show detail view for selected channel
            self.show_channel_detail(all_stats[selected])

    def show_channel_detail(self, channel_stat):
        """Show detailed view for a specific channel"""
        data = channel_stat["data"]
        channel = channel_stat["channel"]

        # Extract statistics
        num_shows = data.get("num_shows", 0)
        cap_violations = data.get("cap_violations", 0)
        spacing_violations = data.get("spacing_violations", 0)
        avg_spacing = data.get("average_spacing", 0)
        hard_cap = data.get("hard_cap", 0)
        minimum_spacing = data.get("minimum_spacing", 3)
        show_counts = data.get("show_counts", {})
        timestamp = self.format_datetime(data.get("timestamp", ""))

        # Build menu items
        items = []

        # Overall statistics section
        items.append("[COLOR yellow]Overall Statistics[/COLOR]")
        items.append("Last Updated: {}".format(timestamp))
        items.append("Shows: {}".format(num_shows))

        # Hard cap status
        if num_shows >= 10:
            if cap_violations == 0:
                items.append("[COLOR green][OK][/COLOR] No show exceeds 5% cap (max {})".format(hard_cap))
            else:
                items.append("[COLOR red][X][/COLOR] {} show(s) exceed 5% cap".format(cap_violations))
        else:
            items.append("[COLOR cyan][-][/COLOR] Hard cap disabled ({} shows)".format(num_shows))

        # Spacing status
        if spacing_violations == 0:
            items.append("[COLOR green][OK][/COLOR] Perfect spacing maintained")
        else:
            if num_shows <= 2:
                items.append("[COLOR yellow][!][/COLOR] {} spacing violations (unavoidable with {} show{})".format(
                    spacing_violations, num_shows, "" if num_shows == 1 else "s"
                ))
            else:
                items.append("[COLOR yellow][!][/COLOR] {} spacing violations".format(spacing_violations))

        # Average spacing
        if avg_spacing > 0:
            items.append("[COLOR cyan][-][/COLOR] Average spacing: {:.1f} episodes".format(avg_spacing))

        items.append("")

        # Per-show breakdown section
        items.append("[COLOR yellow]Per-Show Episode Counts[/COLOR]")

        # Sort shows by episode count (descending)
        sorted_shows = sorted(show_counts.items(), key=lambda x: x[1], reverse=True)

        for show_name, count in sorted_shows:
            # Check if this show violates the cap
            violates_cap = num_shows >= 10 and count > hard_cap

            if violates_cap:
                label = "[COLOR red]{} - {} episodes (EXCEEDS CAP)[/COLOR]".format(show_name, count)
            else:
                label = "{} - {} episodes".format(show_name, count)

            items.append(label)

        items.append("")
        items.append("[COLOR cyan]Back to Dashboard[/COLOR]")

        # Show selection dialog
        selected = xbmcgui.Dialog().select(
            "Channel {} - Distribution Stats".format(channel),
            items
        )

        if selected == -1 or selected == len(items) - 1:
            # Back to dashboard
            self.show_main_dashboard()


def main():
    """Entry point for the dashboard"""
    dashboard = DistributionStatsDashboard()
    dashboard.show_main_dashboard()


if __name__ == "__main__":
    main()
