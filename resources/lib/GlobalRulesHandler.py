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

import xbmc
import xbmcaddon
import xbmcgui
from Globals import *
from Rules import *


class GlobalRulesHandler:
    def __init__(self):
        self.log("__init__")
        # Map rule IDs to their channel type compatibility
        self.ruleCompatibility = {
            1: [0, 3, 4, 12],  # RenameRule - All types
            2: [3, 4, 12],  # NoShowRule - Genre channels only
            4: [3, 4],  # OnlyWatchedRule - TV/Movie only
            5: [0, 3, 4, 12],  # DontAddChannel - All types
            6: [0, 3, 4, 12],  # InterleaveChannel - All types
            11: [3, 4],  # OnlyUnWatchedRule - TV/Movie only
            12: [3],  # PlayShowInOrder - TV only
            17: [0, 3, 4, 12],  # LimitMediaDuration - All types
            26: [0, 3, 4, 12],  # PlotFilterRule - All types
        }

        self.ruleNames = {
            1: "Set Channel Name",
            2: "Don't Include Show/Artist",
            4: "Only Play Watched Items",
            5: "Don't Play This Channel",
            6: "Interleave Another Channel",
            11: "Only Play Unwatched Items",
            12: "Play TV Shows In Order",
            17: "Limit Media Duration",
            26: "Plot Keyword Filter",
        }

    def log(self, msg, level=xbmc.LOGDEBUG):
        log("GlobalRulesHandler: " + msg, level)

    def isGlobalRulesEnabled(self):
        """Check if global rules are enabled"""
        return ADDON_SETTINGS.getSetting("GlobalRules_Enabled") == "true"

    def isChannelTypeEnabled(self, channelType):
        """Check if global rules are enabled for a specific channel type"""
        if not self.isGlobalRulesEnabled():
            return False

        typeMap = {
            0: "GlobalRules_CustomPlaylist",
            3: "GlobalRules_TVGenre",
            4: "GlobalRules_MovieGenre",
            12: "GlobalRules_MusicGenre",
        }

        if channelType in typeMap:
            return ADDON_SETTINGS.getSetting(typeMap[channelType]) == "true"

        return False

    def getEnabledGlobalRules(self, channelType):
        """Get list of enabled global rules for a specific channel type"""
        enabledRules = []

        if not self.isChannelTypeEnabled(channelType):
            return enabledRules

        for ruleId, compatibleTypes in self.ruleCompatibility.items():
            # Check if rule is compatible with this channel type
            if channelType in compatibleTypes:
                # Check if rule is enabled globally
                if (
                    ADDON_SETTINGS.getSetting("GlobalRule_" + str(ruleId) + "_Enabled")
                    == "true"
                ):
                    enabledRules.append(ruleId)

        return enabledRules

    def isChannelExcluded(self, channelNumber):
        """Check if a specific channel number is excluded from global rules"""
        excludedChannels = ADDON_SETTINGS.getSetting("GlobalRules_ExcludeChannels")

        if not excludedChannels:
            return False

        try:
            # Parse comma-separated channel numbers
            excludedList = [
                int(ch.strip()) for ch in excludedChannels.split(",") if ch.strip()
            ]
            return channelNumber in excludedList
        except:
            self.log("Error parsing excluded channels list")
            return False

    def applyGlobalRules(self, channel, channelType):
        """Apply all enabled global rules to a channel"""
        if not self.isGlobalRulesEnabled():
            return

        # Check if this specific channel is excluded
        if self.isChannelExcluded(channel.channelNumber):
            self.log(
                "Channel "
                + str(channel.channelNumber)
                + " is excluded from global rules"
            )
            return

        self.log(
            "Applying global rules to channel "
            + str(channel.channelNumber)
            + " (type "
            + str(channelType)
            + ")"
        )

        # Get enabled rules for this channel type
        enabledRules = self.getEnabledGlobalRules(channelType)

        if not enabledRules:
            self.log("No global rules enabled for this channel type")
            return

        # Get all rule instances
        listrules = RulesList()

        # Apply each enabled global rule
        for ruleId in enabledRules:
            self.log("Applying global rule: " + self.ruleNames.get(ruleId, "Unknown"))

            # Find the rule class
            for rule in listrules.ruleList:
                if rule.getId() == ruleId:
                    # Create a copy of the rule
                    newRule = rule.copy()

                    # Load global options for this rule
                    optionCount = newRule.getOptionCount()
                    for i in range(optionCount):
                        optValue = ADDON_SETTINGS.getSetting(
                            "GlobalRule_" + str(ruleId) + "_opt_" + str(i + 1)
                        )
                        if optValue:
                            newRule.optionValues[i] = optValue

                    # Add to channel's rule list
                    channel.ruleList.append(newRule)
                    self.log("Added rule: " + newRule.getTitle())
                    break

    def showGlobalRuleOptions(self, ruleId):
        """Show a dialog to configure options for a specific global rule"""
        listrules = RulesList()
        selectedRule = None

        # Find the rule
        for rule in listrules.ruleList:
            if rule.getId() == ruleId:
                selectedRule = rule.copy()
                break

        if not selectedRule:
            return False

        # Load current global options
        for i in range(selectedRule.getOptionCount()):
            optValue = ADDON_SETTINGS.getSetting(
                "GlobalRule_" + str(ruleId) + "_opt_" + str(i + 1)
            )
            if optValue:
                selectedRule.optionValues[i] = optValue

        # Create dialog
        dlg = xbmcgui.Dialog()

        # Show options based on rule
        modified = False

        for i in range(selectedRule.getOptionCount()):
            label = selectedRule.getOptionLabel(i)
            currentValue = selectedRule.getOptionValue(i)

            # Determine input type based on rule
            if (
                hasattr(selectedRule, "selectBoxOptions")
                and i < len(selectedRule.selectBoxOptions)
                and selectedRule.selectBoxOptions[i]
            ):
                # Select box
                options = selectedRule.selectBoxOptions[i]
                current = 0
                try:
                    current = options.index(currentValue)
                except:
                    pass

                ret = dlg.select(label, options)
                if ret >= 0:
                    ADDON_SETTINGS.setSetting(
                        "GlobalRule_" + str(ruleId) + "_opt_" + str(i + 1), options[ret]
                    )
                    modified = True
            else:
                # Text input
                ret = dlg.input(label, currentValue)
                if ret and ret != currentValue:
                    ADDON_SETTINGS.setSetting(
                        "GlobalRule_" + str(ruleId) + "_opt_" + str(i + 1), ret
                    )
                    modified = True

        return modified

    def clearChannelGlobalRules(self, channel):
        """Remove all global rules from a channel before applying new ones"""
        globalRuleIds = self.ruleCompatibility.keys()

        # Remove rules that match global rule IDs
        channel.ruleList = [
            rule for rule in channel.ruleList if rule.getId() not in globalRuleIds
        ]
