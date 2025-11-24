#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

"""
Reset Episode History Script
Removes all episode history files, forcing fresh episode selection on next rebuild.
"""

import sys
import xbmc
import xbmcaddon
import xbmcgui

# Add parent directory to path to import modules
addon_path = xbmcaddon.Addon("script.paragontv").getAddonInfo("path")
sys.path.insert(0, addon_path + "/resources/lib")

from EpisodeHistory import EpisodeHistory
from Globals import log


def notify(message, title="Paragon TV"):
    """Display a notification to the user"""
    xbmcgui.Dialog().notification(title, message, xbmcgui.NOTIFICATION_INFO, 3000)


def main():
    """Main function to reset all episode histories"""
    log("ptv_reset_history: Starting episode history reset", xbmc.LOGNOTICE)

    # Ask for confirmation
    dialog = xbmcgui.Dialog()
    confirmed = dialog.yesno(
        "Reset Episode History",
        "This will reset episode tracking for ALL channels.[CR][CR]"
        "All shows will start fresh on next channel rebuild.[CR][CR]"
        "Continue?",
    )

    if not confirmed:
        log("ptv_reset_history: User cancelled reset", xbmc.LOGNOTICE)
        notify("Episode history reset cancelled")
        return

    # Perform reset
    try:
        count = EpisodeHistory.reset_all_channels()

        if count > 0:
            log(
                "ptv_reset_history: Successfully reset {} channel histories".format(count),
                xbmc.LOGNOTICE,
            )
            notify(
                "Reset {} channel histories".format(count),
                "Episode History Reset",
            )
            dialog.ok(
                "Episode History Reset Complete",
                "Successfully reset episode history for %d channels.[CR][CR]"
                "Channels will rebuild with fresh episode selection.[CR][CR]"
                "Note: Channels will rebuild on next scheduled rebuild." % count,
            )
        else:
            log("ptv_reset_history: No history files found to reset", xbmc.LOGNOTICE)
            notify("No episode history found", "Reset Complete")
            dialog.ok(
                "No History Found",
                "No episode history files were found.[CR][CR]"
                "Episode tracking may not be enabled,[CR]"
                "or no channels have been built yet.",
            )

    except Exception as e:
        error_msg = "Error resetting episode history: {}".format(str)(e)
        log("ptv_reset_history: " + error_msg, xbmc.LOGERROR)
        notify("Error resetting history", "Error")
        dialog.ok("Error", error_msg)


if __name__ == "__main__":
    main()
